import redis
from django.conf import settings

__all__ = ['get_redis_client']


redis_connection = redis.StrictRedis.from_url(settings.REDIS_URL)


def get_redis_client():
    return redis_connection
