from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from main.models import Post, User


def referenced_names():
    names = set()
    for profile_pic, cover in User.objects.values_list('profile_pic', 'cover'):
        names.update((profile_pic, cover))
    for image, thumbnail in Post.objects.values_list('content_image', 'content_thumbnail'):
        names.update((image, thumbnail))
    names.discard('')
    return names


def stored_names(directory=''):
    directories, files = default_storage.listdir(directory)
    for name in files:
        yield f'{directory}/{name}' if directory else name
    for sub in directories:
        yield from stored_names(f'{directory}/{sub}' if directory else sub)


class Command(BaseCommand):
    help = (
        'Lists uploaded files that no user or post refers to. Nothing is deleted unless --delete is given. '
        'Works with local disk and S3 storage.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Delete the unreferenced files.')

    def handle(self, *args, **options):
        referenced = referenced_names()
        orphans = sorted(name for name in stored_names() if name not in referenced)
        for name in orphans:
            self.stdout.write(name)
            if options['delete']:
                default_storage.delete(name)
        verb = 'Deleted' if options['delete'] else 'Found (use --delete to remove)'
        self.stdout.write(self.style.SUCCESS(f'{verb}: {len(orphans)} unreferenced file(s).'))
