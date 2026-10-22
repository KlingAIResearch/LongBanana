"""OpenClaw deployment contracts; no agent executable or paid API is used."""
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from longbanana.agents import openclaw
from longbanana.agents.openclaw_judge_inner import install_provisioner
from longbanana.util import read, write


class OpenClawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.templates = {}
        for subagents in (False, True):
            config = {'runtime': {'python': sys.executable, 'openclaw': '/opt/openclaw'},
                      'model': {'model': 'fixture-model'}, 'subagents': subagents}
            cls.templates[subagents] = openclaw.prepare_template(config, Path('/opt/node/bin/node'))

    def test_templates_preserve_specialist_mode_without_host_credentials(self):
        normal, specialist = self.templates[False], self.templates[True]
        self.assertNotIn('gateway', normal['config'])
        self.assertIn('gateway', specialist['config'])
        self.assertEqual(len(specialist['workspace_files']), 4)
        for template in self.templates.values():
            self.assertEqual(template['credentials'], '')
            self.assertEqual(template['config']['models']['providers'], {})
            self.assertEqual(template['config']['agents']['defaults']['model'], 'longbanana/fixture-model')
            self.assertNotIn('local-provisioning-only', json.dumps(template))
            self.assertNotIn(str(openclaw.ROOT), json.dumps(template))

    def test_each_provision_has_independent_state_and_gateway_token(self):
        judge = SimpleNamespace()
        install_provisioner(judge, copy.deepcopy(self.templates[True]))
        roots = []
        try:
            first, a = judge._build_openclaw_env(openclaw_judge_subagents=True)
            roots.append(a)
            second, b = judge._build_openclaw_env(openclaw_judge_subagents=True)
            roots.append(b)
            self.assertNotEqual(a, b)
            self.assertNotEqual(first['OPENCLAW_GATEWAY_TOKEN'], second['OPENCLAW_GATEWAY_TOKEN'])
            self.assertNotEqual(first['OPENCLAW_STATE_DIR'], second['OPENCLAW_STATE_DIR'])
            self.assertEqual(read(first['OPENCLAW_CONFIG_PATH'])['gateway']['auth']['token'], first['OPENCLAW_GATEWAY_TOKEN'])
            with self.assertRaisesRegex(ValueError, 'mode differs'):
                judge._build_openclaw_env(openclaw_judge_subagents=False)
        finally:
            for root in roots:
                shutil.rmtree(root)

    def test_agent_environment_does_not_inherit_keys(self):
        with patch.dict(os.environ, {'EXAMPLE_PROVIDER_SECRET': 'private-test-value'}):
            env = openclaw.environment()
        self.assertNotIn('EXAMPLE_PROVIDER_SECRET', env)
        self.assertEqual(env['OPENCLAW_LONGBANANA_ENV_FILE'], '/input/no-host-env')

    def test_task_staging_global_branch_and_invalid_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            image = root / 'candidate.png'
            image.write_bytes(b'fixture-image-not-opened-by-mocked-execution')
            task = {k: '' for k in openclaw.FIELDS}
            task.update(case_id='LAC-001', task_id='check-1', category='global_check',
                        question='Is the scene complete?', options=['correct', 'incorrect', 'uncertain'],
                        candidate_path=str(image), refs=[str(image)])
            args = SimpleNamespace(subagents=True, openclaw_templates=self.templates,
                openclaw_provider={'apiKey': 'local-token'}, strategy='pipe', timeout=5,
                invalid_retries=0, model='fixture-model')
            cases = [({}, None), ({'is_invalid': False, 'is_pass': True, 'is_uncertain': False}, 2),
                     ({'is_invalid': False, 'is_pass': False, 'is_uncertain': True}, 1),
                     ({'is_invalid': False, 'is_pass': False, 'is_uncertain': False}, 0)]
            for index, (reply, expected) in enumerate(cases):
                args.output_dir = root / str(index)
                args.output_dir.mkdir()
                def execute(command, attempt, timeout):
                    request = read(attempt / 'input/request.json')
                    self.assertTrue(request['subagents'])
                    # The retained runner also disables specialists for global checks.
                    self.assertNotIn('gateway', request['template']['config'])
                    self.assertEqual(request['task']['refs'], ['/images/R01__candidate.png'])
                    write(attempt / 'output/row.json', reply)
                    return {'exit_code': 0, 'timed_out': False}
                with patch.object(openclaw, 'sandbox_command', return_value=['fixture']), \
                     patch.object(openclaw.runner, 'execute', side_effect=execute):
                    result = openclaw.run_task(args, task, 'judge')
                self.assertEqual(result['score'], expected)
                self.assertEqual(result['is_invalid'], expected is None)


if __name__ == '__main__':
    unittest.main()
