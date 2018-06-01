from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BureauOperator, LoginLink


@receiver(post_save, sender=BureauOperator, dispatch_uid="ensure_operator_has_link")
def ensure_operator_has_link(sender, instance, raw, created, **kwargs):
    if not raw and (created or not instance.login_links.exists()):
        LoginLink.objects.create(
            operator=instance
        )
