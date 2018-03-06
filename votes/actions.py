from django.db import transaction, DatabaseError

from .models import VoterListItem, Vote
from phones.models import PhoneNumber


class AlreadyVotedException(Exception):
    pass


def check_voter_list_item(voter_list_id, vote_type):
    voter_list = VoterListItem.objects.select_for_update().get(pk=voter_list_id)
    if voter_list.vote_status != VoterListItem.VOTE_STATUS_NONE:
        raise AlreadyVotedException()

    voter_list.vote_status = vote_type
    voter_list.save()


def check_phone_number_status(phone_number):
    phone_number = PhoneNumber.objects.select_for_update().get(phone_number=phone_number)

    if phone_number.validated:
        raise AlreadyVotedException()

    phone_number.validated = True
    phone_number.save()


def make_online_vote(phone_number, voter_list_id, vote):
    try:
        with transaction.atomic():
            check_voter_list_item(voter_list_id, VoterListItem.VOTE_STATUS_ONLINE)
            check_phone_number_status(phone_number)
            Vote.objects.create(vote=vote)

    except DatabaseError:
        raise AlreadyVotedException()


def make_physical_vote(voter_list_id, vote):
    try:
        with transaction.atomic():
            check_voter_list_item(voter_list_id, VoterListItem.VOTE_STATUS_PHYSICAL)
            Vote.objects.create(vote=vote)
    except DatabaseError:
        AlreadyVotedException()
