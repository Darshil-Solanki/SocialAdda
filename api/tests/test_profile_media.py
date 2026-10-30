import io
import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from .base import ApiTestCase, make_user


def png_upload(name):
    buffer = io.BytesIO()
    Image.new('RGB', (8, 8), color=(20, 120, 200)).save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class ProfileMediaTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        # Uploads go to a throwaway directory, never the project's media folder.
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.alice = make_user('alice')
        self.api.force_authenticate(self.alice)

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)
        super().tearDown()

    def test_cover_photo_upload_is_stored_and_returned(self):
        response = self.api.patch('/api/v1/me/', {'cover': png_upload('cover.png')}, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.cover.name.startswith('covers/'))
        self.assertTrue(os.path.exists(os.path.join(self.media_root, self.alice.cover.name)))
        self.assertIn('/media/covers/', response.json()['cover'])

    def test_cover_is_visible_on_the_public_profile(self):
        self.api.patch('/api/v1/me/', {'cover': png_upload('cover.png')}, format='multipart')
        profile = self.api.get('/api/v1/users/alice/').json()
        self.assertIn('/media/covers/', profile['cover'])

    def test_avatar_upload_is_stored(self):
        response = self.api.patch('/api/v1/me/', {'profile_pic': png_upload('me.png')}, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.profile_pic.name.startswith('profile_pic/'))

    def test_non_image_upload_is_rejected(self):
        bogus = SimpleUploadedFile('notes.txt', b'not an image', content_type='text/plain')
        response = self.api.patch('/api/v1/me/', {'cover': bogus}, format='multipart')
        self.assertEqual(response.status_code, 400)

    def test_remove_photo_and_cover_blank_them_and_delete_the_files(self):
        self.api.patch('/api/v1/me/', {'profile_pic': png_upload('me.png'), 'cover': png_upload('c.png')},
                       format='multipart')
        self.alice.refresh_from_db()
        stored = [os.path.join(self.media_root, self.alice.profile_pic.name),
                  os.path.join(self.media_root, self.alice.cover.name)]
        self.assertTrue(all(os.path.exists(path) for path in stored))

        response = self.api.patch('/api/v1/me/', {'remove_profile_pic': True, 'remove_cover': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['profile_pic'])
        self.assertIsNone(response.json()['cover'])
        self.alice.refresh_from_db()
        self.assertFalse(self.alice.profile_pic)
        self.assertFalse(self.alice.cover)
        self.assertFalse(any(os.path.exists(path) for path in stored))

    def test_replacing_the_photo_deletes_the_old_file(self):
        self.api.patch('/api/v1/me/', {'profile_pic': png_upload('first.png')}, format='multipart')
        self.alice.refresh_from_db()
        old_path = os.path.join(self.media_root, self.alice.profile_pic.name)
        self.api.patch('/api/v1/me/', {'profile_pic': png_upload('second.png')}, format='multipart')
        self.alice.refresh_from_db()
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(os.path.join(self.media_root, self.alice.profile_pic.name)))
