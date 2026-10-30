"""
Media storage selection.

MEDIA_STORAGE=local (default) keeps uploads in the project's media/ folder.
MEDIA_STORAGE=s3 stores them in an S3-compatible bucket (AWS S3, or MinIO for local work).
"""

FILESYSTEM_BACKEND = 'django.core.files.storage.FileSystemStorage'
S3_BACKEND = 'storages.backends.s3.S3Storage'


def media_storage_config(environ):
    """Returns the STORAGES setting for the chosen media backend."""
    static = {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}
    if environ.get('MEDIA_STORAGE', 'local').lower() != 's3':
        return {'default': {'BACKEND': FILESYSTEM_BACKEND}, 'staticfiles': static}

    bucket = environ.get('AWS_STORAGE_BUCKET_NAME')
    if not bucket:
        raise ValueError('MEDIA_STORAGE=s3 requires AWS_STORAGE_BUCKET_NAME.')

    options = {
        'bucket_name': bucket,
        'region_name': environ.get('AWS_S3_REGION_NAME') or None,
        # Endpoint is only set for S3-compatible servers such as MinIO; AWS needs none.
        'endpoint_url': environ.get('AWS_S3_ENDPOINT_URL') or None,
        'access_key': environ.get('AWS_ACCESS_KEY_ID') or None,
        'secret_key': environ.get('AWS_SECRET_ACCESS_KEY') or None,
        # Public URLs without signatures, so the frontend can render images directly.
        'querystring_auth': False,
        'file_overwrite': False,
    }
    if environ.get('AWS_S3_CUSTOM_DOMAIN'):
        options['custom_domain'] = environ['AWS_S3_CUSTOM_DOMAIN']
    return {'default': {'BACKEND': S3_BACKEND, 'OPTIONS': options}, 'staticfiles': static}
