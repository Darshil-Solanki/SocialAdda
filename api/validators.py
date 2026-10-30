from rest_framework import serializers

MAX_IMAGE_BYTES = 5 * 1024 * 1024


def validate_image_size(file):
    """Rejects uploads above MAX_IMAGE_BYTES. Pillow checks the content type; this caps the storage cost."""
    if file.size > MAX_IMAGE_BYTES:
        raise serializers.ValidationError('Images must be 5 MB or smaller.')
