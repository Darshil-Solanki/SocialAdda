"""
Load test for the SocialAdda API.

Run against a seeded database (python manage.py seed_demo), for example:
    locust -f loadtest/locustfile.py --host http://localhost:8000 --headless -u 50 -r 10 -t 60s

Demo users are demo1..demoN with the password from seed_demo.

Logging in is CPU-heavy (password hashing), so set LOAD_TOKENS to a JSON file of pre-fetched
access tokens (see loadtest/fetch_tokens.py) to measure the API without measuring logins.
"""
import json
import os
import random

from locust import HttpUser, between, task

DEMO_USERS = int(os.environ.get('LOAD_DEMO_USERS', '12'))
DEMO_PASSWORD = 'demo-pass-123'


TOKENS_FILE = os.environ.get('LOAD_TOKENS')
TOKENS = json.load(open(TOKENS_FILE)) if TOKENS_FILE else None


class SocialUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        if TOKENS:
            access = random.choice(TOKENS)
        else:
            username = f'demo{random.randint(1, DEMO_USERS)}'
            response = self.client.post(
                '/api/v1/auth/token/',
                json={'username': username, 'password': DEMO_PASSWORD},
                name='login',
            )
            access = response.json()['access']
        self.headers = {'Authorization': f"Bearer {access}"}
        self.post_ids = [item['id'] for item in self.client.get(
            '/api/v1/posts/', headers=self.headers, name='explore-warmup').json()['results']]

    @task(6)
    def following_feed(self):
        self.client.get('/api/v1/feed/following/', headers=self.headers, name='feed following')

    @task(3)
    def explore(self):
        self.client.get('/api/v1/posts/', headers=self.headers, name='explore')

    @task(1)
    def like_and_unlike(self):
        if not self.post_ids:
            return
        post_id = random.choice(self.post_ids)
        self.client.post(f'/api/v1/posts/{post_id}/like/', headers=self.headers, name='like')
        self.client.delete(f'/api/v1/posts/{post_id}/like/', headers=self.headers, name='unlike')
