from main.models import Follow

from .base import ApiTestCase, make_user


class UserApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user('alice', first_name='Alice')
        self.bob = make_user('bob')
        self.api.force_authenticate(self.alice)

    def test_profile_reports_counts_and_follow_state(self):
        Follow.objects.create(follower=self.alice, following=self.bob)
        profile = self.api.get('/api/v1/users/bob/').json()
        self.assertEqual(profile['follower_count'], 1)
        self.assertTrue(profile['is_following'])

    def test_follow_and_unfollow(self):
        self.assertEqual(self.api.post('/api/v1/users/bob/follow/').status_code, 204)
        self.assertTrue(Follow.objects.filter(follower=self.alice, following=self.bob).exists())
        self.assertEqual(self.api.delete('/api/v1/users/bob/follow/').status_code, 204)
        self.assertFalse(Follow.objects.filter(follower=self.alice, following=self.bob).exists())

    def test_cannot_follow_yourself(self):
        response = self.api.post('/api/v1/users/alice/follow/')
        self.assertEqual(response.status_code, 400)

    def test_suggestions_exclude_self_and_followed_users(self):
        carol = make_user('carol')
        Follow.objects.create(follower=self.alice, following=self.bob)
        names = [user['username'] for user in self.api.get('/api/v1/users/suggestions/').json()['results']]
        self.assertEqual(names, [carol.username])

    def test_search_matches_username_and_first_name(self):
        make_user('dave', first_name='Alicia')
        names = sorted(user['username'] for user in self.api.get('/api/v1/users/', {'q': 'ali'}).json()['results'])
        self.assertEqual(names, ['dave'])
