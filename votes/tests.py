from django.test import RequestFactory
from django.shortcuts import reverse

from bs4 import BeautifulSoup

from finuke.test_utils import TestCase

from bureaux.models import Bureau, BureauOperator
from phones.models import PhoneNumber
from bureaux.actions import mark_as_voted

from .models import VoterListItem, Vote
from .actions import make_online_vote, AlreadyVotedException

class VoteActionsTestCase(TestCase):
    fixtures = ['voter_list']

    def setUp(self):
        super().setUp()
        self.phone1 = PhoneNumber.objects.create(phone_number='+33612345678')
        self.phone2 = PhoneNumber.objects.create(phone_number='+33712345678')
        self.identity1 = VoterListItem.objects.all()[0]
        self.identity2 = VoterListItem.objects.all()[1]
        self.operator = BureauOperator.objects.create(email="operator@example.com")
        self.bureau = Bureau.objects.create(place="In the database", operator=self.operator)

    def test_can_only_vote_once_with_phone_number(self):
        make_online_vote('randomip', str(self.phone1.phone_number), self.identity1.id, Vote.YES)

        with self.assertRaises(AlreadyVotedException):
            make_online_vote('randomip', str(self.phone1.phone_number), self.identity2.id, Vote.NO)

    def test_can_only_vote_once_online_with_identity(self):
        make_online_vote('randomip', str(self.phone1.phone_number), self.identity1.id, Vote.YES)

        with self.assertRaises(AlreadyVotedException):
            make_online_vote('randomip', str(self.phone2.phone_number), self.identity1.id, Vote.NO)

    def test_cannot_vote_physically_twice(self):
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.session = {}

        mark_as_voted(request, self.identity1.id, self.bureau)

        with self.assertRaises(AlreadyVotedException):
            mark_as_voted(request, self.identity1.id, self.bureau)

    def test_cannot_vote_physically_when_already_voted_online(self):
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.session = {}

        make_online_vote('randomip', str(self.phone1.phone_number), self.identity1.id, Vote.YES)

        with self.assertRaises(AlreadyVotedException):
            mark_as_voted(request, self.identity1.id, self.bureau)

    def test_cannot_vote_online_when_already_voted_physically(self):
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.session = {}

        mark_as_voted(request, self.identity1.id, self.bureau)

        with self.assertRaises(AlreadyVotedException):
            make_online_vote('randomip', str(self.phone1.phone_number), self.identity1.id, Vote.YES)


class VotesRoutesTestCase(TestCase):
    def setUp(self):
        super().setUp()

    def test_can_enter_phone_number(self):
        res = self.client.get(reverse('validate_phone_number'))
        self.assertEqual(res.status_code, 200)

        content = BeautifulSoup(res.content, "html.parser")

        self.assertTrue(content.select('input[name="phone_number"]'))

        res = self.client.post(reverse('validate_phone_number'), {'phone_number': '06 45 78 98 45'})
        self.assertRedirects(res, reverse('validate_code'))

    def test_allowed_phone_numbers(self):
        url = reverse('validate_phone_number')

        for number in [
            '+33 6 38 64 58 78',  # phone number in international format
            '06 54 12 36 87',  # phone number in national format
            '06 90 48 78 45',  # phone number for guadeloupe in national format
            '+590 6 90 54 12 54',  # phone number for guadeloupe in international format

        ]:
            res = self.client.post(url, {'phone_number': number})
            self.assertRedirects(res, reverse('validate_code'))

    def test_disallowed_phone_numbers(self):
        url = reverse('validate_phone_number')

        for number in [
            '+44 20 7323 8299',  # phone number from another country (in this case British Museum
            '+33 6 45 78',  # obviously incorrect phone number
            '06 54 12 36 78 78',  # another obviously incorrect
            '01 42 78 95 87 45',  # a landline number
            '05 90 48 78 45',  # phone number for guadeloupe in national format but landline
            '+590 5 90 54 12 54',  # landline number in guadeloupe in international format
        ]:
            res = self.client.post(url, {'phone_number': number})
            self.assertEqual(res.status_code, 200)
            self.assertFormFieldHasError(res, 'phone_number', f'Should be an error with number {number}.')
