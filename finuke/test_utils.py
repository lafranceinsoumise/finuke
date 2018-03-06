from django.test.runner import DiscoverRunner
import redislite
from finuke import redis

class CustomRunner(DiscoverRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        former_redis_connection = redis.redis_connection
        redis.redis_connection = redislite.StrictRedis()

        super().run_tests(test_labels, extra_tests, **kwargs)

        redis.redis_connection = former_redis_connection


class RedisLiteMixin():
    def setUp(self):
        super().setUp()
        self.former_redis_connection = redis.redis_connection
        redis.redis_connection = redislite.StrictRedis()

    def tearDown(self):
        redis.redis_connection = self.former_redis_connection
