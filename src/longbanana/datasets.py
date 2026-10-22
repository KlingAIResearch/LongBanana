"""Validate release artifacts and compile deterministic, task-scoped inputs."""
import json
import re
from pathlib import Path, PurePosixPath

from .util import confined, digest, read, sha


def jsonl(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def asset(root, record):
    name = record['path']
    if not isinstance(name, str) or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
        raise ValueError('Assets must use confined relative paths')
    path = confined(root, name)
    if sha(path) != record['sha256']:
        raise ValueError('Asset checksum mismatch: ' + name)
    return path


class Dataset:
    def __init__(self, manifest, evaluation=False):
        self.path = Path(manifest).resolve(strict=True)
        self.root = self.path.parent
        self.meta = read(self.path)
        if self.meta.get('schema_version') != 1:
            raise ValueError('Unsupported dataset schema')
        self.release = self.meta['release']
        self.revision = self.meta['revision']
        if self.release not in {'open_v1', 'open_v1p5'} or not isinstance(self.revision, str) or not self.revision:
            raise ValueError('Unknown release or empty revision')
        self.fingerprint = digest(self.meta)
        self.cases, self.references, self.backgrounds = {}, {}, {}
        for case in jsonl(asset(self.root, self.meta['public_tasks'])):
            key = case['case_id']
            if (not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', key)
                    or key in self.cases):
                raise ValueError('Missing or duplicate case ID')
            if not isinstance(case.get('prompt'), str) or not case['prompt'].strip():
                raise ValueError('Missing public instruction')
            refs = {}
            for ref in case['references']:
                if not ref.get('id') or ref['id'] in refs:
                    raise ValueError('Missing or duplicate reference ID')
                refs[ref['id']] = asset(self.root, ref)
            if not refs:
                raise ValueError('Empty reference set')
            if case.get('background'):
                self.backgrounds[key] = asset(self.root, case['background'])
            self.cases[key], self.references[key] = case, refs
        if not self.cases:
            raise ValueError('Empty dataset')
        self.checks = []
        if evaluation:
            seen = set()
            for check in jsonl(asset(self.root, self.meta['checks'])):
                key = (check['case_id'], str(check['check_id']))
                if key in seen or key[0] not in self.cases or not key[1]:
                    raise ValueError('Duplicate or orphan check')
                seen.add(key)
                if not isinstance(check.get('question'), str) or not check['question'].strip():
                    raise ValueError('Empty check question')
                options = check.get('options')
                if not isinstance(options, list) or not options or not all(isinstance(x, str) and x for x in options):
                    raise ValueError('Checks require answer options')
                ids = check.get('reference_ids')
                if not isinstance(ids, list) or len(ids) != len(set(ids)):
                    raise ValueError('Checks require unique explicit reference IDs')
                if any(ref not in self.references[key[0]] for ref in ids):
                    raise ValueError('Unknown bound reference')
                if not ids and not check.get('candidate_only_reason'):
                    raise ValueError('Empty bindings need an explicit candidate-only rationale')
                self.checks.append(check)
            if not self.checks:
                raise ValueError('Empty checklist')
        counts = self.meta.get('counts', {})
        actual = {'cases': len(self.cases), 'references': sum(map(len, self.references.values())),
                  'backgrounds': len(self.backgrounds)}
        if evaluation:
            actual['checks'] = len(self.checks)
        for name, count in actual.items():
            if counts.get(name) != count:
                raise ValueError('Dataset count mismatch: ' + name)

    def generation_tasks(self):
        # Only public text and images cross this boundary.
        return [{'case_id': key, 'prompt': case['prompt'],
                 'refs': ([str(self.backgrounds[key])] if key in self.backgrounds else [])
                         + [str(p) for p in self.references[key].values()]}
                for key, case in self.cases.items()]

    def judge_tasks(self, candidates):
        artifact = Path(candidates).resolve(strict=True)
        value = read(artifact)
        if value.get('dataset_fingerprint') != self.fingerprint:
            raise ValueError('Candidate images belong to a different dataset revision')
        images = {}
        for row in value['images']:
            key = row['case_id']
            if key not in self.cases or key in images:
                raise ValueError('Duplicate or unknown candidate case')
            images[key] = asset(artifact.parent, row)
        tasks = []
        for check in self.checks:
            key = check['case_id']
            if key not in images:
                continue
            identity = [self.release, self.revision, self.fingerprint, key, str(check['check_id'])]
            tasks.append({'task_id': digest(identity)[:24], 'case_id': key,
                          'harness': value.get('agent', 'external'), 'backend': value.get('backend', 'gemini'),
                          'data_index': str(check['check_id']), 'category': check.get('category', ''),
                          'scene': check.get('scene', ''), 'question': check['question'],
                          'guide': check.get('guide', ''), 'options': check['options'],
                          'option_desc': check.get('option_desc', {}),
                          'candidate_path': str(images[key]),
                          'refs': [str(self.references[key][ref]) for ref in check['reference_ids']]})
        return tasks


def resolve_bindings(check, graph):
    """Resolve only explicit bindings; never infer from prose or category names."""
    references = [r['reference_id'] for r in graph['references']]
    if len(set(references)) != len(references):
        raise ValueError('Duplicate graph references')
    if 'reference_ids' in check:
        bound = check['reference_ids']
    else:
        members = set(check.get('members', []))
        nodes = {n['id'] for n in graph['nodes']}
        if not members or not members <= nodes:
            raise ValueError('Unresolved checklist graph members')
        targets = set(members)
        # References may explicitly support an edge or constraint rather than
        # its constituent nodes. Those bindings are part of the graph too.
        source = check.get('source', '')
        if source:
            kind, separator, source_id = source.partition(':')
            collection = {'edge': 'edges', 'constraint': 'constraints'}.get(kind)
            if not separator or collection is None or source_id not in {x['id'] for x in graph.get(collection, [])}:
                raise ValueError('Unresolved checklist graph source')
            targets.add(source_id)
        bound = {e['src'] for e in graph['evidence_edges'] if e['dst'] in targets}
    if not set(bound) <= set(references):
        raise ValueError('Graph binding references unknown images')
    result = [ref for ref in references if ref in bound]
    if not result and not check.get('candidate_only_reason'):
        raise ValueError('No explicit image evidence: review this binding before release')
    return result
