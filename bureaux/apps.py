from django.apps import AppConfig


class BureauxConfig(AppConfig):
    name = 'bureaux'

    def ready(self):
        from . import signals
