from django.test import TestCase as DjangoTestCase
from django.test.runner import DiscoverRunner
import redislite
from bs4 import BeautifulSoup

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


class TestCase(RedisLiteMixin, DjangoTestCase):
    def assertFormFieldHasError(self, response, fieldname, reason=None):
        if reason is None:
            reason = f"No error found in form for field '{fieldname}'"

        soup = BeautifulSoup(response.content, 'html.parser')

        self.assertTrue('has-error' in soup.select(f'#div_id_{fieldname}')[0].attrs['class'], reason)
