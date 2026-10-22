"""Static agentic Judge using native Codex view_image / Claude Code Read."""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

from .bootstrap import remote_only
from .runner import (bubblewrap, cli_command, execute, final_response, load_env,
                    planner_environment, probe, runtime, token_usage,
                    writable_workspace, write_json)

# Reuse the published benchmark's scoring vocabulary and strategies unchanged.

from openclaw_longbanana.judge.answer_parser import parse_agent_answer
from openclaw_longbanana.judge.prompts import build_agent_judge_prompt, JUDGE_STRATEGY_PROMPTS

FIELDS = ("harness", "backend", "case_id", "data_index", "category", "scene",
          "question", "guide", "options", "option_desc")
REFERENCE_POLICY = "agent-selected-references-v1"


def required_native_views(task):
    # Reference selection belongs to the Agent; a completed candidate read is
    # still mandatory. Missing references alone do not invalidate an answer.
    return {task["candidate_path"]}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_judge_tasks(path: Path) -> list[dict]:
    tasks, seen = [], set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        row = {name: raw.get(name, "") for name in FIELDS}
        if not row["case_id"] or not row["question"]:
            raise ValueError("Judge tasks require case_id and question")
        if not isinstance(row["options"], list) or not row["options"] or not all(isinstance(x, str) and x for x in row["options"]):
            raise ValueError("Judge tasks require nonempty string options")
        paths = [raw.get("candidate_path")] + (raw.get("refs") or [])
        resolved = []
        for value in paths:
            if not isinstance(value, str):
                raise ValueError("candidate_path and refs must be image paths")
            image = Path(value)
            image = (path.resolve().parent / image).resolve() if not image.is_absolute() else image.resolve()
            if not image.is_file() or image.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise ValueError("Judge image missing or unsupported")
            resolved.append(str(image))
        row["candidate_path"], row["refs"] = resolved[0], resolved[1:]
        # Include the setting to distinguish the same check across backends.
        identity = [str(row[k]) for k in ("harness", "backend", "case_id", "category", "data_index")]
        if not row["data_index"]:
            identity.append(row["question"])
        row["task_id"] = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]
        if row["task_id"] in seen:
            raise ValueError("Duplicate judge check task")
        seen.add(row["task_id"])
        tasks.append(row)
    return tasks


def native_prompt(task, agent, strategy):
    text = build_agent_judge_prompt(task, strategy)
    tool = "view_image" if agent == "codex" else "Read"
    text = text.replace("Available MCP tools on the `image-gen` server:", "Available native image tool:")
    text = text.replace("view_reference_image", tool).replace("Applies to harness: opencode-agent-judge", f"Applies to harness: {agent}-judge")
    text = text.replace("For non-global checks, inspect every listed reference image before answering.",
                        "For non-global checks, choose the reference images needed for your judgment; you need not inspect every listed reference.")
    return (text + "\nUse the native image tool to visually inspect the supplied files, not shell pixel calculations. "
            "There is no image-generation MCP server in this Judge sandbox. "
            "Do not read any human/model annotation or expected answer.\n")


def read_trace(path):
    # Native image outputs can be large. Do not retain entire trajectories in RAM.
    with path.open() as stream:
        for line in stream:
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    yield row
            except ValueError:
                pass


def native_views(attempt: Path, agent: str) -> set[str]:
    """Require completed native visual tool operations, not an answer claiming it saw images."""
    rows = read_trace(attempt / "stdout.jsonl")
    paths = set()
    if agent == "claude-code":
        calls, successful = {}, set()
        for row in rows:
            blocks = row.get("message", {}).get("content", [])
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use" and block.get("name") == "Read":
                    calls[block["id"]] = block.get("input", {}).get("file_path", "")
                if block.get("type") == "tool_result" and not block.get("is_error"):
                    content = block.get("content", [])
                    if isinstance(content, list) and any(isinstance(x, dict) and x.get("type") == "image" for x in content):
                        successful.add(block.get("tool_use_id"))
        paths = {calls[key] for key in successful if key in calls}
    else:
        for row in rows:
            item = row.get("item", {})
            if row.get("type") == "item.completed" and item.get("type") == "image_view" and item.get("status", "completed") == "completed":
                paths.add(item.get("path", ""))
        # codex exec --json omits some native tool events. The CLI's persisted
        # rollout records include the call and its actual image-bearing output.
        for rollout in (attempt / "home/.codex/sessions").rglob("*.jsonl"):
            calls = {}
            for row in read_trace(rollout):
                item = row.get("payload", {})
                if item.get("type") == "function_call" and item.get("name", "").split(".")[-1] == "view_image":
                    try:
                        calls[item["call_id"]] = json.loads(item["arguments"])["path"]
                    except (ValueError, KeyError, TypeError):
                        continue
                if item.get("type") == "function_call_output" and item.get("call_id") in calls:
                    output = item.get("output", [])
                    if isinstance(output, list) and any(isinstance(x, dict) and x.get("type") == "input_image" for x in output):
                        paths.add(calls[item["call_id"]])
    return paths


def run_judge(args, task, record):
    case = args.output_dir / args.agent / args.strategy / task["task_id"]
    case.mkdir(parents=True, exist_ok=True)
    with (case / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        signature = {"task": task, "images": [digest(p) for p in [task["candidate_path"]] + task["refs"]],
                     "runtime": record, "model": args.model, "strategy": args.strategy,
                     "planner": args.planner_base_url, "proc": args.proc_mode, "timeout": args.timeout,
                     "adapter_version": 2}
        fingerprint = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
        result_path = case / "result.json"
        if args.resume and result_path.exists():
            prior = json.loads(result_path.read_text())
            if prior.get("status") == "success" and prior.get("fingerprint") == fingerprint:
                return {**prior, "skipped_complete": True}
        start = time.monotonic()
        attempt = Path(tempfile.mkdtemp(prefix="attempt-", dir=case))
        for name in ("home", "work", "output", "images"):
            (attempt / name).mkdir()
        writable_workspace(attempt)
        staged = {k: task[k] for k in FIELDS}
        staged["refs"] = []
        for i, source in enumerate([task["candidate_path"]] + task["refs"]):
            name = "candidate" + Path(source).suffix.lower() if i == 0 else f"R{i:02d}__{Path(source).name}"
            shutil.copyfile(source, attempt / "images" / name)
            if i == 0:
                staged["candidate_path"] = "/images/" + name
            else:
                staged["refs"].append("/images/" + name)
        write_json(attempt / "work/task.json", staged)
        prompt = native_prompt(staged, args.agent, args.strategy)
        (attempt / "work/prompt.txt").write_text(prompt)
        command, bindings = cli_command(args, record, attempt)
        bindings += [(attempt / "home", "/home/agent", True), (attempt / "work", "/work", True),
                     (attempt / "output", "/output", True), (attempt / "images", "/images", False),
                     (args.node.resolve().parent.parent, "/opt/node", False)]
        setup_s = time.monotonic() - start
        status = execute(bubblewrap(args.bwrap, bindings, planner_environment(args, judge=True), command, args.proc_mode), attempt, args.timeout, prompt)
        final = final_response(attempt, args.agent)
        (attempt / "output/answer.txt").write_text(final)
        parsed = parse_agent_answer(final, task["options"])
        views = native_views(attempt, args.agent)
        required = required_native_views(staged)
        error = ("timeout" if status["timed_out"] else f"cli_exit:{status['exit_code']}" if status["exit_code"] else
                 parsed.error_msg if parsed.is_invalid else "missing_native_visual_read" if not required <= views else "")
        result = {**{k: task[k] for k in FIELDS}, "candidate_path": task["candidate_path"],
                  "task_id": task["task_id"], "judge_project": args.agent, "strategy": args.strategy,
                  "model": args.model, "cli_version": record["version"], "fingerprint": fingerprint,
                  "status": "invalid" if error else "success", "is_invalid": bool(error),
                  "reference_policy": REFERENCE_POLICY,
                  "answer": parsed.answer, "is_pass": parsed.is_pass, "is_uncertain": parsed.is_uncertain,
                  "score": None if error else 2 if parsed.is_pass else 1 if parsed.is_uncertain else 0,
                  "reason": parsed.reason, "evidence": parsed.evidence, "error_msg": error,
                  "attempt_dir": str(attempt), "native_views": sorted(views), "n_refs_attached": len(task["refs"]),
                  "setup_s": round(setup_s, 3), "duration_s": round(time.monotonic() - start, 3),
                  "timestamp": datetime.now(timezone.utc).isoformat(), **status,
                  "usage": token_usage(attempt / "stdout.jsonl")}
        write_json(result_path, result)
        return result


def main():
    remote_only()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--agent", choices=["codex", "claude-code"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--bwrap", required=True)
    parser.add_argument("--proc-mode", choices=["isolated", "minimal"], default="minimal")
    parser.add_argument("--planner-base-url")
    parser.add_argument("--expected-version")
    parser.add_argument("--strategy", choices=JUDGE_STRATEGY_PROMPTS, default="pipe")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=3600)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--pass-env", action="append", default=[])
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.timeout <= 0 or args.num_shards < 1 or not 0 <= args.shard_index < args.num_shards:
        parser.error("Invalid workers/timeout/shard configuration")
    if args.env_file:
        load_env(args.env_file)
    args.node = Path(json.loads(args.runtime_manifest.read_text())["node"]["command"][0])
    args.mcp_enabled, args.tool_timeout = False, 1800
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    print(json.dumps(probe(args)), flush=True)
    tasks = [t for i, t in enumerate(load_judge_tasks(args.tasks)) if i % args.num_shards == args.shard_index]
    record = runtime(args)
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_judge, args, task, record): task for task in tasks}
        for future in concurrent.futures.as_completed(futures):
            try:
                row = future.result()
            except Exception as exc:
                row = {"task_id": futures[future]["task_id"], "status": "invalid", "is_invalid": True, "error_msg": type(exc).__name__}
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    # One report per shard/agent/strategy avoids cross-host CSV append races.
    stem = f"{args.agent}_{args.strategy}_shard{args.shard_index}"
    write_json(args.output_dir / (stem + ".json"), rows)
    columns = ["task_id", "judge_project", "strategy", "harness", "backend", "case_id", "data_index", "category",
               "answer", "score", "is_pass", "is_uncertain", "is_invalid", "n_refs_attached", "duration_s", "timestamp",
               "candidate_path", "error_msg", "reason"]
    with (args.output_dir / (stem + ".csv")).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    summary = {"total": len(rows), "valid": sum(r["status"] == "success" for r in rows)}
    print(json.dumps(summary), flush=True)
    if summary["valid"] != summary["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
