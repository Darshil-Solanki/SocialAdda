from django.db import connection
from django.test.utils import CaptureQueriesContext

from main.models import Comment, Follow, Post

from .base import ApiTestCase, make_user


class PostApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        self.api.force_authenticate(self.alice)

    def test_post_needs_text_or_image(self):
        response = self.api.post('/api/v1/posts/', {'content_text': '  '}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_text_is_limited_to_140_characters(self):
        response = self.api.post('/api/v1/posts/', {'content_text': 'x' * 141}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_author_is_the_authenticated_user(self):
        response = self.api.post('/api/v1/posts/', {'content_text': 'hi'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['author']['username'], 'alice')

    def test_only_the_author_can_edit_or_delete(self):
        post = Post.objects.create(creater=self.bob, content_text='bob says hi')
        url = f'/api/v1/posts/{post.id}/'

        self.assertEqual(self.api.patch(url, {'content_text': 'defaced'}, format='json').status_code, 403)
        self.assertEqual(self.api.delete(url).status_code, 403)

        self.api.force_authenticate(self.bob)
        self.assertEqual(self.api.patch(url, {'content_text': 'edited'}, format='json').status_code, 200)
        self.assertEqual(self.api.delete(url).status_code, 204)
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_like_is_idempotent_and_reflected_in_the_post(self):
        post = Post.objects.create(creater=self.bob, content_text='likeable')
        self.assertEqual(self.api.post(f'/api/v1/posts/{post.id}/like/').status_code, 204)
        self.assertEqual(self.api.post(f'/api/v1/posts/{post.id}/like/').status_code, 204)

        detail = self.api.get(f'/api/v1/posts/{post.id}/').json()
        self.assertEqual(detail['like_count'], 1)
        self.assertTrue(detail['is_liked'])

        self.api.delete(f'/api/v1/posts/{post.id}/like/')
        self.assertEqual(self.api.get(f'/api/v1/posts/{post.id}/').json()['like_count'], 0)

    def test_bookmarks_show_up_in_saved_posts(self):
        post = Post.objects.create(creater=self.bob, content_text='keep this')
        self.api.post(f'/api/v1/posts/{post.id}/bookmark/')
        saved = self.api.get('/api/v1/saved/').json()['results']
        self.assertEqual([item['id'] for item in saved], [post.id])
        self.assertTrue(saved[0]['is_saved'])

    def test_comments_are_created_and_counted(self):
        post = Post.objects.create(creater=self.bob, content_text='discuss')
        url = f'/api/v1/posts/{post.id}/comments/'

        created = self.api.post(url, {'body': 'first!'}, format='json')
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()['author']['username'], 'alice')
        self.assertEqual(Comment.objects.filter(post=post).count(), 1)

        self.assertEqual(self.api.post(url, {'body': 'x' * 91}, format='json').status_code, 400)
        post.refresh_from_db()
        self.assertEqual(post.comment_count, 1)
        self.assertEqual(len(self.api.get(url).json()['results']), 1)

    def test_posts_are_cursor_paginated(self):
        for index in range(12):
            Post.objects.create(creater=self.bob, content_text=f'post {index}')
        first_page = self.api.get('/api/v1/posts/').json()
        self.assertEqual(len(first_page['results']), 10)
        self.assertIsNotNone(first_page['next'])

        second_page = self.api.get(first_page['next']).json()
        self.assertEqual(len(second_page['results']), 2)
        first_ids = {item['id'] for item in first_page['results']}
        second_ids = {item['id'] for item in second_page['results']}
        self.assertTrue(first_ids.isdisjoint(second_ids))

    def test_following_feed_only_contains_followed_authors(self):
        carol = make_user('carol')
        Follow.objects.create(follower=self.alice, following=self.bob)
        Post.objects.create(creater=self.bob, content_text='from bob')
        Post.objects.create(creater=carol, content_text='from carol')
        feed = self.api.get('/api/v1/feed/following/').json()['results']
        self.assertEqual([item['author']['username'] for item in feed], ['bob'])

    def test_feed_query_count_does_not_grow_with_post_count(self):
        def feed_query_count():
            with CaptureQueriesContext(connection) as queries:
                self.api.get('/api/v1/posts/')
            return len(queries)

        Post.objects.create(creater=self.bob, content_text='one')
        few = feed_query_count()
        for index in range(8):
            Post.objects.create(creater=self.bob, content_text=f'extra {index}')
        many = feed_query_count()
        self.assertEqual(few, many)

    def test_posts_can_be_filtered_by_author(self):
        Post.objects.create(creater=self.bob, content_text='bob post')
        Post.objects.create(creater=self.alice, content_text='alice post')
        results = self.api.get('/api/v1/posts/', {'author': 'bob'}).json()['results']
        self.assertEqual([item['author']['username'] for item in results], ['bob'])
