"""Deployment adapter; the selected upstream Judge function remains unchanged.

--prepare runs in a worker supervisor subprocess, never in an Agent sandbox.
It captures the original provisioning output (including credentials) over a pipe.
Normal mode runs inside Bubblewrap, using only the sanitized provisioning template.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import uuid

MARKER = "__JUDGE_RUNTIME__"
BOOTSTRAP_NAMES = ("AGENTS.md", "SOUL.md", "TOOLS.md", "IDENTITY.md", "USER.md",
                   "HEARTBEAT.md", "BOOTSTRAP.md")


def remap(value, replacements):
    if isinstance(value, dict):
        return {k: remap(v, replacements) for k, v in value.items()}
    if isinstance(value, list):
        return [remap(v, replacements) for v in value]
    if isinstance(value, str):
        for old, new in replacements:
            value = value.replace(str(old), str(new))
    return value


def load_runner(source, root):
    if source == "published":
        sys.path.insert(0, str(root / "src"))
        return importlib.import_module("openclaw_longbanana.judge.runner")
    sys.path.insert(0, str(root / "harness/agent_judge_static"))
    return importlib.import_module("agent_judge_static.runner")


def prepare(source, root, account_index, subagents):
    judge = load_runner(source, root)
    env, runtime_root = judge._build_openclaw_env(account_index, subagents, [])
    try:
        config = json.loads(Path(env["OPENCLAW_CONFIG_PATH"]).read_text())
        replacements = [(runtime_root, MARKER), (judge.OPENCLAW_SKILLS_DIR, "/opt/skills"),
                        (judge.REPO_ROOT, "/work")]
        # Only code-generated workspaces are carried over. No state/media links,
        # host HOME, auto-discovered credentials or session files are copied.
        files = {str(p.relative_to(runtime_root)): p.read_text()
                 for p in (runtime_root / "workspaces").rglob("AGENTS.md")}
        bootstrap = {name: (judge.REPO_ROOT / name).read_text()
                     for name in BOOTSTRAP_NAMES if (judge.REPO_ROOT / name).is_file()}
        deployed_env = {k: remap(v, replacements) for k, v in env.items()
                        if k in {"OPENCLAW_HOME", "OPENCLAW_STATE_DIR", "OPENCLAW_CONFIG_PATH",
                                 "OPENCLAW_GATEWAY_TOKEN", "OPENCLAW_SUBAGENT_GATEWAY_PORT",
                                 "OPENCLAW_GATEWAY_CALL_TIMEOUT_MS", "OPENCLAW_LOG_LEVEL"}}
        providers = config["models"]["providers"]
        if len(providers) != 1:
            raise ValueError("Expected exactly one configured Judge provider")
        print(json.dumps({"config": remap(config, replacements), "env": deployed_env,
                          "workspace_files": files, "bootstrap": bootstrap,
                          "provider": next(iter(providers)), "account_index": account_index,
                          "credentials": env.get("GOOGLE_APPLICATION_CREDENTIALS", "")}))
    finally:
        shutil.rmtree(runtime_root)


def install_provisioner(judge, template):
    """Replace filesystem/transport provisioning only, not prompts or execution."""
    judge.REPO_ROOT = judge.HARNESS_DIR = Path("/work")
    judge.OPENCLAW_DIR = Path("/opt/openclaw")
    judge.OPENCLAW_SKILLS_DIR = Path("/opt/skills")

    def provision(account_index=None, openclaw_judge_subagents=False, media_paths=None):
        if bool(template["config"].get("gateway")) != bool(openclaw_judge_subagents):
            raise ValueError("Provisioning mode differs from the original Judge request")
        runtime_root = Path(tempfile.gettempdir()) / ("agent-judge-static-openclaw-" + uuid.uuid4().hex)
        config = remap(copy.deepcopy(template["config"]), [(MARKER, str(runtime_root))])
        env = {**os.environ, **remap(template["env"], [(MARKER, str(runtime_root))])}
        for name in ("home", "state", "config", "logs"):
            (runtime_root / name).mkdir(parents=True, exist_ok=True)
        # The media allowlist can see exactly this check's staged images.
        for name in ("state/media", "state/workspace", "config/media"):
            (runtime_root / name).symlink_to("/images", target_is_directory=True)
        for name, text in template["workspace_files"].items():
            path = runtime_root / name
            if not path.resolve().is_relative_to(runtime_root):
                raise ValueError("Invalid generated workspace path")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        if "gateway" in config:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            config["gateway"]["port"] = port
            env["OPENCLAW_SUBAGENT_GATEWAY_PORT"] = str(port)
            token = "agent-judge-static-" + uuid.uuid4().hex
            config["gateway"]["auth"]["token"] = token
            env["OPENCLAW_GATEWAY_TOKEN"] = token
        Path(env["OPENCLAW_CONFIG_PATH"]).write_text(json.dumps(config))
        env["HOME"] = env["OPENCLAW_HOME"]
        return env, runtime_root

    judge._build_openclaw_env = provision


def run():
    request = json.loads(Path("/input/request.json").read_text())
    judge = load_runner(request["source"], Path("/opt/judge"))
    install_provisioner(judge, request["template"])
    # Call the original retry loop, prompt builders, subprocess execution,
    # child completion handling and parser with their original arguments.
    row = judge.run_openclaw_judge(
        request["task"], request["strategy"], Path("/output/judge.log"),
        request["timeout_s"], request["account_index"], request["subagents"],
        request["invalid_retries"],
    )
    Path("/output/row.json").write_text(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--count-accounts", action="store_true")
    parser.add_argument("--source", choices=("published", "historical"))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--account-index", type=int, default=0)
    parser.add_argument("--subagents", action="store_true")
    args = parser.parse_args()
    if args.count_accounts:
        judge = load_runner(args.source, args.root)
        count = getattr(judge, "_agent_judge_account_count", judge._gemini_account_count)
        print(count())
    elif args.prepare:
        prepare(args.source, args.root, args.account_index, args.subagents)
    else:
        run()
