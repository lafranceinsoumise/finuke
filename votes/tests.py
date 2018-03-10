from django.test import TestCase
from django.urls import reverse

from bureaux.models import Bureau, BureauOperator
from phones.models import PhoneNumber

from .models import VoterListItem, Vote
from .actions import make_online_vote, make_physical_vote, AlreadyVotedException


class VoteActionsTestCase(TestCase):
    fixtures = ['voter_list']

    def setUp(self):
        self.phone1 = PhoneNumber.objects.create(phone_number='+33612345678')
        self.phone2 = PhoneNumber.objects.create(phone_number='+33712345678')
        self.identity1 = VoterListItem.objects.all()[0]
        self.identity2 = VoterListItem.objects.all()[1]
        self.operator = BureauOperator.objects.create(email="operator@example.com")
        self.bureau = Bureau.objects.create(place="In the database", operator=self.operator)

    def test_can_only_vote_once_with_phone_number(self):
        make_online_vote(str(self.phone1.phone_number), self.identity1.id, Vote.YES)

        with self.assertRaises(AlreadyVotedException):
            make_online_vote(str(self.phone1.phone_number), self.identity2.id, Vote.NO)

    def test_can_only_vote_once_online_with_identity(self):
        make_online_vote(str(self.phone1.phone_number), self.identity1.id, Vote.YES)

        with self.assertRaises(AlreadyVotedException):
            make_online_vote(str(self.phone2.phone_number), self.identity1.id, Vote.NO)

    def test_cannot_vote_physically_twice(self):
        make_physical_vote(self.identity1.id, self.bureau)

        with self.assertRaises(AlreadyVotedException):
            make_physical_vote(self.identity1.id, self.bureau)

    def test_cannot_vote_physically_when_already_voted_online(self):
        make_online_vote(str(self.phone1.phone_number), self.identity1.id, Vote.YES)

        with self.assertRaises(AlreadyVotedException):
            make_physical_vote(self.identity1.id, self.bureau)

    def test_cannot_vote_online_when_already_voted_physically(self):
        make_physical_vote(self.identity1.id, self.bureau)

        with self.assertRaises(AlreadyVotedException):
            make_online_vote(str(self.phone1.phone_number), self.identity1.id, Vote.YES)
