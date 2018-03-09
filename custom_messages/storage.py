from django.contrib.messages.storage.base import BaseStorage, Message
from django.contrib.messages.storage.fallback import FallbackStorage
from django.shortcuts import reverse

from . import SESSION_KEY
from .models import PersistantMessage


class PersistantMessageWrapper(Message):
    def __init__(self, message_model):
        super().__init__(message_model.level, message_model.text)
        self.closing_link = reverse('mark_as_read', args=[message_model.id])


class CustomStorage(BaseStorage):
    storage_class = FallbackStorage

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        self.storage = self.storage_class(request, *args, **kwargs)

    def _get(self, *args, **kwargs):
        return self.storage._get(*args, **kwargs)

    def _store(self, messages, response, *args, **kwargs):
        self.storage._store(messages, response, *args, **kwargs)

    @property
    def _other_messages(self):
        # show only to connected people
        if not ('login_uuid' in self.request.session or 'assistant_code' in self.request.session):
            return []
        if not hasattr(self, '_other_messages_data'):
            seen_messages = self.request.session.get(SESSION_KEY, [])
            global_messages = PersistantMessage.objects.filter(enabled=True)
            self._other_messages_data = [PersistantMessageWrapper(m) for m in global_messages if m.pk not in seen_messages]
        return self._other_messages_data

    def __len__(self):
        return super().__len__() + len(self._other_messages)

    def __iter__(self):
        yield from self._other_messages
        yield from super().__iter__()

    def __contains__(self, item):
        super().__contains__(item) or item in self._other_messages
