"""
Home-feed storage (hybrid fan-out).

Ordinary authors are fanned out on write: each new post id is added to the sorted set of every follower.
Celebrity authors (more followers than FEED_CELEBRITY_FOLLOWERS) are not fanned out. Their posts are
read from the database at feed time and merged in. The Redis set `feed:celebrities` remembers which
authors took that path, so a follower-count change later does not drop or duplicate posts.

The sorted sets are only an index: every candidate is re-checked against the viewer's current follows
and the database, so unfollowed or deleted posts never appear.
"""
import redis
from django.conf import settings

from .models import Follow, Post

CELEBRITY_SET = 'feed:celebrities'
BACKFILL_ON_FOLLOW = 100

_client = None


def get_feed_client():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.FEED_REDIS_URL, decode_responses=True)
    return _client


def _feed_key(user_id):
    return f'feed:{user_id}'


def _built_key(user_id):
    return f'feed:{user_id}:built'


def _follower_count(author_id):
    return Follow.objects.filter(following_id=author_id).count()


def _is_celebrity(client, author_id):
    return client.sismember(CELEBRITY_SET, author_id)


def fan_out_post(post):
    """Writes a new post into follower feeds, or marks the author as a celebrity and skips fan-out."""
    client = get_feed_client()
    if _is_celebrity(client, post.creater_id) or _follower_count(post.creater_id) > settings.FEED_CELEBRITY_FOLLOWERS:
        client.sadd(CELEBRITY_SET, post.creater_id)
        return 0

    follower_ids = list(Follow.objects.filter(following_id=post.creater_id).values_list('follower_id', flat=True))
    pipe = client.pipeline()
    for follower_id in follower_ids:
        key = _feed_key(follower_id)
        pipe.zadd(key, {post.id: post.id})
        pipe.zremrangebyrank(key, 0, -(settings.FEED_MAX_ITEMS + 1))
    pipe.execute()
    return len(follower_ids)


def on_follow(follower, following):
    """When a feed exists, copy the new followee's recent posts into it (synchronous, so the feed updates at once)."""
    client = get_feed_client()
    if not client.exists(_built_key(follower.id)) or _is_celebrity(client, following.id):
        return
    recent = Post.objects.filter(creater_id=following.id).order_by('-id').values_list('id', flat=True)[:BACKFILL_ON_FOLLOW]
    ids = list(recent)
    if ids:
        client.zadd(_feed_key(follower.id), {post_id: post_id for post_id in ids})


def _ensure_built(client, user, regular_ids):
    if client.exists(_built_key(user.id)):
        return
    if regular_ids:
        recent = Post.objects.filter(creater_id__in=regular_ids).order_by('-id').values_list('id', flat=True)
        ids = list(recent[:settings.FEED_MAX_ITEMS])
        if ids:
            client.zadd(_feed_key(user.id), {post_id: post_id for post_id in ids})
    client.set(_built_key(user.id), '1')


def _fanned_candidates(client, user_id, regular_ids, before, limit):
    """Reads feed-index chunks until enough posts from ordinary authors are found, or the index runs out."""
    found = []
    upper = f'({before}' if before else '+inf'
    chunk_size = max(limit * 3, 30)
    while len(found) < limit:
        chunk = client.zrevrangebyscore(_feed_key(user_id), upper, '-inf', start=0, num=chunk_size)
        if not chunk:
            break
        ids = [int(item) for item in chunk]
        found.extend(Post.objects.filter(id__in=ids, creater_id__in=regular_ids).values_list('id', flat=True))
        if len(chunk) < chunk_size:
            break
        upper = f'({ids[-1]}'
    return found


def following_page_ids(user, before=None, limit=10):
    """Post ids for one page of the following feed, newest first. `before` is an exclusive cursor."""
    client = get_feed_client()
    followed = set(Follow.objects.filter(follower=user).values_list('following_id', flat=True))
    if not followed:
        return []

    celebrity_ids = {int(item) for item in client.smembers(CELEBRITY_SET)} & followed
    regular_ids = followed - celebrity_ids
    _ensure_built(client, user, regular_ids)

    candidates = _fanned_candidates(client, user.id, regular_ids, before, limit) if regular_ids else []
    if celebrity_ids:
        celebrity_posts = Post.objects.filter(creater_id__in=celebrity_ids)
        if before:
            celebrity_posts = celebrity_posts.filter(id__lt=before)
        candidates += list(celebrity_posts.order_by('-id').values_list('id', flat=True)[:limit])
    return sorted(set(candidates), reverse=True)[:limit]
