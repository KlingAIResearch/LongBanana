import unittest
from unittest.mock import patch

from test_core import Fixture
from longbanana import direct, legacy_direct
from longbanana.util import read, write


class Client:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def image_part(self, image):
        return {'size': image.size}

    def generate_text_with_usage(self, contents, config):
        self.calls.append((contents, config))
        return {'text': next(self.replies), 'model': 'fixture', 'usage': {'total_tokens': 10}}


class DirectTests(Fixture):
    def task(self):
        return self.dataset().judge_tasks(self.candidate_manifest())[0]

    def test_original_rubric_image_order_and_retries(self):
        task = self.task()
        client = Client(['not JSON', '{"answer":"pass"}'])
        result = legacy_direct.judge_one(client, task, legacy_direct.Theta())
        self.assertTrue(result['is_pass'])
        self.assertFalse(result['is_invalid'])
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(result['total_tokens'], 20)
        contents, config = client.calls[0]
        self.assertEqual(len(contents), 3)
        self.assertIn('其余为参考图', contents[0])
        self.assertEqual(config, {'max_output_tokens': 8192})

    def test_global_only_attaches_candidate(self):
        task = self.task()
        task['category'] = 'global_check'
        client = Client(['{"answer":"uncertain"}'])
        result = legacy_direct.judge_one(client, task, legacy_direct.Theta())
        self.assertFalse(result['is_invalid'])
        self.assertTrue(result['is_uncertain'])
        self.assertEqual(len(client.calls[0][0]), 2)
        self.assertIn('不提供任何参考图', client.calls[0][0][0])

    def test_invalid_does_not_become_a_fail(self):
        client = Client(['{"answer":"unlisted"}'] * 10)
        result = legacy_direct.judge_one(client, self.task(), legacy_direct.Theta())
        self.assertTrue(result['is_invalid'])
        self.assertEqual(len(client.calls), 10)

    def test_direct_dry_run_and_resume_without_agent_runtime(self):
        config = self.root / 'config.json'
        write(config, {'dataset': 'manifest.json', 'agent': 'direct-vlm', 'workers': 2,
                       'model': {'protocol': 'gemini', 'base_url': 'https://example.org/v1beta',
                                 'model': 'fixture', 'api_key_env': 'EXAMPLE_TEST_KEY'}})
        candidates = self.candidate_manifest()
        with patch.object(direct, 'Endpoint') as endpoint:
            plan = direct.run(config, self.root / 'run', candidates, dry_run=True)
            endpoint.assert_not_called()
            self.assertEqual(plan['tasks'], 1)
        fake = type('Endpoint', (), {'model': 'fixture'})()
        with patch.object(direct, 'Endpoint', return_value=fake), \
             patch.object(direct, 'GeminiClient', side_effect=lambda *a: Client(['{"answer":"pass"}'])) as factory:
            first = direct.run(config, self.root / 'run', candidates)
            second = direct.run(config, self.root / 'run', candidates, resume=True)
        self.assertEqual(factory.call_count, 1)
        self.assertTrue(first['complete'])
        self.assertEqual(second['overall'], 100)


if __name__ == '__main__':
    unittest.main()
