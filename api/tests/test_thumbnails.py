import os
import shutil
import tempfile

from django.test import override_settings
from PIL import Image

from main.models import Post

from .base import ApiTestCase, make_user
from .test_profile_media import png_upload


class ThumbnailTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.addCleanup(self.cleanup_media)
        self.alice = make_user('alice')
        self.api.force_authenticate(self.alice)

    def cleanup_media(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_uploaded_post_image_gets_a_webp_thumbnail(self):
        response = self.api.post('/api/v1/posts/', {'content_image': png_upload('big.png')}, format='multipart')
        self.assertEqual(response.status_code, 201)

        post = Post.objects.get(pk=response.json()['id'])
        self.assertTrue(post.content_thumbnail.name.startswith('posts/thumbs/'))
        self.assertTrue(post.content_thumbnail.name.endswith('.webp'))
        with Image.open(os.path.join(self.media_root, post.content_thumbnail.name)) as thumb:
            self.assertEqual(thumb.format, 'WEBP')
            self.assertLessEqual(max(thumb.size), 480)

    def test_text_only_post_has_no_thumbnail(self):
        response = self.api.post('/api/v1/posts/', {'content_text': 'just words'}, format='json')
        self.assertIsNone(response.json()['content_thumbnail'])
