import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('release_audit', Path(__file__).resolve().parents[1] / 'tools/audit_release.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleaseAuditTests(unittest.TestCase):
    def test_official_template_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'example.json').write_text(json.dumps({
                'base_url': 'https://api.openai.com/v1', 'api_key_env': 'OPENAI_API_KEY',
                'token': '${USER_TOKEN}', 'data': '/data/open_v1'}))
            self.assertTrue(module.audit(root)['passed'])

    def test_sensitive_content_is_detected_without_echo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            key = 'sk-' + 'a' * 36
            host = 'http://' + '10.' + '12.13.14:8080'
            (root / 'settings.json').write_text(json.dumps({'api_key': key, 'url': host}))
            report = module.audit(root)
            self.assertFalse(report['passed'])
            self.assertNotIn(key, json.dumps(report))
            self.assertNotIn(host, json.dumps(report))
            self.assertTrue({'credential', 'private-ip'} <= {r['rule'] for r in report['findings']})

    def test_external_policy_checks_names_and_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'organization-route.json').write_text('deployment-label')
            report = module.audit(root, {'forbidden_literals': ['organization-route', 'deployment-label']})
            self.assertFalse(report['passed'])
            self.assertTrue(any(r['rule'].endswith('-filename') for r in report['findings']))

    def test_symlinks_and_binary_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'blob.bin').write_bytes(b'\xff\xfe')
            (root / 'outside').symlink_to(root.parent)
            report = module.audit(root)
            self.assertEqual({'binary-requires-review', 'symlink'}, {r['rule'] for r in report['findings']})

    def test_ignored_files_are_still_examined(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.gitignore').write_text('.env\n')
            (root / '.env').write_text('TOKEN=example')
            self.assertFalse(module.audit(root)['passed'])


if __name__ == '__main__':
    unittest.main()
