from django.conf import settings


def votation_name(request):
    return {
        'VOTATION_NAME': settings.VOTATION_NAME,
    }
