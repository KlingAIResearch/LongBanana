"""Per-task Bubblewrap generation harness for official Codex / Claude Code."""
from __future__ import annotations

import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import shlex
import subprocess
import tempfile
import time
from pathlib import Path

from .bootstrap import remote_only

BACKENDS = {"gemini": "_gemini"}
BACKEND_GUIDES = {
    "gemini": Path(__file__).with_name("gemini_image_for_agents.md"),
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def beneath(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def write_json(path: Path, value) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def load_env(path: Path) -> None:
    for number, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        name, separator, value = line.partition("=")
        name = name.strip()
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid env-file entry at line {number}")
        tokens = shlex.split(value, comments=True)
        if len(tokens) > 1:
            raise ValueError(f"Quote env-file values containing spaces (line {number})")
        os.environ.setdefault(name, tokens[0] if tokens else "")


def load_tasks(path: Path) -> list[dict]:
    tasks, ids = [], set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        case_id = str(row.get("case_id") or row.get("case_uid") or row.get("id") or "")
        prompt = row.get("prompt") or row.get("prompt_en")
        if not case_id or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Each task needs a unique case_id and public prompt/prompt_en")
        if case_id in ids:
            raise ValueError(f"Duplicate case_id: {case_id}")
        ids.add(case_id)
        refs = row.get("refs") or row.get("reference_images") or []
        if not isinstance(refs, list) or not all(isinstance(x, str) for x in refs):
            raise ValueError("refs must be a list of image paths")
        background = row.get("background") or row.get("background_image_path")
        if background:
            refs = [background] + refs
        resolved = []
        for value in refs:
            ref = Path(value)
            ref = (path.resolve().parent / ref).resolve() if not ref.is_absolute() else ref.resolve()
            if not ref.is_file() or ref.suffix.lower() not in IMAGE_SUFFIXES:
                raise ValueError(f"Not an existing reference image: {ref}")
            resolved.append(str(ref))
        # Never carry private_case/checklist/target metadata into the task workspace.
        tasks.append({"case_id": case_id, "prompt": prompt, "refs": resolved})
    return tasks


def environment(extra: list[str]) -> dict[str, str]:
    env = {"HOME": "/home/agent", "CODEX_HOME": "/home/agent/.codex",
           "CLAUDE_CONFIG_DIR": "/home/agent/.claude", "TMPDIR": "/tmp",
           "PATH": "/opt/node/bin:/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8",
           "IMAGE_GEN_CONFIG": "/config/image_gen.json", "IMAGE_GEN_OUTPUT_DIR": "/output", "IMAGE_OUTPUT_DIR": "/output",
           "DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
    names = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
             "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "no_proxy", "NO_PROXY"] + extra
    for name in names:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or name in env:
            raise ValueError(f"Invalid/reserved pass-env: {name}")
        if name in os.environ:
            env[name] = os.environ[name]
    return env


def bubblewrap(bwrap: str, bindings: list[tuple[Path, str, bool]], env: dict, command: list[str], proc_mode="isolated") -> list[str]:
    argv = [bwrap, "--unshare-all", "--share-net", "--die-with-parent", "--new-session",
            "--cap-drop", "ALL", "--uid", "1000", "--gid", "1000", "--clearenv"]
    # Start with an empty filesystem. Never bind the host root, home, or repository.
    for name in ("usr", "bin", "sbin", "lib", "lib64"):
        source = Path("/" + name)
        if source.exists():
            argv += ["--ro-bind", str(source.resolve()), "/" + name]
    if proc_mode == "isolated":
        argv += ["--proc", "/proc"]
    elif proc_mode == "minimal":
        argv += ["--dir", "/proc"]
        for name in ("cpuinfo", "meminfo", "stat", "uptime", "version"):
            source = Path("/proc") / name
            if source.exists():
                argv += ["--ro-bind", str(source), str(source)]
        # Codex resolves its own executable with readlink(/proc/self/exe).
        # A sandbox-local compatibility link exposes no host process tree.
        # It describes the top-level entrypoint, not arbitrary child processes.
        argv += ["--dir", "/proc/self", "--symlink", command[0], "/proc/self/exe"]
    else:
        raise ValueError("Unknown proc mode")
    argv += ["--dev", "/dev", "--tmpfs", "/tmp", "--dir", "/etc"]
    for source in ("/etc/ssl/certs", "/etc/resolv.conf", "/etc/hosts", "/etc/nsswitch.conf"):
        if Path(source).exists():
            argv += ["--ro-bind", str(Path(source).resolve()), source]
    for source, destination, writable in bindings:
        argv += ["--bind" if writable else "--ro-bind", str(source.resolve()), destination]
    for name, value in env.items():
        argv += ["--setenv", name, value]
    return argv + ["--chdir", "/work", "--"] + command


def execute(argv: list[str], cwd: Path, timeout: float, stdin: str = "") -> dict:
    start = time.monotonic()
    timed_out = False
    with (cwd / "stdout.jsonl").open("w") as stdout, (cwd / "stderr.log").open("w") as stderr:
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                env={"PATH": os.defpath}, start_new_session=True, text=True)
        try:
            proc.communicate(stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
        finally:
            # Clean owned CLI/MCP descendants even if the main CLI exits first.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    return {"exit_code": proc.returncode, "timed_out": timed_out,
            "agent_wall_s": round(time.monotonic() - start, 3)}


def token_usage(path: Path) -> dict:
    totals = {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0}
    available = False
    if not path.exists():
        return {"available": False, **totals}
    for line in path.read_text().splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if not isinstance(item, dict) or item.get("type") not in ("turn.completed", "result"):
            continue
        usage = item.get("usage")
        if not isinstance(usage, dict):
            continue
        available = True
        totals["input_tokens"] += int(usage.get("input_tokens", 0))
        totals["output_tokens"] += int(usage.get("output_tokens", 0))
        totals["cached_input_tokens"] += int(usage.get("cached_input_tokens", usage.get("cache_read_input_tokens", 0)))
        if item.get("type") == "result":
            totals["input_tokens"] += int(usage.get("cache_creation_input_tokens", 0)) + int(usage.get("cache_read_input_tokens", 0))
    return {"available": available, **totals}


def runtime(args) -> dict:
    value = json.loads(args.runtime_manifest.read_text())[args.agent]
    if args.expected_version and value["version"] != args.expected_version:
        raise ValueError("Runtime version does not match --expected-version")
    for filename in value["command"]:
        if not Path(filename).is_file():
            raise ValueError(f"Missing runtime file: {filename}")
    return value


def stage_mcp(args, attempt: Path) -> None:
    dist = attempt / "mcp" / "dist"
    dist.mkdir(parents=True)
    (attempt / "mcp" / "node_modules").mkdir()
    for name in (f"server-{args.backend}.js", "_common.js", BACKENDS[args.backend] + ".js"):
        shutil.copyfile(args.mcp_dir / "dist" / name, dist / name)
    if args.backend == "gemini":
        # Native generation has the same single tool in bridge and direct modes.
        # Do not stage the legacy reference-viewing MCP tool: the CLI reads images.
        shutil.copyfile(Path(__file__).with_name("gemini_server.mjs"), dist / "server-gemini.js")
    if args.backend in BACKEND_GUIDES:
        guide_dir = attempt / "docs"
        guide_dir.mkdir()
        shutil.copyfile(BACKEND_GUIDES[args.backend], guide_dir / "image_backend.md")
    write_json(attempt / "mcp" / "package.json", {"type": "module"})


def cli_command(args, record: dict, attempt: Path) -> tuple[list[str], list[tuple[Path, str, bool]]]:
    binary = Path(record["command"][-1])
    entry = getattr(args, "mcp_entry", None) or f"server-{getattr(args, 'backend', 'gemini')}.js"
    mcp_enabled = getattr(args, "mcp_enabled", True)
    bindings = [(binary.parent, "/opt/agent", False)]
    if args.agent == "codex":
        config = ('model = ' + json.dumps(args.model) + '\n'
                  'approval_policy = "never"\nsandbox_mode = "danger-full-access"\n'
                  )
        if mcp_enabled:
            forwarded = ["IMAGE_GEN_CONFIG", "IMAGE_GEN_OUTPUT_DIR", "IMAGE_OUTPUT_DIR", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                         "LONGBANANA_IMAGE_BRIDGE_URL", "LONGBANANA_IMAGE_BRIDGE_TOKEN", "LONGBANANA_NATIVE_VISION", "MCP_TOOL_TIMEOUT",
                         "http_proxy", "https_proxy", "no_proxy", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"]
            config += ('[mcp_servers.image-gen]\ncommand = "/opt/node/bin/node"\n'
                  f'args = ["/opt/mcp/dist/{entry}"]\n'
                  'env_vars = ' + json.dumps(forwarded) + '\n'
                  f'tool_timeout_sec = {args.tool_timeout}\nstartup_timeout_sec = 60\n')
        if getattr(args, "planner_base_url", None):
            config = 'model_provider = "longbanana"\nweb_search = "disabled"\n' + config
            config += ('\n[model_providers.longbanana]\nname = "LongBanana router"\n'
                       'wire_api = "responses"\nenv_key = "OPENAI_API_KEY"\n'
                       'supports_websockets = false\nbase_url = ' +
                       json.dumps(args.planner_base_url.rstrip("/") + "/v1") + '\n')
        (attempt / "home" / ".codex").mkdir()
        (attempt / "home" / ".codex").chmod(0o777)
        (attempt / "home" / ".codex" / "config.toml").write_text(config)
        cmd = [f"/opt/agent/{binary.name}", "exec", "--skip-git-repo-check", "--json",
               "--output-last-message", "/output/final_response.txt", "-"]
    else:
        mcp = {"mcpServers": {"image-gen": {"command": "/opt/node/bin/node",
                "args": [f"/opt/mcp/dist/{entry}"]}} if mcp_enabled else {}}
        write_json(attempt / "work" / "mcp.json", mcp)
        cmd = ["/opt/node/bin/node", f"/opt/agent/{binary.name}", "--print", "--verbose",
               "--output-format", "stream-json", "--model", args.model,
               "--dangerously-skip-permissions", "--strict-mcp-config", "--mcp-config", "/work/mcp.json"]
    return cmd, bindings


def writable_workspace(attempt: Path, names=("home", "work", "output")) -> None:
    # The remote supervisor is root while bwrap deliberately runs as UID 1000.
    # Only fresh task-local writable directories need this permission.
    for name in names:
        (attempt / name).chmod(0o777)


def planner_environment(args, *, judge=False) -> dict:
    env = environment(args.pass_env)
    if getattr(args, "planner_token", None):
        # Only a scoped loopback token is visible to the agent. Never forward
        # upstream credentials inherited by the supervising process.
        for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            env.pop(name, None)
        env["OPENAI_API_KEY" if args.agent == "codex" else "ANTHROPIC_API_KEY"] = args.planner_token
        env["NO_PROXY"] = env["no_proxy"] = "localhost,127.0.0.1"
    env.pop("ANTHROPIC_API_KEY" if args.agent == "codex" else "OPENAI_API_KEY", None)
    if judge:
        # Judge has no image-generation API/config/service credentials.
        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "IMAGE_GEN_CONFIG",
                     "LONGBANANA_IMAGE_BRIDGE_URL", "LONGBANANA_IMAGE_BRIDGE_TOKEN"):
            env.pop(name, None)
    if args.agent == "claude-code" and getattr(args, "planner_base_url", None):
        env["ANTHROPIC_BASE_URL"] = args.planner_base_url.rstrip("/")
        for name in ("ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
                     "ANTHROPIC_DEFAULT_OPUS_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL"):
            env[name] = args.model
    return env


def final_response(attempt: Path, agent: str) -> str:
    if agent == "codex":
        path = attempt / "output/final_response.txt"
        return path.read_text() if path.is_file() else ""
    result = ""
    for line in (attempt / "stdout.jsonl").read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("type") == "result" and not row.get("is_error"):
            result = row.get("result", "")
    return result


def run_one(args, task: dict, record: dict) -> dict:
    identity = hashlib.sha256(task["case_id"].encode()).hexdigest()[:16]
    case = args.output_dir / args.agent / args.backend / identity
    case.mkdir(parents=True, exist_ok=True)
    with (case / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        config_digest = hashlib.sha256(args.image_config.read_bytes()).hexdigest()
        ref_digests = [hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in task["refs"]]
        fingerprint = hashlib.sha256(json.dumps([task, ref_digests, record, args.model,
            args.backend, config_digest, args.timeout, args.tool_timeout,
            getattr(args, "proc_mode", "isolated"), "sandbox-generation-v2"], sort_keys=True).encode()).hexdigest()
        if getattr(args, "planner_base_url", None):
            fingerprint = hashlib.sha256((fingerprint + args.planner_base_url).encode()).hexdigest()
        if getattr(args, "image_service_url", None):
            fingerprint = hashlib.sha256((fingerprint + args.image_service_url + "bridge-v1").encode()).hexdigest()
        result_path = case / "result.json"
        if args.resume and result_path.exists():
            prior = json.loads(result_path.read_text())
            if prior.get("status") == "success" and prior.get("fingerprint") == fingerprint:
                if Path(prior["output_path"]).is_file():
                    return {**prior, "skipped_complete": True}
        attempt = Path(tempfile.mkdtemp(prefix="attempt-", dir=case))
        start = time.monotonic()
        for directory in ("home", "work", "refs", "output", "config"):
            (attempt / directory).mkdir()
        writable_workspace(attempt)
        refs = []
        for index, filename in enumerate(task["refs"], 1):
            dest = attempt / "refs" / f"R{index:02d}__{Path(filename).name}"
            shutil.copyfile(filename, dest)
            refs.append(f"Original name {json.dumps(Path(filename).name)} -> /refs/{dest.name}")
        cfg = json.loads(args.image_config.read_text())
        bridge_url = getattr(args, "image_service_url", None)
        if args.backend != "gemini":
            raise ValueError("Only the Gemini image backend is supported")
        cfg = {"backends": {args.backend: cfg["backends"][args.backend]}}
        if bridge_url:
            cfg = {"backends": {"gemini": {"accounts": []}}}
        for account in cfg.get("backends", {}).get("gemini", {}).get("accounts", []):
            if account.get("credentials"):
                raise ValueError("Use Gemini API-key accounts; Vertex file credentials need a separate adapter")
        write_json(attempt / "config" / "image_gen.json", cfg)
        # This legacy direct config can contain backend API keys. Make it readable
        # by the sandbox UID; never mount service-account files. Prefer the bridge.
        (attempt / "config" / "image_gen.json").chmod(0o644)
        stage_mcp(args, attempt)
        if bridge_url and args.backend == "gemini":
            shutil.copyfile(Path(__file__).with_name("gemini_bridge.mjs"), attempt / "mcp/dist/_gemini.js")
        command, bindings = cli_command(args, record, attempt)
        bindings += [(attempt / "home", "/home/agent", True), (attempt / "work", "/work", True),
                     (attempt / "refs", "/refs", False), (attempt / "output", "/output", True),
                     (attempt / "config", "/config", False), (attempt / "mcp", "/opt/mcp", False),
                     ((getattr(args, "mcp_modules", None) or args.mcp_dir / "node_modules").resolve(), "/opt/mcp/node_modules", False),
                     (args.node.resolve().parent.parent, "/opt/node", False)]
        if (attempt / "docs").is_dir():
            bindings.append((attempt / "docs", "/docs", False))
        env = planner_environment(args)
        if args.backend == "gemini":
            env["LONGBANANA_NATIVE_VISION"] = "1"
        if bridge_url:
            env["LONGBANANA_IMAGE_BRIDGE_URL"] = bridge_url
            env["LONGBANANA_IMAGE_BRIDGE_TOKEN"] = getattr(args, "image_service_token", None) or os.environ["LONGBANANA_IMAGE_BRIDGE_TOKEN"]
            for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                env.pop(name, None)
        env["MCP_TOOL_TIMEOUT"] = str(args.tool_timeout * 1000)
        guide_prompt = ("\nBackend usage reference (available if you need it): "
                        "/docs/image_backend.md\n") if args.backend in BACKEND_GUIDES else ""
        prompt = (f"Generate the image requested below using the image-gen MCP tools.\n"
                  f"Public task:\n{task['prompt']}\nReference images:\n" + "\n".join(refs) +
                  guide_prompt +
                  "\nSave generated images to /output. Inspect and refine as needed using your native image tools; there is no generation-count limit."
                  " When finished, write the accepted image's absolute path to /output/final_image.txt.\n")
        (attempt / "work" / "prompt.txt").write_text(prompt)
        setup_s = time.monotonic() - start
        status = execute(bubblewrap(args.bwrap, bindings, env, command, getattr(args, "proc_mode", "isolated")), attempt, args.timeout, prompt)
        pointer = attempt / "output" / "final_image.txt"
        image = None
        if pointer.exists():
            chosen = Path(pointer.read_text().strip())
            if chosen.is_absolute() and beneath(chosen, Path("/output")) and ".." not in chosen.parts:
                candidate = (attempt / "output" / chosen.relative_to("/output")).resolve()
                if beneath(candidate, (attempt / "output").resolve()) and candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES:
                    image = candidate
        result = {"case_id": task["case_id"], "agent": args.agent, "backend": args.backend,
                  "model": args.model, "cli_version": record["version"], "fingerprint": fingerprint,
                  "attempt_dir": str(attempt), "setup_s": round(setup_s, 3), **status,
                  "status": "success" if image and status["exit_code"] == 0 else "invalid",
                  "output_path": str(image) if image else "",
                  "backend_guide_sha256": hashlib.sha256((attempt / "docs/image_backend.md").read_bytes()).hexdigest()
                      if args.backend in BACKEND_GUIDES else None,
                  "usage": token_usage(attempt / "stdout.jsonl"),
                  "error": ("timeout" if status["timed_out"] else f"cli_exit:{status['exit_code']}"
                            if status["exit_code"] else "" if image else
                            "No explicit valid final image selection; intermediate images are not accepted")}
        write_json(result_path, result)
        return result


def probe(args, smoke: bool = False) -> dict:
    if not shutil.which(args.bwrap):
        raise RuntimeError("Bubblewrap is missing on this worker; supply --bwrap /shared/path/to/bwrap")
    with tempfile.TemporaryDirectory(prefix="longbanana-bwrap-probe-") as temporary:
        root = Path(temporary)
        for directory in ("work", "home", "refs", "output"):
            (root / directory).mkdir()
        (root / "refs" / "public.txt").write_text("public")
        sentinel = root / "host-private.txt"
        sentinel.write_text("must-not-be-visible")
        cmd = ["/bin/sh", "-c", 'test "$(id -u)" = 1000 && test ! -e "$1" && '
               'test ! -e /root && test ! -e "/proc/1/root$1" && test -r /refs/public.txt && '
               '! touch /refs/forbidden && touch /output/ok && touch /home/agent/ok', "probe", str(sentinel)]
        bindings = [(root / "work", "/work", True), (root / "home", "/home/agent", True),
                    (root / "refs", "/refs", False), (root / "output", "/output", True)]
        result = execute(bubblewrap(args.bwrap, bindings, environment([]), cmd, args.proc_mode), root, 20)
        if result["exit_code"] != 0:
            raise RuntimeError("Bubblewrap isolation probe failed: " + (root / "stderr.log").read_text())
        result["isolation_pass"] = True
        result["proc_mode"] = args.proc_mode
        if smoke:
            record = runtime(args)
            binary = Path(record["command"][-1])
            bindings += [(binary.parent, "/opt/agent", False),
                         (args.node.resolve().parent.parent, "/opt/node", False)]
            command = [f"/opt/agent/{binary.name}", "--version"] if args.agent == "codex" else [
                "/opt/node/bin/node", f"/opt/agent/{binary.name}", "--version"]
            cli = execute(bubblewrap(args.bwrap, bindings, environment([]), command, args.proc_mode), root, 30)
            output = (root / "stdout.jsonl").read_text().strip()
            if cli["exit_code"] != 0 or record["version"] not in output.split():
                raise RuntimeError("Sandboxed CLI smoke failed: " + (root / "stderr.log").read_text())
            result["cli_version"] = output
            help_cmd = command[:-1] + (["exec", "--help"] if args.agent == "codex" else ["--help"])
            cli = execute(bubblewrap(args.bwrap, bindings, environment([]), help_cmd, args.proc_mode), root, 30)
            help_text = (root / "stdout.jsonl").read_text()
            flags = ["--json", "--output-last-message", "--skip-git-repo-check"] if args.agent == "codex" else [
                "--strict-mcp-config", "--dangerously-skip-permissions", "--output-format"]
            if cli["exit_code"] or not all(flag in help_text for flag in flags):
                raise RuntimeError("Required CLI adapter options are unavailable")
            result["adapter_flags_pass"] = True
        return result


def main():
    remote_only()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", "smoke", "run"])
    parser.add_argument("--bwrap", default="bwrap")
    parser.add_argument("--proc-mode", choices=["isolated", "minimal"], default="isolated",
                        help="minimal supports outer containers that prohibit new procfs; never exposes host process directories")
    parser.add_argument("--agent", choices=["codex", "claude-code"], default="codex")
    parser.add_argument("--runtime-manifest", type=Path)
    parser.add_argument("--expected-version")
    parser.add_argument("--node", type=Path)
    parser.add_argument("--tasks", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--planner-base-url", help="Optional local model router root URL (without /v1)")
    parser.add_argument("--image-backend", "--backend", dest="backend", choices=BACKENDS, default="gemini",
                        help="User-selected fixed image backend; only its MCP server is staged. --backend is the legacy alias.")
    parser.add_argument("--image-config", type=Path)
    parser.add_argument("--image-service-url", help="Trusted loopback Gemini image endpoint; upstream credentials stay outside the sandbox")
    parser.add_argument("--mcp-dir", type=Path)
    parser.add_argument("--mcp-modules", type=Path)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=3600)
    parser.add_argument("--tool-timeout", type=int, default=1800)
    parser.add_argument("--pass-env", action="append", default=[])
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.mcp_dir is None:
        args.mcp_dir = Path(__file__).resolve().parents[3] / "mcp/image_gen"
    if args.runtime_manifest and args.node is None:
        manifest = json.loads(args.runtime_manifest.read_text())
        if "node" in manifest:
            args.node = Path(manifest["node"]["command"][0])
        elif "claude-code" in manifest:
            args.node = Path(manifest["claude-code"]["command"][0])
    if args.node is None:
        args.node = Path(shutil.which("node") or "/usr/bin/node")
    if args.env_file:
        # Shared secret file is read by the supervisor only; it is never mounted.
        load_env(args.env_file)
    if args.action != "doctor" and (not args.runtime_manifest or not args.node.is_file()):
        parser.error("--runtime-manifest and an existing --node are required")
    if args.workers < 1 or args.timeout <= 0 or args.tool_timeout <= 0:
        parser.error("workers and timeouts must be positive")
    if args.num_shards < 1 or not 0 <= args.shard_index < args.num_shards:
        parser.error("shard-index must be in [0, num-shards)")
    print(json.dumps(probe(args, args.action == "smoke")), flush=True)
    if args.action != "run":
        return
    if not all((args.tasks, args.output_dir, args.model, args.image_config)):
        parser.error("run requires --tasks --output-dir --model --image-config")
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    record = runtime(args)
    tasks = load_tasks(args.tasks)
    tasks = [task for index, task in enumerate(tasks) if index % args.num_shards == args.shard_index]
    # Locking is per case: separate workers/hosts may safely share this output root.
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, args, task, record): task for task in tasks}
        for future in concurrent.futures.as_completed(futures):
            task = futures[future]
            try:
                result = future.result()
            except Exception as error:
                result = {"case_id": task["case_id"], "status": "invalid", "error": str(error)}
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    summary = {"total": len(tasks), "success": sum(r["status"] == "success" for r in results),
               "invalid": sum(r["status"] != "success" for r in results)}
    print(json.dumps(summary), flush=True)
    if summary["invalid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
