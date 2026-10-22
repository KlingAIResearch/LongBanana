import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / 'mcp/image_gen').is_dir():
    ROOT = Path(sys.prefix) / 'share/longbanana'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    os.replace(name, path)


def confined(root, value):
    root = Path(root).resolve()
    path = (root / value).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Asset escapes artifact root')
    return path


def expand(value):
    if isinstance(value, dict): return {k: expand(v) for k, v in value.items()}
    if isinstance(value, list): return [expand(v) for v in value]
    if isinstance(value, str):
        def replace(match):
            name = match.group(1)
            if name not in os.environ: raise ValueError('Missing environment variable: ' + name)
            return os.environ[name]
        return re.sub(r'\$\{([A-Z_][A-Z0-9_]*)\}', replace, value)
    return value
