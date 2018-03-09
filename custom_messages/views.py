from django.http import JsonResponse

from . import SESSION_KEY
from .models import PersistantMessage


def mark_as_read(request, pk):
    pk = int(pk)
    seen_messages = request.session.get(SESSION_KEY, [])
    if pk not in seen_messages:
        seen_messages.append(pk)
        messages = {i[0] for i in PersistantMessage.objects.values_list('pk')}
        request.session[SESSION_KEY] = sorted(pk for pk in seen_messages if pk in messages)

    return JsonResponse({'status': 'ok'})
