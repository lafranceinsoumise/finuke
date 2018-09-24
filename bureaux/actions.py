from django.db import transaction, DatabaseError
from django.utils import timezone
from django.core.exceptions import ValidationError

from prometheus_client import Counter

from finuke.exceptions import RateLimitedException
from token_bucket import TokenBucket
from votes.actions import check_voter_list_item, AlreadyVotedException, participation_counter
from votes.models import VoterListItem

from . import models

OPERATOR_LOGIN_SESSION_KEY = 'login_uuid'
ASSISTANT_LOGIN_SESSION_KEY = 'assistant_code'
HOMONYMS_CHOICES_KEY = '_homonyms_choice_key'

OpenBureauTokenBucket = TokenBucket('OpenBureau', 20, 3600)
LoginAssistantTokenBucket = TokenBucket('LoginAssistant', 50, 60)
LoginAssistantIPTokenBucket = TokenBucket('LoginAssistant', 100, 60)

operator_login_counter = Counter('finuke_operator_auths_total', 'The number of operator auth trials', ['result'])
assistant_login_counter = Counter('finuke_assistant_auths_total', 'The number of assistant auth trials', ['result'])
marked_as_voted_counter = Counter('finuke_marked_as_voted_total', 'The number of persons marked as votes by an assistant')
bureaux_opened_counter = Counter('finuke_bureaux_opened_total', 'The number of bureaux openings')
bureaux_closed_counter = Counter('finuke_bureaux_closed_total', 'The number of bureaux closings')
bureaux_results_submitted = Counter('finuke_bureaux_results_total', 'The number of bureaux for which results have been submitted')


def request_to_json(request):
    return {
        'ip': request.META['REMOTE_ADDR'],
        'operator': request.operator.id if getattr(request, 'operator', False) else None,
        'link_uuid': request.session.get(OPERATOR_LOGIN_SESSION_KEY, None),
        'assistant_code': request.session.get(ASSISTANT_LOGIN_SESSION_KEY, None),
    }


def authenticate_operator(uuid):
    try:
        login_link = models.LoginLink.objects.select_related('operator').get(uuid=uuid, valid=True)
        operator_login_counter.labels('success').inc()
        return login_link
    except (models.LoginLink.DoesNotExist, ValidationError):
        operator_login_counter.labels('failure').inc()
        return None


def login_operator(request, login_link):
    models.Operation.objects.create(
        type=models.Operation.OPERATOR_LOGIN,
        details={**request_to_json(request), 'login_link': str(login_link.uuid), 'operator': login_link.operator.email},
    )
    request.session[OPERATOR_LOGIN_SESSION_KEY] = str(login_link.uuid)
    return True


def authenticate_assistant(request, code):
    try:
        bureau =  models.Bureau.objects.get(assistant_code=code)
    except models.Bureau.DoesNotExist:
        assistant_login_counter.labels('failure').inc()
        return None

    if not LoginAssistantIPTokenBucket.has_tokens(request.META['REMOTE_ADDR']):
        assistant_login_counter.labels('ip_limited').inc()
        raise RateLimitedException("Trop d'assesseur⋅e⋅s connecté⋅e⋅s")
    if not LoginAssistantTokenBucket.has_tokens(bureau):
        assistant_login_counter.labels('bureau_limited').inc()
        raise RateLimitedException("Trop d'assesseur⋅e⋅s connecté⋅e⋅s")

    assistant_login_counter.labels('success').inc()
    return bureau


def login_assistant(request, bureau):
    request.session[ASSISTANT_LOGIN_SESSION_KEY] = bureau.assistant_code

    models.Operation.objects.create(
        type=models.Operation.ASSISTANT_LOGIN,
        details={**request_to_json(request), 'bureau': bureau.pk, 'assistant_code': bureau.assistant_code}
    )


def open_bureau(request, place):
    if not OpenBureauTokenBucket.has_tokens(request.operator):
        raise RateLimitedException("Trop de bureaux ouverts.")
    with transaction.atomic():
        bureau = models.Bureau.objects.create(
            place=place,
            operator=request.operator
        )

        models.Operation.objects.create(
            type=models.Operation.START_BUREAU,
            details={**request_to_json(request), 'bureau': bureau.id}
        )

    bureaux_opened_counter.inc()

    return bureau


def close_bureau(request, bureau):
    if bureau.end_time is not None:
        raise ValueError('Bureau déjà fermé')
    with transaction.atomic():
        bureau.end_time = timezone.now()
        bureau.save()

        models.Operation.objects.create(
            type=models.Operation.END_BUREAU,
            details={**request_to_json(request), 'bureau': bureau.id}
        )

    bureaux_closed_counter.inc()


def mark_as_voted(request, voter_list_id, bureau):
    try:
        with transaction.atomic():
            models.Operation.objects.create(
                type=models.Operation.PERSON_VOTE,
                details={**request_to_json(request), 'voter_list_item': voter_list_id, 'bureau': bureau.id}
            )
            check_voter_list_item(voter_list_id, VoterListItem.VOTE_STATUS_PHYSICAL, bureau)

        participation_counter.incr()
        marked_as_voted_counter.inc()
    except DatabaseError:
        AlreadyVotedException()
