from django.test import override_settings

from main.models import Follow, Post

from .base import ApiTestCase, make_user


def feed_page(api, before=None):
    params = {'before': before} if before else {}
    return api.get('/api/v1/feed/following/', params).json()


@override_settings(FEED_CELEBRITY_FOLLOWERS=2)
class FollowingFeedTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.viewer = make_user('viewer')
        self.regular = make_user('regular')
        self.celebrity = make_user('celebrity')
        # Three followers pushes the celebrity over the threshold of two.
        for name in ('fan1', 'fan2', 'fan3'):
            Follow.objects.create(follower=make_user(name), following=self.celebrity)
        Follow.objects.create(follower=self.viewer, following=self.regular)
        Follow.objects.create(follower=self.viewer, following=self.celebrity)
        self.api.force_authenticate(self.viewer)

    def test_pages_merge_fanned_and_celebrity_posts_without_gaps_or_repeats(self):
        expected = []
        for index in range(25):
            author = self.celebrity if index % 3 == 0 else self.regular
            expected.append(Post.objects.create(creater=author, content_text=f'post {index}').id)
        expected.sort(reverse=True)

        seen, before = [], None
        for _ in range(5):
            page = feed_page(self.api, before)
            seen.extend(item['id'] for item in page['results'])
            if not page['next']:
                break
            before = page['next'].split('before=')[1]

        self.assertEqual(seen, expected)
        self.assertEqual(len(seen), len(set(seen)))

    def test_unfollowing_hides_posts_immediately(self):
        post = Post.objects.create(creater=self.regular, content_text='soon hidden')
        self.assertIn(post.id, [item['id'] for item in feed_page(self.api)['results']])

        self.api.delete('/api/v1/users/regular/follow/')
        self.assertNotIn(post.id, [item['id'] for item in feed_page(self.api)['results']])

    def test_deleted_posts_do_not_appear(self):
        post = Post.objects.create(creater=self.regular, content_text='to delete')
        post.delete()
        self.assertEqual(feed_page(self.api)['results'], [])

    def test_following_someone_backfills_their_recent_posts(self):
        newcomer = make_user('newcomer')
        older = Post.objects.create(creater=newcomer, content_text='before I followed')
        feed_page(self.api)  # builds the viewer's feed index
        self.api.post('/api/v1/users/newcomer/follow/')
        self.assertIn(older.id, [item['id'] for item in feed_page(self.api)['results']])

    def test_feed_is_empty_for_a_user_following_nobody(self):
        lonely = make_user('lonely')
        self.api.force_authenticate(lonely)
        self.assertEqual(feed_page(self.api)['results'], [])
