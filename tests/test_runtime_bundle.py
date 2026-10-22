import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_bundle', ROOT / 'tools/verify_openclaw_runtime.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RuntimeBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.runtime = self.root / 'openclaw-runtime'
        self.runtime.mkdir()
        package = self.runtime / 'package.json'
        package.write_text('{"version":"1"}')
        self.manifest = {'schema_version': 1, 'version': '1',
                         'files': {'package.json': hashlib.sha256(package.read_bytes()).hexdigest()}}
        self.save_manifest()

    def save_manifest(self):
        (self.root / 'openclaw-runtime.sha256.json').write_text(json.dumps(self.manifest))

    def test_valid_and_installed_dependencies(self):
        deps = self.runtime / 'node_modules'
        deps.mkdir()
        (deps / 'fixture').write_text('separately fingerprinted')
        self.assertTrue(module.verify(self.root)['passed'])

    def test_modified_or_missing_file(self):
        package = self.runtime / 'package.json'
        package.write_text('{}')
        with self.assertRaises(ValueError):
            module.verify(self.root)
        package.unlink()
        with self.assertRaises(ValueError):
            module.verify(self.root)

    def test_extra_file(self):
        (self.runtime / 'unexpected.js').write_text('')
        with self.assertRaises(ValueError):
            module.verify(self.root)

    def test_path_traversal(self):
        self.manifest['files']['../escape'] = '0' * 64
        self.save_manifest()
        with self.assertRaises(ValueError):
            module.verify(self.root)

    def test_symlink_rejected(self):
        package = self.runtime / 'package.json'
        package.rename(self.root / 'outside.json')
        package.symlink_to(self.root / 'outside.json')
        with self.assertRaises(ValueError):
            module.verify(self.root)

    def test_release_bundle(self):
        if not (ROOT / 'openclaw-runtime').exists():
            self.skipTest('Optional runtime assets are not present in the Python package')
        result = module.verify(ROOT)
        self.assertEqual(result['version'], '2026.4.16')
        self.assertGreater(result['files_verified'], 7000)
