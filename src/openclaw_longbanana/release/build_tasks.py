from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_GENERATION_TASKS = "generation_tasks.jsonl"
DEFAULT_JUDGE_TASKS = "judge_tasks_target.jsonl"
DEFAULT_TASK_MANIFEST = "task_manifest.json"


def _read_manifest(release_root: Path) -> list[dict[str, str]]:
    manifest_path = release_root / "manifest.csv"
    with manifest_path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _image_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)


def _release_case_id(row: dict[str, str]) -> str:
    return row.get("case_id") or Path(row["release_case_dir"]).name


def _rel(path: Path, base_dir: Path) -> str:
    return path.resolve().relative_to(base_dir.resolve()).as_posix()


def _rel_from_openclaw(path: Path, openclaw_dir: Path) -> str:
    return Path("../" + _rel(path, openclaw_dir.parent)).as_posix()


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_generation_tasks(release_root: Path, rows: list[dict[str, str]], openclaw_dir: Path) -> list[dict]:
    tasks = []
    for row in rows:
        sample_dir = release_root / row["release_case_dir"]
        refs = [_rel_from_openclaw(path, openclaw_dir) for path in _image_files(sample_dir / "refs")]
        backgrounds = [_rel_from_openclaw(path, openclaw_dir) for path in _image_files(sample_dir / "background")]
        task = {
            "case_id": _release_case_id(row),
            "prompt_en": row.get("prompt_en", ""),
            "refs": refs,
            "background_image_path": backgrounds[0] if backgrounds else "",
        }
        if len(backgrounds) > 1:
            task["background_image_paths"] = backgrounds
        tasks.append(task)
    return tasks


def _task_file(sample_dir: Path) -> Path:
    preferred = sample_dir / "crowd_nl_tasks.json"
    if preferred.exists():
        return preferred
    fallback = sample_dir / "crowd_check_tasks.json"
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"missing crowd_nl_tasks.json and crowd_check_tasks.json under {sample_dir}")


def _crowd_tasks(path: Path) -> list[dict]:
    value = _load_json(path)
    if isinstance(value, dict):
        tasks = value.get("crowd_tasks", [])
    else:
        tasks = value
    if not isinstance(tasks, list):
        raise ValueError(f"{path}: expected crowd_tasks list")
    return [task for task in tasks if isinstance(task, dict)]


def _refs_for_judge(sample_dir: Path, crowd_task: dict, openclaw_dir: Path) -> list[str]:
    asset_bundle = crowd_task.get("asset_bundle", {}) or {}
    refs = []
    for ref in asset_bundle.get("reference_images", []) or []:
        if not isinstance(ref, dict):
            continue
        ref_path = str(ref.get("ref_image_path") or "")
        if not ref_path:
            continue
        refs.append(_rel_from_openclaw(sample_dir / ref_path, openclaw_dir))
    return refs


def _guide(crowd_task: dict) -> str:
    parts = [
        str(crowd_task.get("instruction_zh") or "").strip(),
        str(crowd_task.get("guide") or "").strip(),
        str(crowd_task.get("option_guide_zh") or "").strip(),
    ]
    return "\n\n".join(part for part in parts if part)


def build_judge_tasks(release_root: Path, rows: list[dict[str, str]], openclaw_dir: Path) -> tuple[list[dict], Counter]:
    tasks = []
    task_sources: Counter = Counter()
    for row in rows:
        sample_dir = release_root / row["release_case_dir"]
        task_path = _task_file(sample_dir)
        task_sources[task_path.name] += 1
        candidate_path = _rel_from_openclaw(release_root / row["target_image"], openclaw_dir)
        for index, crowd_task in enumerate(_crowd_tasks(task_path), start=1):
            task_type = str(crowd_task.get("task_type") or crowd_task.get("category") or "")
            task_id = str(crowd_task.get("task_id") or f"task_{index:03d}")
            tasks.append(
                {
                    "harness": "target_baseline",
                    "backend": "release_target",
                    "case_id": _release_case_id(row),
                    "data_index": f"{_release_case_id(row)}#{index:03d}",
                    "task_id": task_id,
                    "category": task_type,
                    "question": crowd_task.get("question_zh") or crowd_task.get("question") or "",
                    "guide": _guide(crowd_task),
                    "options": crowd_task.get("options", []),
                    "option_desc": crowd_task.get("option_guide_zh") or crowd_task.get("option_desc", {}),
                    "candidate_path": candidate_path,
                    "refs": _refs_for_judge(sample_dir, crowd_task, openclaw_dir),
                }
            )
    return tasks, task_sources


def build_tasks(release_root: str | Path) -> dict:
    release_root = Path(release_root).resolve()
    rows = _read_manifest(release_root)
    openclaw_dir = release_root / "openclaw"
    openclaw_dir.mkdir(parents=True, exist_ok=True)
    generation_tasks = build_generation_tasks(release_root, rows, openclaw_dir)
    judge_tasks, task_sources = build_judge_tasks(release_root, rows, openclaw_dir)
    generation_path = openclaw_dir / DEFAULT_GENERATION_TASKS
    judge_path = openclaw_dir / DEFAULT_JUDGE_TASKS
    generation_count = _write_jsonl(generation_path, generation_tasks)
    judge_count = _write_jsonl(judge_path, judge_tasks)
    manifest = {
        "release_root": release_root.name,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generation_tasks": generation_path.name,
        "generation_task_count": generation_count,
        "judge_tasks": judge_path.name,
        "judge_task_count": judge_count,
        "judge_task_sources": dict(sorted(task_sources.items())),
        "datasets": dict(sorted(Counter(row.get("dataset", "") for row in rows).items())),
        "categories": dict(sorted(Counter(f"{row.get('dataset', '')}/{row.get('category', '')}" for row in rows).items())),
        "path_base": "Paths in JSONL files are relative to this openclaw directory.",
    }
    _write_json(openclaw_dir / DEFAULT_TASK_MANIFEST, manifest)
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build OpenClaw JSONL tasks for a LongBanana bench release.")
    parser.add_argument("--release-root", required=True)
    args = parser.parse_args(argv)
    manifest = build_tasks(args.release_root)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
