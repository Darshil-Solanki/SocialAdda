from io import StringIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command

from .base import ApiTestCase, make_user


class PruneMediaTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user('pruner')
        self.user.profile_pic.save('keep.png', ContentFile(b'x'), save=True)
        self.orphan = default_storage.save('posts/orphan.png', ContentFile(b'x'))

    def run_command(self, *args):
        out = StringIO()
        call_command('prune_media', *args, stdout=out)
        return out.getvalue()

    def test_dry_run_lists_only_unreferenced_files_and_deletes_nothing(self):
        output = self.run_command()
        self.assertIn(self.orphan, output)
        self.assertNotIn(self.user.profile_pic.name, output)
        self.assertTrue(default_storage.exists(self.orphan))

    def test_delete_flag_removes_orphans_and_keeps_referenced_files(self):
        self.run_command('--delete')
        self.assertFalse(default_storage.exists(self.orphan))
        self.assertTrue(default_storage.exists(self.user.profile_pic.name))
