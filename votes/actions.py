from django.db import transaction, DatabaseError

from .models import VoterListItem, Vote
from phones.models import PhoneNumber


class AlreadyVotedException(Exception):
    pass


def check_voter_list_item(voter_list_id, vote_type, bureau=None):
    voter_list = VoterListItem.objects.select_for_update().get(pk=voter_list_id)
    if voter_list.vote_status != VoterListItem.VOTE_STATUS_NONE:
        raise AlreadyVotedException()

    voter_list.vote_status = vote_type
    if bureau is not None:
        voter_list.vote_bureau = bureau
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
            if voter_list_id is not None:
                print(voter_list_id)
                check_voter_list_item(voter_list_id, VoterListItem.VOTE_STATUS_ONLINE)
            check_phone_number_status(phone_number)
            vote = Vote.objects.create(vote=vote, with_list=voter_list_id is not None)
            return vote.id

    except DatabaseError:
        raise AlreadyVotedException()
