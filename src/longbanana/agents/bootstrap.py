"""Download checksum-verified official CLI packages for a Linux execution host."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path


def remote_only() -> None:
    if platform.system() != "Linux":
        raise RuntimeError("Bubblewrap execution requires a Linux host")


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=180) as response:
        return response.read()


def extract(data: bytes, destination: Path) -> None:
    # Permit Node's internal npm symlinks, but never paths escaping the archive.
    with tempfile.TemporaryFile() as stream:
        stream.write(data)
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r:*") as archive:
            for member in archive.getmembers():
                path = Path(member.name)
                if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir() or member.issym()):
                    raise ValueError(f"Unsafe archive member: {member.name}")
                if member.issym():
                    target = Path(os.path.normpath(str(path.parent / member.linkname)))
                    if target.is_absolute() or ".." in target.parts:
                        raise ValueError(f"Unsafe archive link: {member.name}")
                    if any(Path(other.name).parts[:len(path.parts)] == path.parts and other.name != member.name
                           for other in archive.getmembers()):
                        raise ValueError("Archive writes through a symlink")
            archive.extractall(destination)


def main() -> None:
    remote_only()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--claude-version", default="2.0.77")
    parser.add_argument("--codex-version", default="0.158.0")
    parser.add_argument("--node", help="Existing worker Node; otherwise download official Node into the shared bundle")
    args = parser.parse_args()
    if platform.machine() != "x86_64" or platform.system() != "Linux":
        raise RuntimeError("This runtime bundle currently supports Linux x86_64 workers")
    root = args.runtime_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    records = {}
    node = shutil.which(args.node) if args.node else None
    if args.node and not node:
        raise RuntimeError("Specified Node.js executable was not found")
    if not node:
        node_version = "v22.14.0"
        node_name = f"node-{node_version}-linux-x64.tar.gz"
        node_url = f"https://nodejs.org/dist/{node_version}/{node_name}"
        node = str(root / f"node-{node_version}-linux-x64" / "bin" / "node")
        checksums = fetch(f"https://nodejs.org/dist/{node_version}/SHASUMS256.txt").decode()
        expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1] == node_name)
        if not Path(node).exists():
            data = fetch(node_url)
            if hashlib.sha256(data).hexdigest() != expected:
                raise RuntimeError("Official Node checksum mismatch")
            extract(data, root)
        records["node"] = {"version": node_version, "source": node_url, "sha256": expected, "command": [node]}
    # npm's first-party registry is the official Claude Code distribution channel.
    package = "@anthropic-ai/claude-code"
    metadata_url = f"https://registry.npmjs.org/{package}/{args.claude_version}"
    metadata = json.loads(fetch(metadata_url))
    if metadata["name"] != package or metadata["version"] != args.claude_version:
        raise RuntimeError("Official package metadata does not match the requested version")
    tarball_url = metadata["dist"]["tarball"]
    if not tarball_url.startswith("https://registry.npmjs.org/"):
        raise RuntimeError("Unexpected package download origin")
    data = fetch(tarball_url)
    algorithm, expected = metadata["dist"]["integrity"].split("-", 1)
    actual = base64.b64encode(hashlib.new(algorithm, data).digest()).decode()
    if actual != expected:
        raise RuntimeError("Claude Code npm integrity verification failed")
    claude_root = root / f"claude-code-{args.claude_version}"
    if not (claude_root / "package" / "cli.js").exists():
        claude_root.mkdir(exist_ok=True)
        extract(data, claude_root)
    records["claude-code"] = {
        "version": args.claude_version, "source": tarball_url,
        "integrity": metadata["dist"]["integrity"],
        "command": [str(Path(node).resolve()), str(claude_root / "package" / "cli.js")],
    }
    codex_url = (f"https://github.com/openai/codex/releases/download/rust-v{args.codex_version}/"
                 "codex-x86_64-unknown-linux-musl.tar.gz")
    codex_root = root / f"codex-{args.codex_version}"
    binary = codex_root / "codex-x86_64-unknown-linux-musl"
    if not binary.exists():
        data = fetch(codex_url)
        codex_root.mkdir(exist_ok=True)
        extract(data, codex_root)
        digest = hashlib.sha256(data).hexdigest()
        (codex_root / "archive.sha256").write_text(digest + "\n")
    records["codex"] = {
        "version": args.codex_version, "source": codex_url,
        "sha256": (codex_root / "archive.sha256").read_text().strip(),
        "command": [str(binary)],
    }
    # Record verified CLI identities without making any model/API requests.
    for record in records.values():
        result = subprocess.run(record["command"] + ["--version"], capture_output=True,
                                text=True, timeout=30, check=True)
        record["version_output"] = result.stdout.strip()
        if record["version"] not in record["version_output"].split():
            raise RuntimeError("Downloaded CLI reports an unexpected version")
    manifest = root / "runtime.json"
    temporary = root / "runtime.json.tmp"
    temporary.write_text(json.dumps(records, indent=2) + "\n")
    temporary.replace(manifest)
    print(json.dumps({"runtime_manifest": str(manifest), "versions": {
        name: record["version_output"] for name, record in records.items()}}, indent=2))


if __name__ == "__main__":
    main()
