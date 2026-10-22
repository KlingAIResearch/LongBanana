import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from longbanana.datasets import Dataset, resolve_bindings
from longbanana.experiment import Store, scores
from longbanana.agents.runner import planner_environment
from longbanana.providers.router import Router, to_anthropic
from longbanana.supervisor import run
from longbanana.util import sha, write


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        from PIL import Image
        for name in ('ref.png', 'background.png', 'candidate.png'):
            Image.new('RGB', (8, 8), 'red').save(self.root / name)
        self.cases = [{'case_id': 'LAC-001', 'category': 'LAC', 'prompt': 'Place the red object on the table.',
                       'references': [{'id': 'R01', **self.asset('ref.png')}], 'background': self.asset('background.png')}]
        self.checks = [{'case_id': 'LAC-001', 'check_id': '1', 'category': 'identity_check',
                        'question': 'Is the object red?', 'options': ['pass', 'fail', 'uncertain'], 'reference_ids': ['R01']}]
        self.rewrite()

    def asset(self, name):
        return {'path': name, 'sha256': sha(self.root / name)}

    def rewrite(self):
        for name, values in [('public.jsonl', self.cases), ('checks.jsonl', self.checks)]:
            (self.root / name).write_text(''.join(json.dumps(v) + '\n' for v in values))
        self.manifest = {'schema_version': 1, 'release': 'open_v1', 'revision': 'test-1',
                         'public_tasks': self.asset('public.jsonl'), 'checks': self.asset('checks.jsonl'),
                         'counts': {'cases': 1, 'references': 1, 'backgrounds': 1, 'checks': len(self.checks)}}
        write(self.root / 'manifest.json', self.manifest)

    def dataset(self, evaluation=True):
        return Dataset(self.root / 'manifest.json', evaluation)

    def candidate_manifest(self):
        write(self.root / 'candidates.json', {'dataset_fingerprint': self.dataset().fingerprint,
              'images': [{'case_id': 'LAC-001', **self.asset('candidate.png')}]})
        return self.root / 'candidates.json'


class DatasetTests(Fixture):
    def test_background_order_and_no_private_fields(self):
        task = self.dataset(False).generation_tasks()[0]
        self.assertEqual(set(task), {'case_id', 'prompt', 'refs'})
        self.assertEqual([Path(p).name for p in task['refs']], ['background.png', 'ref.png'])

    def test_tampered_ref_rejected(self):
        (self.root / 'ref.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.dataset()

    def test_explicit_bindings_only(self):
        self.checks[0]['reference_ids'] = ['R99']
        self.rewrite()
        with self.assertRaisesRegex(ValueError, 'Unknown bound'):
            self.dataset()

    def test_empty_binding_needs_rationale(self):
        self.checks[0]['reference_ids'] = []
        self.rewrite()
        with self.assertRaisesRegex(ValueError, 'rationale'):
            self.dataset()
        self.checks[0]['candidate_only_reason'] = 'Checks the complete canvas aspect ratio.'
        self.rewrite()
        self.assertEqual(self.dataset().checks[0]['category'], 'identity_check')

    def test_duplicate_check_rejected(self):
        self.checks.append(copy.deepcopy(self.checks[0]))
        self.rewrite()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.dataset()

    def test_paths_cannot_escape(self):
        self.cases[0]['references'][0]['path'] = '../outside.png'
        self.rewrite()
        with self.assertRaisesRegex(ValueError, 'relative paths'):
            self.dataset()

    def test_candidate_revision_must_match(self):
        path = self.candidate_manifest()
        self.manifest['revision'] = 'test-2'
        write(self.root / 'manifest.json', self.manifest)
        with self.assertRaisesRegex(ValueError, 'revision'):
            self.dataset().judge_tasks(path)

    def test_reference_subset_and_release_scoped_id(self):
        path = self.candidate_manifest()
        one = self.dataset().judge_tasks(path)[0]
        self.assertEqual(one['refs'], [str(self.root / 'ref.png')])
        self.manifest['release'] = 'open_v1p5'
        write(self.root / 'manifest.json', self.manifest)
        write(path, {'dataset_fingerprint': self.dataset().fingerprint,
                     'images': [{'case_id': 'LAC-001', **self.asset('candidate.png')}]})
        two = self.dataset().judge_tasks(path)[0]
        self.assertNotEqual(one['task_id'], two['task_id'])

    def test_graph_binding_order(self):
        graph = {'references': [{'reference_id': 'R01'}, {'reference_id': 'R02'}],
                 'nodes': [{'id': 'N1'}], 'evidence_edges': [{'src': 'R02', 'dst': 'N1'}, {'src': 'R01', 'dst': 'N1'}]}
        self.assertEqual(resolve_bindings({'members': ['N1']}, graph), ['R01', 'R02'])
        with self.assertRaises(ValueError):
            resolve_bindings({'members': ['N2']}, graph)

    def test_graph_constraint_evidence_is_not_dropped(self):
        graph = {'references': [{'reference_id': 'R01'}, {'reference_id': 'R02'}],
                 'nodes': [{'id': 'N1'}], 'constraints': [{'id': 'C1', 'members': ['N1']}],
                 'evidence_edges': [{'src': 'R01', 'dst': 'N1'}, {'src': 'R02', 'dst': 'C1'}]}
        self.assertEqual(resolve_bindings({'members': ['N1'], 'source': 'constraint:C1'}, graph), ['R01', 'R02'])
        with self.assertRaisesRegex(ValueError, 'source'):
            resolve_bindings({'members': ['N1'], 'source': 'constraint:C9'}, graph)


class StoreTests(Fixture):
    def test_resume_identity_and_hash(self):
        store = Store(self.root / 'run', {'model': 'test'})
        with self.assertRaises(ValueError):
            Store(store.root, {'model': 'other'}, True)
        with self.assertRaises(ValueError):
            Store(store.root, {'model': 'test'})
        self.assertEqual(Store(store.root, {'model': 'test'}, True).fingerprint, store.fingerprint)
        attempt = store.attempt('a')
        store.save('a', 'fp', {'status': 'success', 'output_path': str(self.root / 'candidate.png')}, attempt)
        self.assertIsNotNone(store.completed('a', 'fp'))
        self.assertIsNone(store.completed('a', 'changed'))
        (self.root / 'candidate.png').write_bytes(b'tampered')
        self.assertIsNone(store.completed('a', 'fp'))

    def test_lock_rejects_duplicate_owner(self):
        store = Store(self.root / 'run', {})
        with store.lock('a'):
            with self.assertRaises(RuntimeError):
                with store.lock('a'):
                    pass

    def test_scores_are_case_means_not_check_means(self):
        tasks = [{'task_id': str(i), 'case_id': 'a' if i < 2 else 'b'} for i in range(3)]
        rows = [{'task_id': str(i), 'status': 'success', 'score': 2 if i < 2 else 0} for i in range(3)]
        value = scores(rows, tasks, {'a': 'LAC', 'b': 'RGC'})
        self.assertEqual(value['overall'], 50)
        self.assertTrue(value['complete'])
        rows[2].update(status='invalid', score=None)
        self.assertTrue(scores(rows, tasks, {'a': 'LAC', 'b': 'RGC'})['provisional'])
        with self.assertRaises(ValueError):
            scores(rows + [rows[0]], tasks, {'a': 'LAC', 'b': 'RGC'})


class ProviderTests(unittest.TestCase):
    def test_agent_only_receives_scoped_token(self):
        args = SimpleNamespace(pass_env=[], agent='codex', planner_token='loopback-test', planner_base_url='http://127.0.0.1:1234')
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'upstream', 'ANTHROPIC_API_KEY': 'upstream',
                                    'GEMINI_API_KEY': 'upstream', 'GOOGLE_API_KEY': 'upstream'}):
            env = planner_environment(args, judge=True)
        self.assertEqual(env['OPENAI_API_KEY'], 'loopback-test')
        self.assertNotIn('upstream', env.values())
        self.assertNotIn('IMAGE_GEN_CONFIG', env)

    def test_native_payload_preserves_encrypted_content(self):
        config = {'protocol': 'responses', 'model': 'test', 'base_url': 'https://api.openai.com/v1', 'api_key_env': 'TEST_KEY'}
        with patch.dict(os.environ, {'TEST_KEY': 'dummy'}):
            router = Router(config)
        body = {'model': 'test', 'input': [{'type': 'reasoning', 'encrypted_content': 'opaque-test'}], 'stream': True}
        with patch.object(router.endpoint, 'open') as call:
            router.open_native(body, 'responses')
            self.assertEqual(call.call_args.args[0], body)
        with self.assertRaisesRegex(ValueError, 'conversion'):
            router.run({'model': 'test', 'messages': []}, 'anthropic')

    def test_unknown_model_rejected(self):
        config = {'protocol': 'responses', 'model': 'test', 'base_url': 'https://api.openai.com/v1', 'api_key_env': 'TEST_KEY'}
        with patch.dict(os.environ, {'TEST_KEY': 'dummy'}):
            router = Router(config)
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            router.open_native({'model': 'other'}, 'responses')

    def test_anthropic_tool_result(self):
        body = {'contents': [{'role': 'model', 'parts': [{'functionCall': {'id': 'call1', 'name': 'read', 'args': {'path': 'a'}}}]},
                             {'role': 'user', 'parts': [{'functionResponse': {'id': 'call1', 'name': 'read', 'response': {'ok': True}}}]}]}
        result = to_anthropic(body, 'test')
        self.assertEqual(result['messages'][0]['content'][0]['type'], 'tool_use')
        self.assertEqual(result['messages'][1]['content'][0]['tool_use_id'], 'call1')


class SupervisorTests(Fixture):
    def config(self):
        (self.root / 'runtime-bin').write_text('fixture-runtime')
        write(self.root / 'runtime.json', {'codex': {'version': 'test', 'command': ['runtime-bin']},
                                         'node': {'version': 'test', 'command': ['runtime-bin']}})
        for name in ('@modelcontextprotocol/sdk', 'sharp', 'zod'):
            write(self.root / 'modules' / name / 'package.json', {'name': name, 'version': 'test'})
        value = {'dataset': 'manifest.json', 'agent': 'codex', 'workers': 2,
                 'runtime': {'manifest': 'runtime.json', 'bwrap': 'runtime-bin', 'mcp_modules': 'modules'},
                 'model': {'protocol': 'responses', 'model': 'test', 'base_url': 'https://api.openai.com/v1', 'api_key_env': 'TEST_KEY'},
                 'image': {'protocol': 'gemini', 'model': 'gemini-3.1-flash-image', 'base_url': 'https://generativelanguage.googleapis.com/v1beta', 'api_key_env': 'TEST_KEY'}}
        write(self.root / 'config.json', value)
        return self.root / 'config.json'

    def test_dry_run_never_launches_or_calls_api(self):
        with patch('longbanana.supervisor.runner.probe') as probe, patch('longbanana.supervisor.Router') as router:
            result = run(self.config(), 'generate', self.root / 'output', dry_run=True)
        self.assertEqual(result['tasks'], 1)
        probe.assert_not_called()
        router.assert_not_called()
        self.assertFalse((self.root / 'output').exists())

    def test_generate_resume_reuses_valid_output(self):
        config = self.config()
        calls = []
        def fake_generate(args, task, record):
            from PIL import Image
            calls.append(task['case_id'])
            out = args.output_dir / 'image.png'
            Image.new('RGB', (8, 8)).save(out)
            return {'case_id': task['case_id'], 'status': 'success', 'output_path': str(out)}
        with patch.dict(os.environ, {'TEST_KEY': 'dummy'}), patch('longbanana.supervisor.runner.probe'), \
             patch('longbanana.supervisor.create_server'), patch('longbanana.supervisor.create_image_server'), \
             patch('longbanana.supervisor.launch_service', return_value='http://127.0.0.1:1234'), \
             patch('longbanana.supervisor.runner.run_one', side_effect=fake_generate):
            self.assertTrue(run(config, 'generate', self.root / 'output')['complete'])
            self.assertTrue(run(config, 'generate', self.root / 'output', resume=True)['complete'])
        self.assertEqual(calls, ['LAC-001'])
        self.assertEqual(len(self.dataset().judge_tasks(self.root / 'output/candidates.json')), 1)

    def test_judge_uses_bound_refs_without_image_service(self):
        config = self.config()
        candidates = self.candidate_manifest()
        calls = []
        def fake_judge(args, task, record):
            calls.append(task['task_id'])
            self.assertFalse(args.mcp_enabled)
            self.assertEqual(task['refs'], [str(self.root / 'ref.png')])
            return {'case_id': task['case_id'], 'task_id': task['task_id'], 'status': 'success', 'score': 1, 'is_invalid': False}
        with patch.dict(os.environ, {'TEST_KEY': 'dummy'}), patch('longbanana.supervisor.runner.probe'), \
             patch('longbanana.supervisor.create_server'), patch('longbanana.supervisor.create_image_server') as image, \
             patch('longbanana.supervisor.launch_service', return_value='http://127.0.0.1:1234'), \
             patch('longbanana.supervisor.judge.run_judge', side_effect=fake_judge):
            result = run(config, 'judge', self.root / 'judge-output', candidates)
            self.assertEqual(result['overall'], 50)
            self.assertTrue(result['complete'])
            run(config, 'judge', self.root / 'judge-output', candidates, resume=True)
            image.assert_not_called()
        self.assertEqual(len(calls), 1)

    def test_unknown_adapter_fails_before_launch(self):
        config = self.config()
        value = json.loads(config.read_text())
        value['agent'] = 'unknown-agent'
        write(config, value)
        with self.assertRaisesRegex(ValueError, 'Unknown agent'):
            run(config, 'generate', self.root / 'output', dry_run=True)
        self.assertFalse((self.root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
