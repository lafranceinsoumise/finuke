import uuid
from django.test import TestCase as DjangoTestCase, override_settings
from django.shortcuts import reverse

from finuke.test_utils import RedisLiteMixin

from votes.models import VoterListItem
from .actions import OPERATOR_LOGIN_SESSION_KEY, ASSISTANT_LOGIN_SESSION_KEY
from .models import BureauOperator, LoginLink, Bureau, Operation


class TestCase(RedisLiteMixin, DjangoTestCase):
    pass


@override_settings(ENABLE_ELECTRONIC_VOTE=True, ENABLE_PHYSICAL_VOTE=True, ELECTRONIC_VOTE_REQUIRE_SMS=True, ELECTRONIC_VOTE_REQUIRE_BIRTHDATE=False)
class BasicFunctionalityTestCase(TestCase):
    fixtures = ['voter_list.json']

    def setUp(self):
        super().setUp()

        self.operator = BureauOperator.objects.create(
            email="test@test.com"
        )

        self.login_link = LoginLink.objects.create(
            operator=self.operator
        )

        self.bureau = Bureau.objects.create(
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

    def test_can_login_as_assistant(self):
        res = self.client.get(reverse('assistant_login'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('assistant_login'), {'code': self.bureau.assistant_code})
        self.assertRedirects(res, reverse('vote_bureau', args=[self.bureau.pk]))

        operation = Operation.objects.get()
        details = operation.details

        self.assertEqual(operation.type, Operation.ASSISTANT_LOGIN)
        self.assertEqual(details['assistant_code'], self.bureau.assistant_code)

    def test_cannot_login_with_random_assistant_code(self):
        res = self.client.post(reverse('assistant_login'), {'code': '00000000'})
        self.assertEqual(res.status_code, 200)

    def test_cannot_open_bureau_when_not_logged_in(self):
        res = self.client.get(reverse('open_bureau'))
        self.assertEqual(res.status_code, 302)
        res = self.client.post(reverse('open_bureau'), data={'place': 'Somewhere'})
        self.assertEqual(res.status_code, 302)

    def test_can_open_bureau(self):
        session = self.client.session
        session[OPERATOR_LOGIN_SESSION_KEY] = str(self.login_link.uuid)
        session.save()
        res = self.client.get(reverse('open_bureau'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('open_bureau'), data={'place': 'Somewhere'})

        self.assertEqual(Bureau.objects.count(), 2)
        bureau = Bureau.objects.order_by('-start_time').first()

        self.assertRedirects(res, reverse('detail_bureau', args=[bureau.pk]))

        operation = Operation.objects.get()
        details = operation.details

        self.assertEqual(operation.type, Operation.START_BUREAU)
        self.assertEqual(details['operator'], self.operator.id)
        self.assertEqual(details['link_uuid'], str(self.login_link.uuid))
        self.assertEqual(details['bureau'], bureau.id)

    def test_cannot_close_bureau_when_not_logged_in(self):
        res = self.client.get(reverse('close_bureau', args=[self.bureau.pk]))
        self.assertEqual(res.status_code, 302)

        res = self.client.post(reverse('close_bureau', args=[self.bureau.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res['location'][:2], '/?')

    def test_can_close_bureau(self):
        session = self.client.session
        session[OPERATOR_LOGIN_SESSION_KEY] = str(self.login_link.uuid)
        session.save()
        res = self.client.get(reverse('close_bureau', args=[self.bureau.pk]))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('close_bureau', args=[self.bureau.pk]))
        self.assertRedirects(res, reverse('list_bureaux'))

        operation = Operation.objects.get()
        details = operation.details

        self.assertEqual(operation.type, Operation.END_BUREAU)
        self.assertEqual(details['operator'], self.operator.id)
        self.assertEqual(details['link_uuid'], str(self.login_link.uuid))
        self.assertEqual(details['bureau'], self.bureau.id)

    def test_cannot_see_voting_view_when_unlogged(self):
        res = self.client.get(reverse('vote_bureau', args=[self.bureau.pk]))
        self.assertEqual(res.status_code, 302)

    def test_can_mark_someone_as_voting_as_operator(self):
        voter = VoterListItem.objects.order_by('?').first()
        session = self.client.session
        session[OPERATOR_LOGIN_SESSION_KEY] = str(self.login_link.uuid)
        session.save()

        res = self.client.get(reverse('vote_bureau', args=[self.bureau.pk]))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('vote_bureau', args=[self.bureau.pk]), data={'persons': [voter.pk]})
        self.assertRedirects(res, reverse('vote_bureau', args=[self.bureau.pk]))

        voter.refresh_from_db()

        self.assertEqual(voter.vote_status, VoterListItem.VOTE_STATUS_PHYSICAL)
        self.assertEqual(voter.vote_bureau, self.bureau)

        operation = Operation.objects.get()
        details = operation.details

        self.assertEqual(operation.type, Operation.PERSON_VOTE)
        self.assertEqual(details['operator'], self.operator.id)
        self.assertEqual(details['link_uuid'], str(self.login_link.uuid))
        self.assertEqual(details['bureau'], self.bureau.id)
        self.assertEqual(details['voter_list_item'], voter.id)

    def test_can_mark_someone_as_voting_as_assistant(self):
        voter = VoterListItem.objects.order_by('?').first()
        session = self.client.session
        session[ASSISTANT_LOGIN_SESSION_KEY] = self.bureau.assistant_code
        session.save()

        res = self.client.get(reverse('vote_bureau', args=[self.bureau.pk]))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('vote_bureau', args=[self.bureau.pk]), data={'persons': [voter.pk]})
        self.assertRedirects(res, reverse('vote_bureau', args=[self.bureau.pk]))

        voter.refresh_from_db()

        self.assertEqual(voter.vote_status, VoterListItem.VOTE_STATUS_PHYSICAL)
        self.assertEqual(voter.vote_bureau, self.bureau)

        operation = Operation.objects.get()
        details = operation.details

        self.assertEqual(operation.type, Operation.PERSON_VOTE)
        self.assertEqual(details['assistant_code'], self.bureau.assistant_code)
        self.assertEqual(details['bureau'], self.bureau.id)
        self.assertEqual(details['voter_list_item'], voter.id)
