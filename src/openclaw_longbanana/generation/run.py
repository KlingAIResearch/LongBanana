from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from openclaw_longbanana.config import (
    PROJECT_ROOT,
    image_gen_mcp_dir,
    load_env_file,
    load_image_backend_config_path,
    load_openclaw_model_config,
    no_proxy_default,
    node_bin,
    openclaw_bin,
)
from openclaw_longbanana.strategies import build_strategy_prompt, parse_pipe_generation_mode, parse_strategy_names
from openclaw_longbanana.task_paths import resolve_task_paths


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
COMPLETION_MARKER = ".generation_complete.json"
FIELDNAMES = [
    "case_id",
    "strategy",
    "backend",
    "prompt_head",
    "n_refs",
    "output_path",
    "status",
    "error_msg",
    "duration_s",
    "timestamp",
    "file_size_bytes",
]

_csv_lock = threading.Lock()


def _read_jsonl(path: Path) -> list[dict]:
    tasks = []
    base_dir = path.resolve().parent
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            tasks.append(resolve_task_paths(value, base_dir))
    return tasks


def _task_id(task: dict) -> str:
    return str(task.get("case_id") or task.get("case_uid") or task.get("data_id") or task.get("id") or uuid.uuid4().hex)


def _task_prompt(task: dict) -> str:
    return str(task.get("prompt") or task.get("prompt_en") or task.get("target_description") or "")


def _refs(task: dict) -> list[str]:
    refs = task.get("refs") or task.get("reference_images") or []
    return [str(ref) for ref in refs if str(ref)]


def _background(task: dict) -> str:
    return str(task.get("background") or task.get("background_image_path") or "")


def _build_base_prompt(task: dict, output_dir: Path, backend: str, timeout_s: int) -> str:
    files = []
    background = _background(task)
    if background:
        files.append(background)
    files.extend(_refs(task))
    files_block = "\n".join(f"  - {path}" for path in files)
    prompt = _task_prompt(task)
    if not prompt:
        raise ValueError(f"task {_task_id(task)} has no prompt/prompt_en/target_description")

    docs_by_backend = {
        "gemini": PROJECT_ROOT / "docs" / "gemini_image_for_agents.md",
    }
    docs_path = docs_by_backend.get(backend)
    docs_block = (
        "Backend API reference (available if you need it):\n"
        f"  - {docs_path}\n"
    ) if docs_path else ""
    return (
        f"Goal: generate a single image for case .\n\n"
        f"Target description:\n{prompt}\n\n"
        f"Files on disk:\n{files_block}\n\n"
        f"Active image backend: {backend}  (fixed for this run; "
        f"the image-gen tool cannot be re-routed).\n\n"
        f"{docs_block}"
        f"Environment:\n"
        f"- Output directory: {output_dir}\n"
        f"- Filename ending in .png or .jpg.\n"
        f"- Wall-clock budget: {timeout_s}s.\n\n"
        f"Available MCP tools on the `image-gen` server:\n"
        f"  - view_reference_image\n"
        f"  - generate_image\n"
        f"Use `view_reference_image` to inspect the listed files before generating.\n"
        f"The tool writes the image to the output directory above, so you do not need to save files manually.\n"
    )


def build_prompt(task: dict, output_dir: Path, backend: str, strategy: str, timeout_s: int, pipe_mode: str) -> str:
    return build_strategy_prompt(
        base_prompt=_build_base_prompt(task, output_dir, backend, timeout_s),
        strategy_name=strategy,
        harness_name="openclaw",
        pipe_generation_mode=pipe_mode,
    )


def _write_openclaw_config(
    *,
    config_path: Path,
    state_dir: Path,
    output_dir: Path,
    backend: str,
    timeout_s: int,
    image_config: Path,
) -> None:
    model_cfg = load_openclaw_model_config(max_tokens=int(os.environ.get("OPENCLAW_MAX_TOKENS", "8192")))
    mcp_bin = image_gen_mcp_dir() / "dist" / f"server-{backend}.js"
    mcp_env = {
        "IMAGE_GEN_CONFIG": str(image_config),
        "IMAGE_OUTPUT_DIR": "${IMAGE_OUTPUT_DIR}",
        "IMAGE_GENERATE_OUTPUT_DIR": "${IMAGE_OUTPUT_DIR}",
        "LONGBANANA_DATA_ROOT": os.environ.get("LONGBANANA_DATA_ROOT", ""),
    }
    # OpenClaw launches MCP servers with the explicit environment below
    # instead of inheriting every runner variable. Forward backend routing and
    # local-service controls so deployment overrides do not silently fall back
    # to the server entry point's compiled default URL.
    for key in (
        "MCP_GENERATED_PREVIEW_MAX_SIDE",
        "MCP_GENERATED_PREVIEW_JPEG_QUALITY",
        "MCP_VIEW_MAX_SIDE",
        "MCP_VIEW_JPEG_QUALITY",
    ):
        value = os.environ.get(key)
        if value:
            mcp_env[key] = value
    for key in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "NO_PROXY", "no_proxy"):
        value = os.environ.get(key)
        if value:
            mcp_env[key] = value
    mcp_env.setdefault("NO_PROXY", no_proxy_default())
    mcp_env.setdefault("no_proxy", mcp_env["NO_PROXY"])
    config = {
        "agents": {
            "defaults": {
                "model": {
                    "primary": model_cfg.model_ref,
                },
                "thinkingDefault": os.environ.get("OPENCLAW_THINKING", "high"),
                "timeoutSeconds": timeout_s,
                "workspace": "~/.openclaw/workspace",
                "skipBootstrap": True,
            }
        },
        "models": {
            "providers": {
                model_cfg.provider: model_cfg.provider_config(),
            },
        },
        "mcp": {
            "servers": {
                "image-gen": {
                    "command": node_bin(),
                    "args": [str(mcp_bin)],
                    "requestTimeoutMs": int(os.environ.get("MCP_TOOL_TIMEOUT_MS", "300000")),
                    "env": mcp_env,
                },
            },
        },
        "logging": {
            "level": os.environ.get("OPENCLAW_LOG_LEVEL", "info"),
            "file": str(state_dir / "openclaw-runtime.log"),
            "maxFileBytes": 50 * 1024 * 1024,
        },
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def _build_env(root: Path, output_dir: Path, backend: str, timeout_s: int, config_dir: Path) -> dict:
    load_env_file()
    env = {**os.environ}
    for key in ("ALL_PROXY", "all_proxy", "socks_proxy", "SOCKS_PROXY"):
        env.pop(key, None)
    env.setdefault("NO_PROXY", no_proxy_default())
    env.setdefault("no_proxy", env["NO_PROXY"])
    home = root / "home"
    state_dir = root / "state"
    home.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    image_config = load_image_backend_config_path(backend, config_dir)
    config_path = root / "config" / "openclaw.json"
    _write_openclaw_config(
        config_path=config_path,
        state_dir=state_dir,
        output_dir=output_dir,
        backend=backend,
        timeout_s=timeout_s,
        image_config=image_config,
    )
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["OPENCLAW_HOME"] = str(home)
    env["OPENCLAW_STATE_DIR"] = str(state_dir)
    env["OPENCLAW_CONFIG_PATH"] = str(config_path)
    env["IMAGE_OUTPUT_DIR"] = str(output_dir)
    env["IMAGE_GENERATE_OUTPUT_DIR"] = str(output_dir)
    return env


def _run_openclaw(cmd: list[str], cwd: Path, env: dict, timeout_s: int, log_path: Path) -> subprocess.CompletedProcess:
    with open(log_path, "a", encoding="utf-8") as lf:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            timeout=timeout_s,
            stdin=subprocess.DEVNULL,
            stdout=lf,
            stderr=subprocess.STDOUT,
            text=True,
        )


def _images(output_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in output_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ) if output_dir.exists() else []


def _write_completion_marker(output_dir: Path, output_path: Path) -> None:
    marker = output_dir / COMPLETION_MARKER
    temporary = marker.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "status": "success",
                "output_path": str(output_path.resolve()),
                "completed_at": datetime.now().isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(marker)


def _completed_output(output_dir: Path) -> Path | None:
    marker = output_dir / COMPLETION_MARKER
    if not marker.is_file():
        return None
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        output_path = Path(str(payload["output_path"])).resolve()
        output_path.relative_to(output_dir.resolve())
    except (KeyError, OSError, ValueError, json.JSONDecodeError):
        return None
    if output_path.is_file() and output_path.suffix.lower() in IMAGE_SUFFIXES:
        return output_path
    return None


def _backfill_completion_markers(results_csv: Path, results_dir: Path) -> int:
    if not results_csv.is_file():
        return 0
    backfilled = 0
    with results_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") != "success" or not row.get("output_path"):
                continue
            output_path = Path(row["output_path"]).resolve()
            try:
                output_path.relative_to(results_dir.resolve())
            except ValueError:
                continue
            if not output_path.is_file():
                continue
            marker = output_path.parent / COMPLETION_MARKER
            if not marker.exists():
                _write_completion_marker(output_path.parent, output_path)
                backfilled += 1
    return backfilled


def _row(task: dict, strategy: str, backend: str, *, status: str, output_path: str = "", error_msg: str = "", duration_s: float = 0.0, file_size_bytes: int = 0) -> dict:
    return {
        "case_id": _task_id(task),
        "strategy": strategy,
        "backend": backend,
        "prompt_head": _task_prompt(task)[:200].replace("\n", " "),
        "n_refs": len(_refs(task)),
        "output_path": output_path,
        "status": status,
        "error_msg": error_msg,
        "duration_s": round(duration_s, 2),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "file_size_bytes": file_size_bytes,
    }


def run_one(task: dict, strategy: str, backend: str, results_dir: Path, timeout_s: int, pipe_mode: str, config_dir: Path) -> dict:
    output_dir = results_dir / strategy / "openclaw" / backend / _task_id(task)
    output_dir.mkdir(parents=True, exist_ok=True)
    completed = _completed_output(output_dir)
    if completed is not None:
        return _row(task, strategy, backend, status="skipped_exists", output_path=str(completed), file_size_bytes=completed.stat().st_size)

    temp_root = Path(tempfile.mkdtemp(prefix="openclaw-longbanana-gen-"))
    log_path = results_dir / "logs" / f"{strategy}_openclaw_{backend}_{_task_id(task)}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    try:
        env = _build_env(temp_root, output_dir, backend, timeout_s, config_dir)
        prompt = build_prompt(task, output_dir, backend, strategy, timeout_s, pipe_mode)
        cmd = [
            node_bin(),
            str(openclaw_bin()),
            "agent",
            "--local",
            "--agent",
            "main",
            "--thinking",
            os.environ.get("OPENCLAW_THINKING", "high"),
            "--timeout",
            str(timeout_s),
            "--message",
            prompt,
            "--verbose",
            os.environ.get("OPENCLAW_VERBOSE", "full"),
            "--json",
        ]
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write(f"strategy={strategy}\nbackend={backend}\ncase_id={_task_id(task)}\n")
            lf.write(f"openclaw_config={env['OPENCLAW_CONFIG_PATH']}\n")
            lf.write("=" * 60 + "\n")
        proc = _run_openclaw(cmd, openclaw_bin().parent, env, timeout_s, log_path)
        images = _images(output_dir)
        if proc.returncode == 0 and images:
            latest = max(images, key=lambda p: p.stat().st_mtime)
            _write_completion_marker(output_dir, latest)
            return _row(task, strategy, backend, status="success", output_path=str(latest), duration_s=time.time() - start, file_size_bytes=latest.stat().st_size)
        return _row(task, strategy, backend, status="no_output", error_msg=f"openclaw_exit:{proc.returncode}", duration_s=time.time() - start)
    except subprocess.TimeoutExpired:
        return _row(task, strategy, backend, status="timeout", error_msg=f"timeout_after_{timeout_s}s", duration_s=timeout_s)
    except Exception as exc:
        return _row(task, strategy, backend, status="error", error_msg=f"{type(exc).__name__}: {str(exc)[:180]}", duration_s=time.time() - start)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def append_row(path: Path, row: dict) -> None:
    with _csv_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            writer.writerow(row)


def main(argv: list[str] | None = None) -> None:
    load_env_file()
    parser = argparse.ArgumentParser(description="Run OpenClaw LongBanana image generation.")
    parser.add_argument("--tasks-jsonl", required=True)
    parser.add_argument("--results-dir", default="runs/generation")
    parser.add_argument("--backends", default=os.environ.get("BACKENDS", "gemini"))
    parser.add_argument("--strategies", default=os.environ.get("AGENT_STRATEGIES", "pipe"))
    parser.add_argument("--pipe-generation-mode", default=os.environ.get("PIPE_GENERATION_MODE", "multi"))
    parser.add_argument("--workers", type=int, default=int(os.environ.get("CASE_CONCURRENCY", "1")))
    parser.add_argument("--limit", type=int, default=int(os.environ.get("CASE_LIMIT", "0") or "0"))
    parser.add_argument("--timeout-s", type=int, default=int(os.environ.get("TASK_TIMEOUT", "90000")))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    tasks = _read_jsonl(Path(args.tasks_jsonl))
    if args.limit:
        tasks = tasks[: args.limit]
    strategies = parse_strategy_names(args.strategies)
    pipe_mode = parse_pipe_generation_mode(args.pipe_generation_mode)
    backends = tuple(part.strip() for part in args.backends.split(",") if part.strip())
    # MCP processes run with the OpenClaw runtime as cwd. Keep the output path
    # absolute so the MCP writer and this runner inspect the same directory
    # even when callers provide a relative --results-dir.
    results_dir = Path(args.results_dir).resolve()
    plan = [(task, strategy, backend) for task in tasks for strategy in strategies for backend in backends]

    print(
        f"tasks={len(tasks)} strategies={strategies} backends={backends} "
        f"planned_runs={len(plan)} workers={args.workers} dry_run={args.dry_run}"
    )
    if args.dry_run:
        for task, strategy, backend in plan[:20]:
            print(f"  {strategy:16} openclaw {backend:8} {_task_id(task)} refs={len(_refs(task))}")
        return

    config_dir = results_dir / "configs"
    results_csv = results_dir / "results.csv"
    backfilled = _backfill_completion_markers(results_csv, results_dir)
    if backfilled:
        print(f"backfilled_completion_markers={backfilled}")
    if args.workers == 1:
        for task, strategy, backend in plan:
            append_row(results_csv, run_one(task, strategy, backend, results_dir, args.timeout_s, pipe_mode, config_dir))
    else:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = {
                executor.submit(run_one, task, strategy, backend, results_dir, args.timeout_s, pipe_mode, config_dir): (task, strategy, backend)
                for task, strategy, backend in plan
            }
            for future in as_completed(futures):
                append_row(results_csv, future.result())
    print(f"done: {results_csv}")


if __name__ == "__main__":
    main()
