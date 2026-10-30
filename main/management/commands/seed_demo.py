import random

from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import Post, User
from main.services import add_comment, set_follow, set_like
from main.tasks import fanout_post_task

DEMO_PASSWORD = 'demo-pass-123'
SAMPLE_TEXTS = [
    'Good morning from the terrace!',
    'Finally finished the project. Coffee time.',
    'Anyone watching the match tonight?',
    'Trying a new recipe. Wish me luck.',
    'Rain all day, perfect for reading.',
    'Shipped the feature. Feels great.',
]


class Command(BaseCommand):
    help = 'Creates a deterministic set of demo users, follows, posts, likes and comments.'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=12)
        parser.add_argument('--posts-per-user', type=int, default=3)
        parser.add_argument('--seed', type=int, default=42)

    def handle(self, *args, **options):
        rng = random.Random(options['seed'])
        users = self.create_users(options['users'])
        with transaction.atomic():
            self.create_follows(users, rng)
            posts = self.create_posts(users, options['posts_per_user'], rng)
        self.create_engagement(users, posts, rng)
        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(users)} users (password "{DEMO_PASSWORD}"), {len(posts)} posts.'
        ))

    def create_users(self, count):
        users = []
        for index in range(1, count + 1):
            username = f'demo{index}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.test',
                    'first_name': f'Demo{index}',
                    'last_name': 'User',
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users.append(user)
        return users

    def create_follows(self, users, rng):
        for user in users:
            others = [other for other in users if other.pk != user.pk]
            for followee in rng.sample(others, k=min(4, len(others))):
                set_follow(user, followee, follow=True)

    def create_posts(self, users, per_user, rng):
        posts = []
        for user in users:
            for _ in range(per_user):
                post = Post.objects.create(creater=user, content_text=rng.choice(SAMPLE_TEXTS))
                fanout_post_task.delay(post.pk)
                posts.append(post)
        return posts

    def create_engagement(self, users, posts, rng):
        for post in posts:
            for liker in rng.sample(users, k=rng.randint(0, min(5, len(users)))):
                set_like(post, liker, liked=True)
            if rng.random() < 0.5:
                commenter = rng.choice(users)
                add_comment(post, commenter, rng.choice(SAMPLE_TEXTS)[:90])
