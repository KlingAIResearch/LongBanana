"""Verify the bundled OpenClaw files without executing code or installing packages."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def verify(root):
    root = Path(root).resolve(strict=True)
    runtime = root / 'openclaw-runtime'
    if runtime.is_symlink():
        raise ValueError('Runtime directory must not be a symlink')
    manifest = json.loads((root / 'openclaw-runtime.sha256.json').read_text())
    if manifest.get('schema_version') != 1 or not manifest.get('files'):
        raise ValueError('Invalid runtime manifest')
    expected = manifest['files']
    for name, digest in expected.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name:
            raise ValueError('Unsafe runtime manifest path')
        path = runtime / name
        if any(p.is_symlink() for p in [path, *path.parents] if p != root and p.is_relative_to(root)):
            raise ValueError('Runtime file must not be a symlink: ' + name)
        if not path.is_file():
            raise ValueError('Missing runtime file: ' + name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError('Runtime checksum mismatch: ' + name)
    actual = set()
    pending = [runtime]
    while pending:
        for path in pending.pop().iterdir():
            # Installed dependencies are separately fingerprinted by the harness.
            if path == runtime / 'node_modules':
                continue
            if path.is_symlink():
                raise ValueError('Unexpected runtime symlink')
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                actual.add(path.relative_to(runtime).as_posix())
    if actual != set(expected):
        raise ValueError('Unexpected files in the runtime directory')
    package = json.loads((runtime / 'package.json').read_text())
    if package['version'] != manifest['version']:
        raise ValueError('Runtime version mismatch')
    return {'version': manifest['version'], 'files_verified': len(expected), 'passed': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    print(json.dumps(verify(parser.parse_args().root)))
