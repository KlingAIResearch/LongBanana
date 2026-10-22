"""Scan a source distribution without printing matched sensitive content."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


RULES = {
    'credential': re.compile(r'\b(?:sk-[A-Za-z0-9_-]{24,}|AIza[A-Za-z0-9_-]{30,})'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'service-account': re.compile(r'"type"\s*:\s*"service_account"'),
    'private-host': re.compile(r'https?://[^\s/"\x27]+\.(?:internal|local|corp)(?=[:/\s"\x27]|$)', re.I),
    'private-ip': re.compile(r'https?://(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)(?=[:/\s"\x27]|$)'),
    'job-id': re.compile(r'\b20\d{6}-\d{8}-[a-z0-9]{6}\b'),
    'personal-path': re.compile(r'/(?:home|Users)/(?!agent(?:/|\b)|user(?:/|\b)|USERNAME\b)[A-Za-z0-9_.-]+/'),
    'inline-credential': re.compile(r'(?:api[_-]?key|access[_-]?token|client[_-]?secret)["\x27]?\s*[:=]\s*["\x27][A-Za-z0-9_-]{24,}["\x27]', re.I),
}
BLOCKED_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache'}
BLOCKED_SUFFIXES = {'.pyc', '.pyo', '.pem', '.key', '.p12', '.pfx', '.log', '.map'}


def audit(root: Path, policy=None):
    root = root.resolve(strict=True)
    policy = policy or {}
    patterns = list(RULES.items())
    patterns += [(f'private-policy-{i}', re.compile(re.escape(value), re.I))
                 for i, value in enumerate(policy.get('forbidden_literals', [])) if value]
    patterns += [(f'private-pattern-{i}', re.compile(value, re.I))
                 for i, value in enumerate(policy.get('forbidden_patterns', []))]
    findings, checked = [], 0

    def add(path, rule, line=None):
        row = {'path': str(path.relative_to(root)), 'rule': rule}
        if line is not None:
            row['line'] = line
        findings.append(row)

    # Do not follow symlinks or silently skip ignored/untracked files.
    pending = [root]
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir()):
            relative = str(path.relative_to(root))
            for rule, regex in patterns:
                if regex.search(relative):
                    add(path, rule + '-filename')
            if path.is_symlink():
                add(path, 'symlink')
            elif path.is_dir():
                if path.name in BLOCKED_DIRS:
                    add(path, 'excluded-directory')
                else:
                    pending.append(path)
            elif path.is_file():
                checked += 1
                if (path.suffix.lower() in BLOCKED_SUFFIXES or
                        (path.name == '.env' or path.name.endswith('.env'))):
                    add(path, 'private-or-generated-file')
                try:
                    content = path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    add(path, 'binary-requires-review')
                    continue
                for rule, regex in patterns:
                    for match in regex.finditer(content):
                        add(path, rule, content.count('\n', 0, match.start()) + 1)
    return {'scope': 'source-tree', 'files_checked': checked,
            'passed': not findings, 'findings': findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--policy', type=Path)
    args = parser.parse_args()
    if args.policy and args.policy.resolve().is_relative_to(args.root.resolve()):
        parser.error('Deployment-specific policy must stay outside the release tree')
    policy = json.loads(args.policy.read_text()) if args.policy else None
    result = audit(args.root, policy)
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
