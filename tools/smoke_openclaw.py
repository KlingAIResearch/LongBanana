"""Real sandbox/CLI/Gateway smoke against a local deterministic model fixture.

Use an existing OpenClaw experiment configuration for its runtime locations only.
The fixture replaces every provider and supplies synthetic images. No provider
credential is required and no upstream model or image API is contacted.
"""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading

from PIL import Image

from longbanana.datasets import Dataset
from longbanana.supervisor import run
from longbanana.util import expand, read, sha, write


class Fixture(BaseHTTPRequestHandler):
    calls = []
    lock = threading.Lock()
    phase = 'judge'
    image = ''

    def log_message(self, *_):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        tools = [f['name'] for t in body.get('tools', []) for f in t.get('functionDeclarations', [])]
        contents = json.dumps(body.get('contents', []))
        generate_tool = next((name for name in tools if name.endswith('generate_image')), None)
        if 'IMAGE' in body.get('generationConfig', {}).get('responseModalities', []):
            part = {'inlineData': {'mimeType': 'image/png', 'data': self.image}}
            kind = 'image'
        elif self.phase == 'generate' and generate_tool and '"functionResponse"' not in contents:
            part = {'functionCall': {'name': generate_tool, 'args': {
                'prompt': 'Draw a red square.', 'reference_images': ['/images/0/reference.png'],
                'output_dir': '/output/pipe/openclaw/gemini/fixture'}}}
            kind = 'generate_tool'
        elif self.phase == 'generate':
            part = {'text': 'The image is complete and saved in the requested output directory.'}
            kind = 'generation_done'
        elif 'sessions_spawn' in tools and '"functionResponse"' not in contents:
            part = {'functionCall': {'name': 'sessions_spawn', 'args': {
                'agentId': 'identity-judge', 'thinking': 'high',
                'task': 'Inspect candidate /images/candidate.png and reference /images/R01__reference.png. '
                        'Compare visible red squares. Return identity evidence. Do not spawn agents.'}}}
            kind = 'spawn'
        elif tools == ['session_status']:
            part = {'text': 'The candidate and reference both contain the same red square.'}
            kind = 'child'
        else:
            part = {'text': '<answer>{"answer":"pass","reason":"Both squares are red",'
                            '"evidence":["red square"],"subagent_evidence":{"identity":["matching squares"]}}</answer>'}
            kind = 'verdict'
        with self.lock:
            self.calls.append({'kind': kind, 'tools': tools, 'images': contents.count('"inlineData"')})
        response = {'candidates': [{'content': {'role': 'model', 'parts': [part]}, 'finishReason': 'STOP'}],
                    'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 10, 'totalTokenCount': 20}}
        streaming = 'streamGenerateContent' in self.path
        payload = (('data: ' + json.dumps(response) + '\n\n') if streaming else json.dumps(response)).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream' if streaming else 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--phase', choices=('judge', 'generate'), default='judge')
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = args.config.resolve(strict=True)
    runtime = expand(read(source)['runtime'])
    runtime = {k: str((source.parent / v).absolute()) for k, v in runtime.items()}
    for name in ('reference.png', 'candidate.png'):
        Image.new('RGB', (32, 32), 'red').save(root / name)
    Fixture.phase = args.phase
    Fixture.image = base64.b64encode((root / 'reference.png').read_bytes()).decode()
    def asset(name):
        return {'path': name, 'sha256': sha(root / name)}
    tasks = [{'case_id': 'fixture', 'category': 'LAC', 'prompt': 'Draw a red square.',
              'references': [{'id': 'R01', **asset('reference.png')}]}]
    checks = [{'case_id': 'fixture', 'check_id': str(i), 'category': category,
               'question': 'Are the visible squares red?', 'guide': 'Use visible color only.',
               'options': ['pass', 'fail', 'uncertain'], 'reference_ids': ['R01'] if i else [],
               **({} if i else {'candidate_only_reason': 'Canvas color is visible in the candidate.'})}
              for i, category in enumerate(('global_check', 'identity_check'))]
    for name, rows in [('public.jsonl', tasks), ('checks.jsonl', checks)]:
        (root / name).write_text(''.join(json.dumps(row) + '\n' for row in rows))
    write(root / 'manifest.json', {'schema_version': 1, 'release': 'open_v1', 'revision': 'offline-fixture',
          'public_tasks': asset('public.jsonl'), 'checks': asset('checks.jsonl'),
          'counts': {'cases': 1, 'references': 1, 'backgrounds': 0, 'checks': 2}})
    write(root / 'candidates.json', {'dataset_fingerprint': Dataset(root / 'manifest.json').fingerprint,
          'images': [{'case_id': 'fixture', **asset('candidate.png')}]})
    server = ThreadingHTTPServer(('127.0.0.1', 0), Fixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    old = os.environ.get('LONGBANANA_OFFLINE_FIXTURE_KEY')
    os.environ['LONGBANANA_OFFLINE_FIXTURE_KEY'] = 'offline-fixture'
    config = {'agent': 'openclaw', 'dataset': str(root / 'manifest.json'), 'runtime': runtime,
              'workers': 2, 'subagents': True, 'invalid_retries': 0, 'timeout': 150,
              'model': {'protocol': 'gemini', 'base_url': f'http://127.0.0.1:{server.server_port}/v1beta',
                        'model': 'fixture-model', 'api_key_env': 'LONGBANANA_OFFLINE_FIXTURE_KEY', 'use_proxy': False}}
    if args.phase == 'generate':
        config['image'] = {**config['model'], 'model': 'fixture-image'}
    write(root / 'config.json', config)
    try:
        candidates = root / 'candidates.json' if args.phase == 'judge' else None
        summary = run(root / 'config.json', args.phase, root / 'run', candidates)
        calls = len(Fixture.calls)
        run(root / 'config.json', args.phase, root / 'run', candidates, resume=True)
        evidence = list((root / 'run').rglob('*.subagents.json'))
        report = {'summary': summary, 'fixture_calls': Fixture.calls, 'resume_no_requests': calls == len(Fixture.calls),
                  'child_evidence_files': len(evidence), 'upstream_api_calls': 0, 'real_model_quality_tested': False}
        write(root / 'smoke_report.json', report)
        print(json.dumps(report), flush=True)
        behavior_passed = bool(evidence) if args.phase == 'judge' else any(c['kind'] == 'image' for c in Fixture.calls)
        if not summary['complete'] or not report['resume_no_requests'] or not behavior_passed:
            raise RuntimeError('OpenClaw sandbox smoke failed')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(3)
        if old is None:
            os.environ.pop('LONGBANANA_OFFLINE_FIXTURE_KEY', None)
        else:
            os.environ['LONGBANANA_OFFLINE_FIXTURE_KEY'] = old


if __name__ == '__main__':
    main()
