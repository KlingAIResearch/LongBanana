#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from openclaw_longbanana.config import load_env_file
from openclaw_longbanana.strategies import parse_strategy_names
from openclaw_longbanana.task_paths import resolve_task_paths

from .runner import (
    DEFAULT_RESULTS_DIR,
    FIELDNAMES,
    append_row,
    parse_judge_projects,
    plan_runs,
    run_openclaw_judge,
    write_summary,
)


DEFAULT_STRATEGIES = "pipe"


def load_tasks_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    base_dir = path.resolve().parent
    tasks: list[dict] = []
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


def main(argv: list[str] | None = None) -> None:
    load_env_file()
    parser = argparse.ArgumentParser(description="Run OpenClaw static image judge over JSONL tasks.")
    parser.add_argument("--results-dir", default=str(DEFAULT_RESULTS_DIR))
    parser.add_argument("--strategies", default=DEFAULT_STRATEGIES)
    parser.add_argument("--judge-projects", default="openclaw")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout-s", type=int, default=900)
    parser.add_argument(
        "--invalid-retries",
        type=int,
        default=5,
        help="Retry non-timeout invalid OpenClaw judge outputs this many times.",
    )
    parser.add_argument("--tasks-jsonl", required=True, help="Load judge tasks from a JSONL file.")
    parser.add_argument("--resume", action="store_true", help="Skip existing valid rows and rerun missing or invalid rows.")
    parser.add_argument(
        "--retry-invalid-only",
        action="store_true",
        help="Rerun only existing rows whose latest judgment has is_invalid=True.",
    )
    parser.add_argument(
        "--openclaw-judge-subagents",
        action="store_true",
        help="Enable OpenClaw visual subagent judge mode for OCR, detection/counting, layout, and identity evidence.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    strategies = parse_strategy_names(args.strategies)
    try:
        judge_projects = parse_judge_projects(args.judge_projects)
    except ValueError as exc:
        parser.error(str(exc))
    tasks = load_tasks_jsonl(args.tasks_jsonl)
    if args.limit:
        tasks = tasks[: args.limit]

    runs = plan_runs(tasks, strategies, judge_projects)
    results_dir = Path(args.results_dir)
    judgments_csv = results_dir / "judgments.csv"
    summary_json = results_dir / "summary.json"
    logs_dir = results_dir / "logs"
    runs, resume_stats = _filter_runs_for_resume(
        runs,
        judgments_csv,
        resume=args.resume,
        retry_invalid_only=args.retry_invalid_only,
        mutate=not args.dry_run,
        parser=parser,
    )

    print(
        f"tasks={len(tasks)} strategies={strategies} judge_projects={judge_projects} planned_runs={len(runs)} "
        f"schedule=run-parallel openclaw_judge_subagents={args.openclaw_judge_subagents} "
        f"invalid_retries={args.invalid_retries} "
        f"resume_skipped={resume_stats['skipped']} resume_rerun={resume_stats['rerun']}"
    )
    if args.dry_run:
        for planned in runs[:10]:
            task = planned.task
            print(
                f"  {planned.strategy:16} {planned.judge_project:10} {task.get('harness',''):12} "
                f"{task.get('backend',''):8} {task.get('case_id','')} "
                f"cat={task.get('category','')} refs={len(task.get('refs', []) or [])}"
            )
        return

    results_dir.mkdir(parents=True, exist_ok=True)
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for planned in runs:
            task = planned.task
            log_name = (
                f"{planned.strategy}_{planned.judge_project}_{task.get('harness','')}_"
                f"{task.get('backend','')}_{task.get('case_id','')}_{task.get('data_index','')}.log"
            ).replace("/", "_")
            run_judge = {"openclaw": run_openclaw_judge}[planned.judge_project]
            if planned.judge_project == "openclaw":
                future = executor.submit(
                    run_judge,
                    task,
                    planned.strategy,
                    logs_dir / log_name,
                    args.timeout_s,
                    planned.account_index,
                    args.openclaw_judge_subagents,
                    args.invalid_retries,
                )
            else:
                future = executor.submit(
                    run_judge,
                    task,
                    planned.strategy,
                    logs_dir / log_name,
                    args.timeout_s,
                    planned.account_index,
                )
            futures[future] = planned
        for future in as_completed(futures):
            row = future.result()
            append_row(judgments_csv, row)
            done += 1
            if done % 10 == 0 or done == len(runs):
                print(f"progress {done}/{len(runs)}")

    write_summary(judgments_csv, summary_json)
    print(f"done: {judgments_csv} {summary_json}")


RUN_KEY_FIELDS = (
    "strategy",
    "judge_project",
    "harness",
    "backend",
    "case_id",
    "data_index",
    "category",
    "candidate_path",
)


def _as_bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _planned_run_key(planned) -> tuple[str, ...]:
    task = planned.task
    return (
        str(planned.strategy),
        str(planned.judge_project),
        str(task.get("harness", "")),
        str(task.get("backend", "")),
        str(task.get("case_id", "")),
        str(task.get("data_index", "")),
        str(task.get("category", "")),
        str(task.get("candidate_path", "")),
    )


def _row_key(row: dict) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")) for field in RUN_KEY_FIELDS)


def _load_latest_judgment_rows(judgments_csv: Path) -> tuple[list[dict], dict[tuple[str, ...], dict]]:
    if not judgments_csv.exists() or judgments_csv.stat().st_size == 0:
        return [], {}
    rows = list(csv.DictReader(open(judgments_csv, encoding="utf-8")))
    order = []
    latest = {}
    for row in rows:
        key = _row_key(row)
        if key in latest:
            order.remove(key)
        latest[key] = row
        order.append(key)
    return [latest[key] for key in order], latest


def _rewrite_judgments_csv(judgments_csv: Path, rows: list[dict]) -> None:
    judgments_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(judgments_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _backup_judgments_csv(judgments_csv: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = judgments_csv.with_name(f"{judgments_csv.name}.bak.{timestamp}")
    counter = 1
    while backup_path.exists():
        backup_path = judgments_csv.with_name(f"{judgments_csv.name}.bak.{timestamp}.{counter}")
        counter += 1
    shutil.copy2(judgments_csv, backup_path)
    return backup_path


def _filter_runs_for_resume(
    runs,
    judgments_csv: Path,
    *,
    resume: bool,
    retry_invalid_only: bool,
    mutate: bool,
    parser: argparse.ArgumentParser,
):
    if not resume and not retry_invalid_only:
        return runs, {"skipped": 0, "rerun": 0}
    if retry_invalid_only and not judgments_csv.exists():
        parser.error("--retry-invalid-only requires an existing judgments.csv in --results-dir")

    existing_rows, latest_by_key = _load_latest_judgment_rows(judgments_csv)
    keys_to_rerun = set()
    filtered_runs = []
    skipped = 0

    for planned in runs:
        key = _planned_run_key(planned)
        existing = latest_by_key.get(key)
        existing_invalid = existing is not None and _as_bool(existing.get("is_invalid", ""))
        if retry_invalid_only:
            if existing_invalid:
                filtered_runs.append(planned)
                keys_to_rerun.add(key)
            else:
                skipped += 1
        elif existing is None or existing_invalid:
            filtered_runs.append(planned)
            if existing_invalid:
                keys_to_rerun.add(key)
        else:
            skipped += 1

    if mutate and keys_to_rerun and judgments_csv.exists():
        _backup_judgments_csv(judgments_csv)
        kept_rows = [row for row in existing_rows if _row_key(row) not in keys_to_rerun]
        _rewrite_judgments_csv(judgments_csv, kept_rows)

    return filtered_runs, {"skipped": skipped, "rerun": len(keys_to_rerun)}


if __name__ == "__main__":
    main()
