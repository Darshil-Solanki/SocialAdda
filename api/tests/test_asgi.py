import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class AsgiImportTests(SimpleTestCase):
    def test_asgi_module_imports_in_a_fresh_process(self):
        # A fresh interpreter has no settings configured, just like daphne at startup.
        env = {key: value for key, value in os.environ.items() if key != 'DJANGO_SETTINGS_MODULE'}
        result = subprocess.run(
            [sys.executable, '-c', 'import SocialAdda.asgi'],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
