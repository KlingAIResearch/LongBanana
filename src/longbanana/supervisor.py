"""Portable native-agent orchestration. Credentials stay in this process."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import secrets
import threading
from types import SimpleNamespace

from .agents import runner, judge, openclaw
from .agents.openclaw_transport import serve as serve_openclaw
from .datasets import Dataset
from .experiment import Store, scores
from .providers.router import Router
from .providers.http_server import create_server
from .providers.image_service import create_image_server
from .util import ROOT, digest, expand, read, sha, write


def code_contract():
    roots = [Path(__file__).parent, openclaw.PACKAGE,
             ROOT / 'mcp/image_gen/dist', ROOT / 'openclaw_skills', ROOT / 'docs/legacy']
    return {f'{index}/{p.relative_to(root)}': sha(p) for index, root in enumerate(roots)
            for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in {'.py', '.js', '.mjs', '.md'}}


def launch_service(stack, server):
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def close():
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
    stack.callback(close)
    return f'http://127.0.0.1:{server.server_port}'


def prepare(config_path, phase, candidates=None):
    config_path = Path(config_path).resolve(strict=True)
    config = expand(read(config_path))
    def path(value):
        return str((config_path.parent / value).resolve())
    if phase not in {'generate', 'judge'}:
        raise ValueError('Unsupported phase')
    if config.get('agent') not in {'codex', 'claude-code', 'openclaw'}:
        raise ValueError('Unknown agent adapter')
    config['dataset'] = path(config['dataset'])
    for field in ('manifest', 'bwrap'):
        config['runtime'][field] = path(config['runtime'][field])
    if config['agent'] == 'openclaw':
        for field in ('openclaw', 'openclaw_modules'):
            config['runtime'][field] = path(config['runtime'][field])
        config['runtime']['python'] = str((config_path.parent / config['runtime']['python']).absolute())
        for field in ('subagents', 'buffered_gemini'):
            if field in config and type(config[field]) is not bool:
                raise ValueError(field + ' must be a boolean')
        if type(config.get('invalid_retries', 5)) is not int or config.get('invalid_retries', 5) < 0:
            raise ValueError('Invalid retry count')
        if config.get('thinking', 'high') != 'high':
            raise ValueError('The retained OpenClaw profile uses high thinking')
        if config['model'].get('image_jpeg_quality') or config['model'].get('resize_on_413'):
            raise ValueError('Image transport overrides are not implemented for OpenClaw')
        config.setdefault('timeout', 90000 if phase == 'generate' else 900)
        config.setdefault('tool_timeout', 300)
    if phase == 'generate':
        config['runtime']['mcp_modules'] = path(config['runtime']['mcp_modules'])
    if config.get('model', {}).get('headers') or config.get('image', {}).get('headers'):
        raise ValueError('Use headers_env for custom headers; do not embed credential values')
    for endpoint in [config['model']] + ([config['image']] if phase == 'generate' else []):
        allowed = {'protocol', 'base_url', 'model', 'api_key_env', 'credentials_env', 'headers_env',
                   'use_proxy', 'allow_conversion', 'image_jpeg_quality', 'resize_on_413'}
        if set(endpoint) - allowed:
            raise ValueError('Unsupported endpoint configuration field')
        if endpoint.get('protocol') not in openclaw.APIS:
            raise ValueError('Unsupported endpoint protocol')
    if phase == 'generate' and config['image']['protocol'] != 'gemini':
        raise ValueError('The image service requires the Gemini protocol')
    desired = 'responses' if config['agent'] == 'codex' else 'anthropic'
    if config['agent'] != 'openclaw' and config['model']['protocol'] != desired and not config['model'].get('allow_conversion'):
        raise ValueError('Protocol conversion must be explicitly enabled')
    workers = config.get('workers', 1)
    if type(workers) is not int or workers < 1:
        raise ValueError('workers must be a positive integer')
    for name in ('timeout', 'tool_timeout', 'api_timeout', 'model_concurrency', 'image_concurrency'):
        if name in config and (type(config[name]) not in (int, float) or config[name] <= 0):
            raise ValueError(name + ' must be positive')
    for name in ('model_concurrency', 'image_concurrency'):
        if name in config and type(config[name]) is not int:
            raise ValueError(name + ' must be an integer')
    if config.get('proc_mode', 'minimal') not in {'isolated', 'minimal'}:
        raise ValueError('Unsupported proc mode')
    data = Dataset(config['dataset'], evaluation=phase == 'judge')
    if phase == 'judge' and candidates is None:
        raise ValueError('Judge requires a candidate manifest')
    tasks = data.generation_tasks() if phase == 'generate' else data.judge_tasks(candidates)
    runtime_path = Path(config['runtime']['manifest'])
    manifest = read(runtime_path)
    # Runtime manifests may use paths relative to their own directory.
    for entry in manifest.values():
        if isinstance(entry, dict) and 'command' in entry:
            entry['command'] = [str((runtime_path.parent / p).resolve()) for p in entry['command']]
    record = openclaw.runtime_identity(config['runtime']) if config['agent'] == 'openclaw' else manifest[config['agent']]
    runtime_hashes = {str(i): sha(p) for i, p in enumerate(record['command'])}
    runtime_hashes.update(record.get('hashes', {}))
    node = Path(manifest['node']['command'][0])
    runtime_hashes['node'] = sha(node)
    runtime_hashes['bwrap'] = sha(config['runtime']['bwrap'])
    if phase == 'judge' and config.get('strategy', 'pipe') not in judge.JUDGE_STRATEGY_PROMPTS:
        raise ValueError('Unknown Judge strategy')
    if config['agent'] == 'openclaw' and phase == 'generate':
        from openclaw_longbanana.strategies import parse_strategy_names, parse_pipe_generation_mode
        parse_strategy_names(config.get('strategy', 'pipe'))
        parse_pipe_generation_mode(config.get('pipe_mode', 'multi'))
    if phase == 'generate':
        modules = Path(config['runtime']['mcp_modules'])
        for name in ('@modelcontextprotocol/sdk', 'sharp', 'zod'):
            runtime_hashes['mcp/' + name] = sha(modules / name / 'package.json')
    identity_config = copy.deepcopy(config)
    identity_config.pop('workers', None)
    identity_config.pop('dataset', None)
    identity_config.pop('runtime', None)
    if phase == 'judge':
        identity_config.pop('image', None)
    identity = {'phase': phase, 'dataset_fingerprint': data.fingerprint, 'config': identity_config,
                'runtime': {'version': record['version'], 'hashes': runtime_hashes}, 'code': code_contract()}
    if candidates:
        identity['candidates_manifest_sha256'] = sha(candidates)
    return config, data, tasks, record, node, identity


def run(config_path, phase, output, candidates=None, resume=False, dry_run=False,
        case_ids=None, shard_index=0, num_shards=1):
    config, data, all_tasks, record, node, identity = prepare(config_path, phase, candidates)
    if num_shards < 1 or not 0 <= shard_index < num_shards:
        raise ValueError('Invalid shard index/count')
    selected = set(case_ids or data.cases)
    if not selected <= set(data.cases):
        raise ValueError('Unknown selected case')
    tasks = [task for i, task in enumerate(all_tasks) if task['case_id'] in selected and i % num_shards == shard_index]
    if not tasks:
        raise ValueError('No tasks selected')
    plan = {'phase': phase, 'agent': config['agent'], 'release': data.release, 'revision': data.revision,
            'tasks': len(tasks), 'cases': len({t['case_id'] for t in tasks}), 'workers': config.get('workers', 1),
            'experiment_fingerprint': digest(identity), 'dry_run': dry_run}
    if dry_run:
        return plan
    args = SimpleNamespace(agent=config['agent'], model=config['model']['model'], node=node,
        bwrap=config['runtime']['bwrap'], proc_mode=config.get('proc_mode', 'minimal'),
        pass_env=[], timeout=config.get('timeout', 3600), tool_timeout=config.get('tool_timeout', 1800),
        strategy=config.get('strategy', 'pipe'), backend='gemini', mcp_enabled=phase == 'generate',
        mcp_dir=ROOT / 'mcp/image_gen', mcp_modules=Path(config['runtime'].get('mcp_modules', '.')),
        resume=False, expected_version=record['version'])
    if args.agent == 'openclaw':
        args.openclaw_runtime = Path(config['runtime']['openclaw'])
        args.openclaw_modules = Path(config['runtime']['openclaw_modules'])
        args.python = Path(config['runtime']['python'])
        args.subagents = config.get('subagents', False)
        args.invalid_retries = config.get('invalid_retries', 5)
        args.thinking = config.get('thinking', 'high')
        args.pipe_mode = config.get('pipe_mode', 'multi')
    # Always fail closed before starting any API service or task.
    runner.probe(args)
    store = Store(output, identity, resume)
    image_config = store.root / 'image_bridge.json'
    if phase == 'generate':
        write(image_config, {'backends': {'gemini': {'accounts': []}}})
        args.image_config = image_config
    args.planner_token = secrets.token_urlsafe(32)
    args.image_service_token = secrets.token_urlsafe(32)
    with ExitStack() as stack:
        if args.agent == 'openclaw':
            transport = openclaw.ConfiguredTransport(config['model'], config.get('model_concurrency', 30),
                config.get('api_timeout', 300), config.get('buffered_gemini', False))
            port = stack.enter_context(serve_openclaw(transport))
            args.openclaw_provider = transport.sanitized(port)
            if phase == 'judge':
                args.openclaw_templates = {False: openclaw.prepare_template({**config, 'subagents': False}, node)}
                if args.subagents:
                    args.openclaw_templates[True] = openclaw.prepare_template({**config, 'subagents': True}, node)
        else:
            router = Router(config['model'], config.get('model_concurrency', 30), config.get('api_timeout', 300))
            args.planner_base_url = launch_service(stack, create_server(router, args.planner_token))
        if phase == 'generate':
            image_server = create_image_server(config['image'], args.image_service_token,
                config.get('image_concurrency', 10), args.tool_timeout)
            args.image_service_url = launch_service(stack, image_server) + '/generate'

        def execute(task):
            key = [phase, data.release, data.revision, task.get('task_id', task['case_id'])]
            # Identity excludes ephemeral loopback ports/tokens. Resume does not
            # depend on the port chosen by a previous supervisor process.
            fingerprint = digest({'experiment': store.fingerprint, 'task': task,
                                  'images': [sha(p) for p in task['refs'] + ([task['candidate_path']] if phase == 'judge' else [])]})
            with store.lock(key):
                prior = store.completed(key, fingerprint) if resume else None
                if prior:
                    return {**prior, 'skipped_complete': True}
                attempt = store.attempt(key)
                local = copy.copy(args)
                local.output_dir = attempt
                try:
                    if args.agent == 'openclaw':
                        result = openclaw.run_task(local, task, phase)
                    else:
                        result = runner.run_one(local, task, record) if phase == 'generate' else judge.run_judge(local, task, record)
                    return store.save(key, fingerprint, result, attempt)
                except Exception as exc:
                    # Never persist exception strings containing URLs/credentials.
                    result = {'case_id': task['case_id'], 'status': 'invalid', 'is_invalid': True,
                              'score': None, 'error_type': type(exc).__name__}
                    if 'task_id' in task:
                        result['task_id'] = task['task_id']
                    return store.save(key, fingerprint, result, attempt)

        with ThreadPoolExecutor(max_workers=config.get('workers', 1)) as pool:
            futures = [pool.submit(execute, task) for task in tasks]
            for future in as_completed(futures):
                row = future.result()
                print(json.dumps({'case_id': row['case_id'], 'task_id': row.get('task_id'),
                                  'status': row['status'], 'skipped_complete': row.get('skipped_complete', False)}), flush=True)
    # Serialize snapshot updates; different shards may finish concurrently.
    with store.lock('summary', blocking=True):
        records = store.records()
        if phase == 'generate':
            images = []
            for row in records:
                if row['status'] != 'success':
                    continue
                image = Path(row['output_path']).resolve()
                if not image.is_relative_to(store.root) or sha(image) != row['output_sha256']:
                    raise ValueError('Generated output changed or escaped its experiment')
                images.append({'case_id': row['case_id'], 'path': str(image.relative_to(store.root)), 'sha256': row['output_sha256']})
            write(store.root / 'candidates.json', {'schema_version': 1, 'dataset_fingerprint': data.fingerprint,
                  'agent': args.agent, 'backend': 'gemini', 'images': sorted(images, key=lambda r: r['case_id'])})
            summary = {'planned': len(all_tasks), 'valid': len(images), 'complete': len(images) == len(all_tasks)}
        else:
            summary = scores(records, all_tasks, {k: v['category'] for k, v in data.cases.items()})
            summary['dataset_planned_checks'] = len(data.checks)
            summary['complete'] = summary['complete'] and len(all_tasks) == len(data.checks)
            summary['provisional'] = not summary['complete']
        write(store.root / 'summary.json', summary)
    return {**plan, **summary}
