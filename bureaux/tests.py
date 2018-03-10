import uuid
from django.test import TestCase as DjangoTestCase
from django.shortcuts import reverse

from finuke.test_utils import RedisLiteMixin

from .models import BureauOperator, LoginLink, Bureau, Operation


class TestCase(RedisLiteMixin, DjangoTestCase):
    pass


class OperationLoggingTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.operator = BureauOperator.objects.create(
            email="test@test.com"
        )

        self.login_link = LoginLink.objects.create(
            operator=self.operator
        )

        self.bureau = Bureau(
            place="DTC",
            operator=self.operator
        )

    def test_cannot_login_as_operator_with_wrong_link(self):
        res = self.client.get(reverse('login', args=[uuid.uuid4()]))
        self.assertRedirects(res, reverse('login_error'))

    def test_can_login_as_operator(self):
        res = self.client.get(reverse('login', args=[self.login_link.uuid]))
        self.assertRedirects(res, reverse('list_bureaux'))

        operation = Operation.objects.get()
        details = operation.details

        self.assertEqual(operation.type, Operation.OPERATOR_LOGIN)
        self.assertEqual(details['operator'], self.operator.email)
        self.assertEqual(details['login_link'], str(self.login_link.uuid))
