"""Per-task OpenClaw sandbox deployment; original execution logic is retained."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import openclaw_longbanana

from . import runner
from .judge import FIELDS
from .openclaw_judge_inner import remap
from .openclaw_transport import Transport
from ..providers.router import Endpoint
from ..util import ROOT, digest, read, sha, write

APIS = {'gemini': 'google-generative-ai', 'responses': 'openai-responses',
        'anthropic': 'anthropic-messages', 'chat': 'openai-completions'}
PACKAGE = Path(openclaw_longbanana.__file__).parent


class ConfiguredTransport(Transport):
    def __init__(self, config, concurrency=30, timeout=300, buffered_gemini=False):
        self.endpoint_config = Endpoint(config, concurrency, timeout)
        model = config['model']
        provider = {'baseUrl': config['base_url'], 'apiKey': '', 'api': APIS[config['protocol']],
                    'auth': 'api-key', 'models': [{'id': model, 'name': model, 'api': APIS[config['protocol']],
                    'reasoning': True, 'input': ['text', 'image'], 'contextWindow': 200000,
                    'maxTokens': 16384, 'cost': {'input': 0, 'output': 0, 'cacheRead': 0, 'cacheWrite': 0}}]}
        super().__init__(provider, timeout=timeout, buffered_gemini=buffered_gemini)
        self.semaphore = self.endpoint_config.semaphore
        self.use_proxy = config.get('use_proxy', True)

    def headers(self):
        return self.endpoint_config.headers()


def runtime_identity(config):
    root = Path(config['openclaw']).resolve(strict=True)
    python = Path(config['python']).absolute()
    # A symlinked venv executable is intentional; preserve the interpreter prefix.
    prefix = python.parent.parent.resolve()
    if prefix in {Path('/'), Path('/root'), Path.home().resolve()} or ROOT.is_relative_to(prefix):
        raise ValueError('Python runtime prefix is too broad to mount safely')
    files = {str(p.relative_to(root)): sha(p) for p in sorted((root / 'dist').rglob('*')) if p.is_file()}
    if not files:
        raise ValueError('OpenClaw dist assets are missing')
    for name in ('openclaw.mjs', 'package.json'):
        files[name] = sha(root / name)
    modules = Path(config['openclaw_modules'])
    locks = [modules / '.package-lock.json', modules / '.pnpm/lock.yaml',
             modules.parent / 'pnpm-lock.yaml', modules.parent / 'package-lock.json']
    locks = [p for p in locks if p.is_file()]
    if not locks:
        raise ValueError('OpenClaw dependencies require their installed lock file')
    dependency_records = {str(index): sha(p) for index, p in enumerate(locks)}
    for name in ('.modules.yaml', '.pnpm-workspace-state-v1.json'):
        if (modules / name).is_file():
            dependency_records[name] = sha(modules / name)
    return {'version': read(root / 'package.json')['version'], 'command': [str(root / 'openclaw.mjs')],
            'hashes': {'assets': digest(files), 'dependencies': digest(dependency_records), 'python': sha(python)}}


def prepare_template(config, node):
    """Provision in an isolated subprocess with a dummy key; make no API call."""
    env = {'PATH': os.defpath, 'PYTHONPATH': str(PACKAGE.parent), 'PYTHONDONTWRITEBYTECODE': '1',
           'PYTHONNOUSERSITE': '1', 'OPENCLAW_LONGBANANA_ENV_FILE': '/nonexistent/longbanana.env',
           'OPENCLAW_SKILLS_DIR': str(ROOT / 'openclaw_skills'), 'OPENCLAW_JUDGE_PROVIDER': 'google',
           'GEMINI_API_KEY': 'local-provisioning-only', 'AGENT_JUDGE_GEMINI_MODEL': config['model']['model'],
           'NODE_BIN': str(node), 'OPENCLAW_BIN': str(Path(config['runtime']['openclaw']) / 'openclaw.mjs')}
    command = [config['runtime']['python'], str(Path(__file__).with_name('openclaw_judge_inner.py')),
               '--prepare', '--source', 'published', '--root', str(ROOT), '--account-index', '0']
    if config.get('subagents', False):
        command.append('--subagents')
    result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError('OpenClaw template provisioning failed')
    template = json.loads(result.stdout)
    if template['credentials']:
        raise ValueError('Unexpected credentials in provisioning template')
    old = template['provider']
    model = config['model']['model']
    template = remap(template, [(old + '/' + model, 'longbanana/' + model)])
    template['provider'] = 'longbanana'
    # Transport replaces the complete provider before this enters a sandbox.
    template['config']['models']['providers'] = {}
    if template['config'].get('gateway'):
        template['config']['gateway'].setdefault('controlUi', {})['enabled'] = False
    return template


def environment(thinking='high'):
    return {'HOME': '/home/agent', 'PATH': '/opt/node/bin:/usr/bin:/bin', 'TMPDIR': '/tmp',
            'LANG': 'C.UTF-8', 'NODE_BIN': '/opt/node/bin/node',
            'OPENCLAW_BIN': '/opt/openclaw/openclaw.mjs', 'OPENCLAW_SKILLS_DIR': '/opt/skills',
            'IMAGE_GEN_MCP_DIR': '/opt/mcp', 'IMAGE_GEN_CONFIG': '/input/image.json',
            'OPENCLAW_LONGBANANA_ENV_FILE': '/input/no-host-env',
            'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1', 'NODE_DISABLE_COMPILE_CACHE': '1',
            'no_proxy': 'localhost,127.0.0.1', 'NO_PROXY': 'localhost,127.0.0.1',
            'OPENCLAW_THINKING': thinking, 'AGENT_JUDGE_THINKING': thinking}


def sandbox_command(args, attempt, phase):
    bindings = [(attempt / 'home', '/home/agent', True), (attempt / 'work', '/work', True),
                (attempt / 'output', '/output', True), (attempt / 'images', '/images', False),
                (attempt / 'input', '/input', False), (attempt / 'code', '/opt/judge', False),
                (ROOT / 'openclaw_skills', '/opt/skills', False),
                (args.node.parent.parent, '/opt/node', False)]
    for name in ('openclaw.mjs', 'package.json', 'dist', 'docs'):
        path = args.openclaw_runtime / name
        if path.exists():
            bindings.append((path, '/opt/openclaw/' + name, False))
    bindings.append((args.openclaw_modules, '/opt/openclaw/node_modules', False))
    prefix = args.python.parent.parent
    bindings.append((prefix, str(prefix), False))
    if phase == 'generate':
        bindings += [(attempt / 'mcp', '/opt/mcp', False), (args.mcp_modules, '/opt/mcp/node_modules', False),
                     (ROOT / 'docs/legacy', '/opt/reference/docs', False)]
    command = [str(args.python), '/input/inner.py']
    argv = runner.bubblewrap(args.bwrap, bindings, environment(args.thinking), command, args.proc_mode)
    if args.proc_mode == 'minimal':
        for i, word in enumerate(argv):
            if word == '--symlink' and argv[i + 2] == '/proc/self/exe':
                argv[i + 1] = '/opt/node/bin/node'
    return argv


def run_task(args, task, phase):
    attempt = args.output_dir
    for name in ('home', 'work', 'output', 'images', 'input'):
        (attempt / name).mkdir()
    runner.writable_workspace(attempt)
    # Only the small public execution package is mounted, never its source repository.
    shutil.copytree(PACKAGE, attempt / 'code/src/openclaw_longbanana',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    if phase == 'judge':
        inner = Path(__file__).with_name('openclaw_judge_inner.py')
        staged = {name: task[name] for name in FIELDS}
        staged['refs'] = []
        for index, source in enumerate([task['candidate_path']] + task['refs']):
            name = 'candidate' + Path(source).suffix if index == 0 else f'R{index:02d}__{Path(source).name}'
            shutil.copyfile(source, attempt / 'images' / name)
            if index == 0:
                staged['candidate_path'] = '/images/' + name
            else:
                staged['refs'].append('/images/' + name)
        effective_subagents = args.subagents and task.get('category') != 'global_check'
        template = copy.deepcopy(args.openclaw_templates[effective_subagents])
        template['config']['models']['providers'] = {'longbanana': args.openclaw_provider}
        for name, text in template['bootstrap'].items():
            (attempt / 'work' / name).write_text(text)
        request = {'source': 'published', 'template': template, 'task': staged, 'strategy': args.strategy,
                   'timeout_s': args.timeout, 'invalid_retries': args.invalid_retries,
                   'subagents': args.subagents, 'account_index': 0}
        outer_timeout = (args.invalid_retries + 1) * (args.timeout + 180) + 60
    else:
        inner = Path(__file__).with_name('openclaw_gen_inner.py')
        staged = {'case_id': task['case_id'], 'prompt': task['prompt'], 'refs': []}
        for index, source in enumerate(task['refs']):
            folder = attempt / 'images' / str(index)
            folder.mkdir()
            shutil.copyfile(source, folder / Path(source).name)
            staged['refs'].append(f'/images/{index}/{Path(source).name}')
        shutil.copytree(ROOT / 'mcp/image_gen', attempt / 'mcp', ignore=shutil.ignore_patterns('node_modules'))
        (attempt / 'mcp/node_modules').mkdir(exist_ok=True)
        write(attempt / 'input/image.json', {'backends': {'gemini': {'accounts': []}}})
        request = {'task': staged, 'strategy': args.strategy, 'timeout_s': args.timeout,
                   'pipe_mode': args.pipe_mode, 'provider': args.openclaw_provider,
                   'image_url': args.image_service_url, 'image_token': args.image_service_token,
                   'tool_timeout': args.tool_timeout}
        outer_timeout = args.timeout + 180
    shutil.copyfile(inner, attempt / 'input/inner.py')
    write(attempt / 'input/request.json', request)
    start = time.monotonic()
    status = runner.execute(sandbox_command(args, attempt, phase), attempt, outer_timeout)
    path = attempt / 'output/row.json'
    if status['exit_code'] == 0 and not status['timed_out'] and path.is_file():
        result = read(path)
    else:
        result = {'status': 'invalid', 'is_invalid': True, 'error_msg': 'sandbox_timeout' if status['timed_out'] else 'sandbox_exit'}
    if not isinstance(result, dict):
        result = {'status': 'invalid', 'is_invalid': True, 'error_msg': 'malformed_result'}
    if phase == 'judge':
        def flag(name):
            return str(result.get(name, False)).lower() in {'true', '1', 'yes'}
        # A missing/truncated row must not silently become a valid Fail score.
        fields = ('is_invalid', 'is_pass', 'is_uncertain')
        well_formed = isinstance(result, dict) and all(type(result.get(k)) is bool for k in fields)
        invalid = not well_formed or flag('is_invalid') or (flag('is_pass') and flag('is_uncertain'))
        if not well_formed:
            result.setdefault('error_msg', 'malformed_judgment_row')
        result.update(status='invalid' if invalid else 'success', is_invalid=invalid,
                      score=None if invalid else 2 if flag('is_pass') else 1 if flag('is_uncertain') else 0,
                      task_id=task['task_id'], candidate_path=task['candidate_path'])
    elif result.get('status') == 'success':
        selected = Path(result.get('output_path', ''))
        if not selected.is_absolute() or not selected.is_relative_to('/output') or '..' in selected.parts:
            raise ValueError('Invalid OpenClaw output selection')
        output = (attempt / 'output' / selected.relative_to('/output')).resolve(strict=True)
        if not output.is_relative_to((attempt / 'output').resolve()):
            raise ValueError('OpenClaw output escaped sandbox')
        result['output_path'] = str(output)
    result.update(case_id=task['case_id'], agent='openclaw', model=args.model,
                  attempt_dir=str(attempt), sandbox_process=status, sandbox_wall_s=time.monotonic() - start)
    return result
