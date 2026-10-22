"""Experiment identity, immutable attempts, hash-checked resume, and scoring."""
from contextlib import contextmanager
import fcntl
from pathlib import Path
import uuid

from .util import digest, read, sha, write


class Store:
    def __init__(self, root, identity, resume=False):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.fingerprint = digest(identity)
        with self.lock('experiment'):
            path = self.root / 'experiment.json'
            if path.exists():
                prior = read(path)
                if prior['fingerprint'] != self.fingerprint:
                    raise ValueError('Experiment identity changed; choose a new output directory')
                if not resume:
                    raise ValueError('Experiment already exists; use --resume')
            else:
                write(path, {'schema_version': 1, 'fingerprint': self.fingerprint, 'identity': identity})

    @contextmanager
    def lock(self, key, blocking=False):
        folder = self.root / 'locks'
        folder.mkdir(exist_ok=True)
        with (folder / (digest(key) + '.lock')).open('a') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            except BlockingIOError:
                raise RuntimeError('Another process owns this experiment task') from None
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def record_path(self, key):
        return self.root / 'results' / (digest(key) + '.json')

    def completed(self, key, task_fingerprint):
        path = self.record_path(key)
        if not path.exists():
            return None
        value = read(path)
        if value.get('task_fingerprint') != task_fingerprint or value.get('status') != 'success':
            return None
        if value.get('output_path'):
            output = Path(value['output_path'])
            if not output.is_file() or sha(output) != value.get('output_sha256'):
                return None
        return value

    def attempt(self, key):
        path = self.root / 'attempts' / digest(key) / uuid.uuid4().hex
        path.mkdir(parents=True)
        return path

    def save(self, key, task_fingerprint, result, attempt):
        value = {**result, 'task_key': key, 'task_fingerprint': task_fingerprint,
                 'experiment_fingerprint': self.fingerprint}
        if value.get('output_path') and value.get('status') == 'success':
            from PIL import Image
            with Image.open(value['output_path']) as image:
                image.verify()
            value['output_sha256'] = sha(value['output_path'])
        write(attempt / 'record.json', value)
        write(self.record_path(key), value)
        return value

    def records(self):
        return [read(p) for p in sorted((self.root / 'results').glob('*.json'))]


def scores(records, expected_tasks, case_categories):
    expected = {t['task_id']: t for t in expected_tasks}
    if len(expected) != len(expected_tasks):
        raise ValueError('Duplicate planned check')
    valid, seen = {}, set()
    for row in records:
        key = row.get('task_id')
        if key not in expected:
            raise ValueError('Result is not part of the planned checklist')
        if key in seen:
            raise ValueError('Duplicate result for a check')
        seen.add(key)
        if row.get('status') == 'success' and not row.get('is_invalid'):
            if type(row.get('score')) is not int or row['score'] not in (0, 1, 2):
                raise ValueError('Valid judgments must have a 0/1/2 score')
            valid[key] = row['score']
    cases, counts = {}, {}
    for key, task in expected.items():
        case = task['case_id']
        counts[case] = counts.get(case, 0) + 1
        if key in valid:
            cases.setdefault(case, []).append(valid[key])
    case_scores = {case: {'score': 50 * sum(values) / len(values), 'valid': len(values),
                         'planned': counts[case], 'complete': len(values) == counts[case]}
                   for case, values in cases.items()}
    categories = {}
    for case, value in case_scores.items():
        categories.setdefault(case_categories[case], []).append(value['score'])
    coverage_complete = len(valid) == len(expected) and bool(expected)
    return {'planned': len(expected), 'valid': len(valid), 'invalid_or_missing': len(expected) - len(valid),
            'complete': coverage_complete, 'provisional': not coverage_complete,
            'overall': sum(v['score'] for v in case_scores.values()) / len(case_scores) if case_scores else None,
            'categories': {k: sum(v) / len(v) for k, v in categories.items()}, 'cases': case_scores}
