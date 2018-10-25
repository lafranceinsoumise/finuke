import redis
from django.conf import settings

__all__ = ['get_redis_client']


redis_connection = redis.StrictRedis.from_url(settings.REDIS_URL)


def get_redis_client():
    return redis_connection


class RedisCounter():
    def __init__(self, name):
        self.name = name

    def get(self):
        return int(get_redis_client().get(f"counter:{self.name}") or 0)

    def incr(self):
        return get_redis_client().incr(f"counter:{self.name}")
