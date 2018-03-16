from django.core.management import BaseCommand
from django.urls import reverse
from django.core import mail
from django.db import transaction
from tqdm import tqdm
from textwrap import wrap

from ...models import UnlockingRequest


messages = {
    UnlockingRequest.STATUS_OK: "Votre demande a été acceptée. Vous pouvez de nouveau voter avec ce numéro.",
    UnlockingRequest.STATUS_KO: "Votre demande a été refusée car le nom que vous avez indiqué comme ayant voté ne "
                                "correspondait pas au nom associé au numéro. Si vous êtes certains, merci de refaire "
                                "une demande, en indiquant bien les noms de naissance des personnes concernées.",
    UnlockingRequest.STATUS_DUPLICATE: "Vous nous aviez déjà envoyé une requête pour ce numéro. Nous ne pouvons"
                                       " malheureusement"
                                       " débloquer qu'une seule fois par numéro, pour éviter les abus.",
    UnlockingRequest.STATUS_UNLISTED: "Malheureusement, la personne ayant voté avec le numéro que vous nous avez"
                                      " transmis a voté sans indiquer son identité (soit parce qu'elle n'était pas"
                                      " inscrite, soit parce qu'elle ne s'est pas trouvé). Il nous est donc impossible"
                                      " de vérifier votre requête.",
    UnlockingRequest.STATUS_UNUSED: "Le numéro que vous nous avez transmis n'a pas encore été utilisé. Il est déjà"
                                    " utilisable pour recevoir un vote. Si vous rencontrez un autre problème, utilisez"
                                    " le formulaire de contact.",
    UnlockingRequest.STATUS_INVALID_NUMBER: "Le numéro que vous nous avez indiqué n'est pas un numéro de téléphone"
                                            " mobile valide. Il n'est malheureusement possible de voter qu'avez un"
                                            " mobile français. S'il s'agit d'une faute de frappe de votre part, merci"
                                            " de faire une nouvelle demande avec le bon numéro."
}

include_link_to_form = {UnlockingRequest.STATUS_KO, UnlockingRequest.STATUS_INVALID_NUMBER}

message_template = """
Bonjour,

Vous nous avez adressé une demande de déblocage du numéro {numero}.
Vous nous aviez indiqué :

Personne souhaitant voter : {requester}
Personne ayant déjà voté : {declared_voter}

{answer}

Bien cordialement,
L'équipe du vote
""".strip()


class Command(BaseCommand):
    help = 'Traiter les demande de déblocage'

    def handle(self, *args, **options):
        status_to_include = set(messages)
        requests = UnlockingRequest.objects.filter(answer_sent=False, status__in=status_to_include)

        form_link = "https://nucleaire.vote" + reverse('unlocking_request')

        for request in tqdm(requests, desc="Traitement des requêtes"):
            answer = '\n'.join(wrap(messages[request.status]))
            if request.status in include_link_to_form:
                answer += '\n\nSuivez le lien suivant pour retourner au formulaire :\n' + form_link
            message = message_template.format(
                numero=request.phone_number.phone_number.as_international if request.phone_number else request.raw_number,
                requester=request.requester,
                declared_voter=request.declared_voter,
                answer=answer
            )

            mail.send_mail(
                subject='Votre demande de déblocage de numéro',
                message=message,
                from_email='notifications@nucleaire.vote',
                recipient_list=[request.email]
            )

            with transaction.atomic():
                request.answer_sent=True
                request.save()

                if request.status == UnlockingRequest.STATUS_OK:
                    request.phone_number.validated = False
                    request.phone_number.save()
