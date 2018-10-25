from django.conf import settings
from django.db import DatabaseError, transaction
from elasticsearch import Elasticsearch, NotFoundError

from phonenumber_field.phonenumber import PhoneNumber
from prometheus_client import Counter

from finuke.redis import RedisCounter
from token_bucket import TokenBucket
from .models import VoterListItem, FEVoterListItem, Vote, VoterInformation
from phones.models import PhoneNumber

VoteIPTokenBucket = TokenBucket('VoteIP', 10, 60)

online_vote_counter = Counter('finuke_online_votes_total', 'Number of online votes')
fe_vote_counter = Counter('finuke_fe_votes_total', 'Number of FE votes')


class VoteLimitException(Exception):
    pass


class AlreadyVotedException(Exception):
    pass


participation_counter = RedisCounter('participation')


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
        if self.phone_number is None:
            return False
        if self.phone_number.validated:
            return False

        return self.phone_number is not None and bool(self._request.session.get(self.PHONE_NUMBER_VALID_KEY))

    @is_phone_valid.setter
    def is_phone_valid(self, value):
        self._request.session[self.PHONE_NUMBER_VALID_KEY] = value

    @property
    def can_see_list(self):
        if not settings.ELECTRONIC_VOTE_REQUIRE_SMS:
            return True

        return self.is_phone_valid

    @property
    def can_vote(self):
        return self.is_foreign_french or \
               (self.can_see_list and
                (not settings.ELECTRONIC_VOTE_REQUIRE_LIST or
                 (self.voter and self.voter.vote_status == VoterListItem.VOTE_STATUS_NONE)))

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


def make_online_validation(*, ip, phone_number=None, voter=None, is_foreign_french=False, vote, contact_information=None):
    """Make an online vote

    This procedure must be executed inside an atomic transaction

    :param ip: the ip of the client trying to vote
    :param phone_number: the phone number used to validate the vote (can be None if not phone number validation)
    :param voter: the voter model instance
    :param is_foreign_french: is the voter in the foreign French list ?
    :param vote: the vote choice
    :return:
    """
    if not VoteIPTokenBucket.has_tokens(ip):
        raise VoteLimitException("Trop de votes sur cette IP.")

    vote_id = None
    contact_information_id = None

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

            if settings.ENABLE_VOTING:
                vote_id = Vote.objects.create(vote=vote, with_list=voter is not None).pk

            if settings.ENABLE_CONTACT_INFORMATION:
                contact_information_id = VoterInformation.objects.create(
                    voter=voter,
                    **{
                        'phone' if isinstance(contact_information, PhoneNumber) else 'email': contact_information
                    }
                ).pk

    except DatabaseError:
        raise AlreadyVotedException()

    if settings.ELASTICSEARCH_ENABLED and settings.ENABLE_HIDING_VOTERS:
        deindex_voter(voter.id)

    participation_counter.incr()
    online_vote_counter.inc()

    return vote_id, contact_information_id


def deindex_voter(voter_id):
    es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])
    try:
        es.delete('voters', 'voter', voter_id)
    except NotFoundError:
        pass


def save_contact_information(voter, contact_information):
    return VoterInformation.objects.create(
        voter=voter,
        **{
            'phone' if isinstance(contact_information, PhoneNumber) else 'email': contact_information
        }
    )
