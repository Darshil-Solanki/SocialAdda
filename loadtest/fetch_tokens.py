"""Writes access tokens for the demo users to a JSON file, for loadtest/locustfile.py (LOAD_TOKENS).

    python loadtest/fetch_tokens.py --host http://localhost:8000 --users 150 --out tokens.json
"""
import argparse
import json

import requests

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='http://localhost:8000')
parser.add_argument('--users', type=int, default=12)
parser.add_argument('--password', default='demo-pass-123')
parser.add_argument('--out', default='tokens.json')
args = parser.parse_args()

tokens = []
for index in range(1, args.users + 1):
    response = requests.post(
        f'{args.host}/api/v1/auth/token/',
        json={'username': f'demo{index}', 'password': args.password},
        timeout=30,
    )
    response.raise_for_status()
    tokens.append(response.json()['access'])

with open(args.out, 'w') as handle:
    json.dump(tokens, handle)
print(f'wrote {len(tokens)} tokens to {args.out}')
