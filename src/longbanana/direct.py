"""Direct Gemini baseline using the retained visual rubric and retry rules."""
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import io
import json
from pathlib import Path

from . import legacy_direct
from .datasets import Dataset
from .experiment import Store, scores
from .providers.router import Endpoint
from .util import digest, expand, read, sha, write


class GeminiClient:
    def __init__(self, endpoint, attempt):
        self.endpoint, self.attempt = endpoint, attempt

    @staticmethod
    def image_part(image):
        stream = io.BytesIO()
        image.save(stream, format='PNG')
        return {'inlineData': {'mimeType': 'image/png', 'data': base64.b64encode(stream.getvalue()).decode()}}

    def generate_text_with_usage(self, contents, config):
        parts = [{'text': value} if isinstance(value, str) else value for value in contents]
        payload = {'contents': [{'role': 'user', 'parts': parts}],
                   'generationConfig': {'maxOutputTokens': config['max_output_tokens']}}
        try:
            body = self.endpoint.open(payload).json()
        except Exception as exc:
            with (self.attempt / 'api_calls.jsonl').open('a') as stream:
                stream.write(json.dumps({'error_type': type(exc).__name__, 'status': getattr(exc, 'status', None)}) + '\n')
            # Retain error type/status, not upstream text that may echo secrets.
            raise RuntimeError(type(exc).__name__ + ':' + str(getattr(exc, 'status', ''))) from None
        with (self.attempt / 'api_calls.jsonl').open('a') as stream:
            stream.write(json.dumps({'response': body}, ensure_ascii=False) + '\n')
        text = '\n'.join(part['text'] for candidate in body.get('candidates', [])
                         for part in candidate.get('content', {}).get('parts', [])
                         if part.get('text') and not part.get('thought'))
        usage = body.get('usageMetadata', {})
        return {'text': text, 'model': body.get('modelVersion', self.endpoint.model),
                'usage': {'input_tokens': usage.get('promptTokenCount', 0),
                          'output_tokens': usage.get('candidatesTokenCount', 0),
                          'total_tokens': usage.get('totalTokenCount', 0),
                          'cached_tokens': usage.get('cachedContentTokenCount', 0),
                          'reasoning_tokens': usage.get('thoughtsTokenCount', 0)}}


def run(config_path, output, candidates, resume=False, dry_run=False, case_ids=None, shard_index=0, num_shards=1):
    config_path = Path(config_path).resolve(strict=True)
    config = expand(read(config_path))
    if set(config) - {'dataset', 'agent', 'workers', 'api_timeout', 'model_concurrency', 'model'}:
        raise ValueError('Unsupported direct baseline setting')
    if config.get('agent') != 'direct-vlm' or config['model'].get('protocol') != 'gemini':
        raise ValueError('The retained direct baseline uses Gemini without an agent')
    if set(config['model']) - {'protocol', 'base_url', 'model', 'api_key_env', 'credentials_env', 'headers_env', 'use_proxy'}:
        raise ValueError('Unsupported direct model setting')
    workers = config.get('workers', 30)
    concurrency = config.get('model_concurrency', workers)
    timeout = config.get('api_timeout', 180)
    if any(type(x) is not int or x < 1 for x in (workers, concurrency)) or type(timeout) not in (int, float) or timeout <= 0:
        raise ValueError('Workers, concurrency and timeout must be positive')
    if num_shards < 1 or not 0 <= shard_index < num_shards:
        raise ValueError('Invalid shard')
    dataset = Dataset(config_path.parent / config['dataset'], evaluation=True)
    all_tasks = dataset.judge_tasks(candidates)
    selected = set(case_ids or dataset.cases)
    if not selected <= set(dataset.cases):
        raise ValueError('Unknown case')
    tasks = [t for i, t in enumerate(all_tasks) if t['case_id'] in selected and i % num_shards == shard_index]
    if not tasks:
        raise ValueError('No tasks selected')
    plan = {'phase': 'judge-direct', 'agent': 'direct-vlm', 'release': dataset.release, 'tasks': len(tasks),
            'workers': workers, 'dry_run': dry_run}
    if dry_run:
        return plan
    from .supervisor import code_contract
    identity_config = copy.deepcopy(config)
    identity_config.pop('workers', None)
    identity_config.pop('dataset')
    identity = {'phase': 'judge-direct', 'dataset_fingerprint': dataset.fingerprint, 'config': identity_config,
                'code': code_contract(), 'candidates_manifest_sha256': sha(candidates)}
    endpoint = Endpoint(config['model'], concurrency, timeout)
    store = Store(output, identity, resume)

    def execute(task):
        key = ['judge-direct', dataset.release, dataset.revision, task['task_id']]
        fingerprint = digest({'experiment': store.fingerprint, 'task': task,
                              'images': [sha(p) for p in [task['candidate_path'], *task['refs']]]})
        with store.lock(key):
            prior = store.completed(key, fingerprint) if resume else None
            if prior:
                return {**prior, 'skipped_complete': True}
            attempt = store.attempt(key)
            result = legacy_direct.judge_one(GeminiClient(endpoint, attempt), task, legacy_direct.Theta())
            invalid = result['is_invalid']
            result.update(case_id=task['case_id'], task_id=task['task_id'], agent='direct-vlm',
                          candidate_path=task['candidate_path'], model=endpoint.model,
                          status='invalid' if invalid else 'success',
                          score=None if invalid else 2 if result['is_pass'] else 1 if result['is_uncertain'] else 0)
            return store.save(key, fingerprint, result, attempt)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for future in as_completed([pool.submit(execute, task) for task in tasks]):
            result = future.result()
            print(json.dumps({'task_id': result['task_id'], 'status': result['status'],
                              'skipped_complete': result.get('skipped_complete', False)}), flush=True)
    with store.lock('summary', blocking=True):
        summary = scores(store.records(), all_tasks, {key: case['category'] for key, case in dataset.cases.items()})
        summary['dataset_planned_checks'] = len(dataset.checks)
        summary['complete'] = summary['complete'] and len(all_tasks) == len(dataset.checks)
        summary['provisional'] = not summary['complete']
        write(store.root / 'summary.json', summary)
    return {**plan, **summary}
