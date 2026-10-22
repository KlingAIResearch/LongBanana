from __future__ import annotations

import copy
from pathlib import Path
from urllib.parse import urlparse


PATH_FIELDS = {
    "background",
    "background_image_path",
    "candidate_path",
    "image_path",
    "target_image",
    "target_image_path",
}
PATH_LIST_FIELDS = {
    "background_image_paths",
    "reference_images",
    "refs",
}


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "s3", "gs"}


def resolve_relative_path(value: object, base_dir: Path) -> object:
    if not isinstance(value, str) or not value:
        return value
    path = Path(value).expanduser()
    if path.is_absolute() or _is_url(value):
        return value
    return str((base_dir / path).resolve())


def resolve_task_paths(task: dict, base_dir: str | Path) -> dict:
    base_path = Path(base_dir)
    resolved = copy.deepcopy(task)
    for field in PATH_FIELDS:
        if field in resolved:
            resolved[field] = resolve_relative_path(resolved[field], base_path)
    for field in PATH_LIST_FIELDS:
        values = resolved.get(field)
        if isinstance(values, list):
            resolved[field] = [
                resolve_relative_path(value, base_path) if isinstance(value, str) else value
                for value in values
            ]
    return resolved
