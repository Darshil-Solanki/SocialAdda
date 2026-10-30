import boto3
from django.test import SimpleTestCase, override_settings
from moto import mock_aws

from SocialAdda.storage import FILESYSTEM_BACKEND, S3_BACKEND, media_storage_config

from .base import ApiTestCase, make_user
from .test_profile_media import png_upload

BUCKET = 'socialadda-test-media'
REGION = 'us-east-1'


class StorageConfigTests(SimpleTestCase):
    def test_local_storage_is_the_default(self):
        self.assertEqual(media_storage_config({})['default']['BACKEND'], FILESYSTEM_BACKEND)

    def test_s3_options_come_from_the_environment(self):
        config = media_storage_config({
            'MEDIA_STORAGE': 's3',
            'AWS_STORAGE_BUCKET_NAME': 'my-bucket',
            'AWS_S3_ENDPOINT_URL': 'http://localhost:9000',
            'AWS_ACCESS_KEY_ID': 'key',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        })
        self.assertEqual(config['default']['BACKEND'], S3_BACKEND)
        options = config['default']['OPTIONS']
        self.assertEqual(options['bucket_name'], 'my-bucket')
        self.assertEqual(options['endpoint_url'], 'http://localhost:9000')
        self.assertFalse(options['querystring_auth'])

    def test_s3_without_a_bucket_fails_fast(self):
        with self.assertRaises(ValueError):
            media_storage_config({'MEDIA_STORAGE': 's3'})


@mock_aws
class S3UploadTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        # Simulated S3 for the duration of the test; nothing reaches AWS.
        s3_mock = mock_aws()
        s3_mock.start()
        self.addCleanup(s3_mock.stop)
        boto3.client('s3', region_name=REGION).create_bucket(Bucket=BUCKET)

        storage = override_settings(STORAGES=media_storage_config({
            'MEDIA_STORAGE': 's3',
            'AWS_STORAGE_BUCKET_NAME': BUCKET,
            'AWS_S3_REGION_NAME': REGION,
        }))
        storage.enable()
        self.addCleanup(storage.disable)

        self.alice = make_user('alice')
        self.api.force_authenticate(self.alice)

    def test_cover_upload_lands_in_the_bucket(self):
        response = self.api.patch('/api/v1/me/', {'cover': png_upload('cover.png')}, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.alice.refresh_from_db()

        stored = boto3.client('s3', region_name=REGION).head_object(Bucket=BUCKET, Key=self.alice.cover.name)
        self.assertGreater(stored['ContentLength'], 0)
        self.assertIn(BUCKET, response.json()['cover'])
