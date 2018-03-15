from django.db import transaction, DatabaseError
from functools import wraps

from prometheus_client import Counter

from token_bucket import TokenBucket
from .models import VoterListItem, FEVoterListItem, Vote
from phones.models import PhoneNumber

VoteIPTokenBucket = TokenBucket('VoteIP', 10, 60)

online_vote_counter = Counter('finuke_online_votes_total', 'Number of online votes')
fe_vote_counter = Counter('finuke_fe_votes_total', 'Number of FE votes')


class VoteLimitException(Exception):
    pass


class AlreadyVotedException(Exception):
    pass


class VoterState:
    PHONE_NUMBER_KEY = 'phone_number'
    PHONE_NUMBER_VALID_KEY = 'phone_valid'
    VOTER_ID_KEY = 'list_voter'
    IS_FOREIGN_FRENCH = 'list_voter_type'
    SESSIONS_KEY = [PHONE_NUMBER_KEY, PHONE_NUMBER_VALID_KEY, VOTER_ID_KEY, IS_FOREIGN_FRENCH]

    def __init__(self, request):
        self._request = request
        self._cache = {}

    def clean_session(self):
        for key in self.SESSIONS_KEY:
            if key in self._request.session:
                del self._request.session[key]

        # reset cache
        self._cache = {}

    @property
    def phone_number(self):
        if self.PHONE_NUMBER_KEY not in self._request.session or self.is_foreign_french:
            return None

        if 'phone_number' not in self._cache:
            try:
                self._cache['phone_number'] = PhoneNumber.objects.get(phone_number=self._request.session[self.PHONE_NUMBER_KEY])
            except PhoneNumber.DoesNotExist:
                self._cache['phone_number'] = None

        return self._cache['phone_number']

    @phone_number.setter
    def phone_number(self, value):
        self._request.session[self.PHONE_NUMBER_KEY] = str(value.phone_number)
        self._request.session[self.PHONE_NUMBER_VALID_KEY] = False
        self._cache['phone_number'] = value

    @property
    def is_phone_valid(self):
        return self.phone_number is not None and bool(self._request.session.get(self.PHONE_NUMBER_VALID_KEY))

    @is_phone_valid.setter
    def is_phone_valid(self, value):
        self._request.session[self.PHONE_NUMBER_VALID_KEY] = value

    @property
    def is_foreign_french(self):
        return self._request.session.get(self.IS_FOREIGN_FRENCH, False)

    @is_foreign_french.setter
    def is_foreign_french(self, value):
        self._request.session[self.IS_FOREIGN_FRENCH] = value

    @property
    def voter(self):
        if self.VOTER_ID_KEY not in self._request.session:
            return None
        if 'voter' not in self._cache:
            model = FEVoterListItem if self.is_foreign_french else VoterListItem
            try:
                self._cache['voter'] = model.objects.get(pk=self._request.session[self.VOTER_ID_KEY])
            except model.DoesNotExist:
                self._cache['voter'] = None

        return self._cache['voter']

    @voter.setter
    def voter(self, value):
        self._cache['voter'] = value
        self._request.session[self.VOTER_ID_KEY] = value.pk
        self._request.session[self.IS_FOREIGN_FRENCH] = value.__class__ is FEVoterListItem


def check_voter_list_item(voter_list_id, vote_type, bureau=None):
    voter_list = VoterListItem.objects.select_for_update().get(pk=voter_list_id)
    if voter_list.vote_status != VoterListItem.VOTE_STATUS_NONE:
        raise AlreadyVotedException()

    voter_list.vote_status = vote_type
    if bureau is not None:
        voter_list.vote_bureau = bureau
    voter_list.save()

    return voter_list


def check_fe_voter_list_item(fe_voter_list_id):
    fe_voter_list = FEVoterListItem.objects.select_for_update().get(pk=fe_voter_list_id)
    if fe_voter_list.has_voted:
        raise AlreadyVotedException()

    fe_voter_list.has_voted = True
    fe_voter_list.save()

    return fe_voter_list


def check_phone_number_status(phone_number, voter=None):
    phone_number = PhoneNumber.objects.select_for_update().get(phone_number=phone_number)

    if phone_number.validated:
        raise AlreadyVotedException()

    if voter is not None:
        phone_number.voter = voter

    phone_number.validated = True
    phone_number.save()

    return phone_number


def make_online_vote(ip, phone_number, voter, is_foreign_french, vote):
    if not VoteIPTokenBucket.has_tokens(ip):
        raise VoteLimitException("Trop de votes sur cette IP.")

    try:
        with transaction.atomic():
            if voter is not None:
                if is_foreign_french:
                    check_fe_voter_list_item(voter.pk)
                    fe_vote_counter.inc()
                else:
                    check_voter_list_item(voter.pk, VoterListItem.VOTE_STATUS_ONLINE)

            if phone_number is not None:
                check_phone_number_status(phone_number.phone_number, voter=voter)

            vote = Vote.objects.create(vote=vote, with_list=voter is not None)

    except DatabaseError:
        raise AlreadyVotedException()

    online_vote_counter.inc()
    return vote.id
