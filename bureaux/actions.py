from django.db import transaction, DatabaseError
from django.utils import timezone
from django.core.exceptions import ValidationError

from token_bucket import TokenBucket
from votes.actions import check_voter_list_item, AlreadyVotedException
from votes.models import VoterListItem

from . import models

OpenBureauTokenBucket = TokenBucket('OpenBureau', 20, 3600)


class BureauException(Exception):
    pass


def request_to_json(request):
    return {
        'ip': request.META['REMOTE_ADDR'],
        'operator': request.operator.id if getattr(request, 'operator', False) else None,
        'link_uuid': request.session.get('link_uuid', None),
    }


def authenticate_operator(uuid):
    try:
        return models.LoginLink.objects.select_related('operator').get(uuid=uuid, valid=True)
    except (models.LoginLink.DoesNotExist, ValidationError):
        return None


def login_operator(request, login_link):
    models.Operation.objects.create(
        type=models.Operation.OPERATOR_LOGIN,
        details={**request_to_json(request), 'login_link': str(login_link.uuid), 'operator': login_link.operator.email},
    )
    request.session['login_uuid'] = str(login_link.uuid)
    return True


def login_assistant(request, bureau):
    request.session['assistant_code'] = bureau.assistant_code
    models.Operation.objects.create(
        type=models.Operation.ASSISTANT_LOGIN,
        details={**request_to_json(request), 'bureau': bureau.pk, 'assistant_code': bureau.assistant_code}
    )


def open_bureau(request, place):
    if not OpenBureauTokenBucket.has_tokens(request.operator):
        raise BureauException("Trop de bureaux ouverts.")
    with transaction.atomic():
        bureau = models.Bureau.objects.create(
            place=place,
            operator=request.operator
        )

        models.Operation.objects.create(
            type=models.Operation.START_BUREAU,
            details={**request_to_json(request), 'bureau': bureau.id}
        )

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


def mark_as_voted(request, voter_list_id, bureau):
    try:
        with transaction.atomic():
            models.Operation.objects.create(
                type=models.Operation.PERSON_VOTE,
                details={**request_to_json(request), 'voter_list_item': voter_list_id, 'bureau': bureau.id}
            )
            check_voter_list_item(voter_list_id, VoterListItem.VOTE_STATUS_PHYSICAL, bureau)
    except DatabaseError:
        AlreadyVotedException()
