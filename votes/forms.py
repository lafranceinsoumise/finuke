import logging
import re
from datetime import timedelta
from collections import Counter

from crispy_forms.helper import FormHelper
from crispy_forms import layout
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import Form, ModelForm, CharField, ChoiceField, ModelChoiceField, RadioSelect, DateField
from django.utils import timezone
from django.utils.html import mark_safe
from django.urls import reverse
from phonenumber_field.formfields import PhoneNumberField

from finuke.exceptions import RateLimitedException
from phones.models import PhoneNumber, SMS
from phones.sms import send_new_code, is_valid_code, SMSSendException
from votes.models import Vote, VoterListItem, UnlockingRequest

MOBILE_PHONE_RE = re.compile(r'^0[67]')

DROMS_PREFIX = {
    '639': 262,  # Mayotte
    '690': 590,  # Gadeloupe
    '691': 590,  # Gadeloupe
    '694': 594,  # Guyane
    '696': 596,  # Martinique
    '697': 596,  # Martinique
    '692': 262,  # Réunion
    '693': 262,  # Réunion
}

TOM_COUNTRY_CODES = set([687, 689, 590, 590, 508, 681])

DROMS_COUNTRY_CODES = set(DROMS_PREFIX.values())

logger = logging.getLogger('finuke.sms')


def normalize_mobile_phone(phone_number, messages):
    if phone_number.country_code == 33:
        # if french number, we verifies if it is not actually a DROM mobile number and replace country code in this case
        drom = DROMS_PREFIX.get(str(phone_number.national_number)[:3], None)
        if drom is not None:
            phone_number.country_code = drom
        # if it is not the case, we verify it is a mobile number
        elif not MOBILE_PHONE_RE.match(phone_number.as_national):
            raise ValidationError(messages['mobile_only'])

    elif phone_number.country_code in DROMS_COUNTRY_CODES:
        # if country code is one of the DROM country codes, we check that is is a valid mobile phone number
        if DROMS_PREFIX.get(str(phone_number.national_number)[:3], None) != phone_number.country_code:
            raise ValidationError(messages['mobile_only'])

    elif phone_number.country_code in TOM_COUNTRY_CODES:
        pass

    else:
        raise ValidationError(messages['french_only'])

    return phone_number


class BaseForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(layout.Submit('submit', 'Valider'))


class FindPersonInListForm(Form):
    person = ModelChoiceField(queryset=VoterListItem.objects.filter(vote_status=VoterListItem.VOTE_STATUS_NONE),
                              widget=None, error_messages={'required': "Vous n'avez pas sélectionné de nom dans la liste."})
    birth_date = DateField(required=settings.ELECTRONIC_VOTE_REQUIRE_BIRTHDATE)

    def __init__(self, *args, **kwargs):
        self.birthdate_check = kwargs.pop('birthdate_check')
        super().__init__(*args, **kwargs)


    def clean(self):
        if not self.birthdate_check:
            return super().clean()

        cleaned_data = super().clean()
        if not cleaned_data['person'].birth_date == cleaned_data.get('birth_date'):
            raise ValidationError('La date de naissance n\'est pas celle inscrite sur les listes électorales.')

        return cleaned_data



class ValidatePhoneForm(BaseForm):
    phone_number = PhoneNumberField(label='Numéro de téléphone portable')

    error_messages = {
        'french_only': "Le numéro doit être un numéro de téléphone français.",
        'mobile_only': "Vous devez donner un numéro de téléphone mobile.",
        'rate_limited': "Trop de SMS envoyés. Merci de réessayer dans quelques minutes.",
        'sending_error': "Le SMS n'a pu être envoyé suite à un problème technique. Merci de réessayer plus tard.",
        'already_used': "Ce numéro a déjà été utilisé pour voter. Si vous le partagez avec une autre"
                        " personne, <a href=\"{}\">vous pouvez"
                        " exceptionnellement en demander le déblocage</a>.",
    }

    def __init__(self, ip, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ip = ip

    def clean_phone_number(self):
        phone_number = normalize_mobile_phone(self.cleaned_data['phone_number'], self.error_messages)

        (self.phone_number, created) = PhoneNumber.objects.get_or_create(phone_number=phone_number)

        if self.phone_number.validated:
            raise ValidationError(mark_safe(self.error_messages['already_used'].format(reverse('unlocking_request'))))

        return phone_number

    def send_code(self):
        try:
            return send_new_code(self.phone_number, self.ip)
        except RateLimitedException:
            self.add_error('phone_number', self.error_messages['rate_limited'])
            return None
        except SMSSendException:
            self.add_error('phone_number', self.error_messages['sending_error'])


class ValidateCodeForm(BaseForm):
    code = CharField(label='Code reçu par SMS')

    def __init__(self, *args, phone_number, **kwargs):
        super().__init__(*args, **kwargs)
        self.phone_number = phone_number

    def clean_code(self):
        # remove spaces added by Cleave.js
        code = self.cleaned_data['code'].replace(' ', '')

        try:
            valid = is_valid_code(self.phone_number, code)
        except RateLimitedException:
            raise ValidationError('Trop de tentative échouées. Veuillez patienter une minute par mesure de sécurité.')

        if not valid:
            codes = list(SMS.objects.values('code').filter(phone_number=self.phone_number,
                                                           created__gt=timezone.now() - timedelta(minutes=30)))
            logger.warning(
                f"SMS code failure : tried {self.cleaned_data['code']} and valid codes were {', '.join([code['code'] for code in codes])}")
            if len(code) == 5:
                raise ValidationError('Votre code est incorrect. Attention : le code demandé figure '
                                      'dans le SMS et comporte 6 chiffres. Ne le confondez pas avec le numéro court '
                                      'de l\'expéditeur (5 chiffres).')
            raise ValidationError('Votre code est incorrect ou expiré.')

        return code


class VoteForm(BaseForm):
    choice = ChoiceField(label='Vote', choices=Vote.VOTE_CHOICES, widget=RadioSelect, required=True)


class PhoneUnlockingRequestForm(ModelForm):
    error_messages = {
        'french_only': "Il n'est possible de voter qu'avec des numéros de téléphone français. Ce formulaire ne sert"
                       " qu'à débloquer un numéro qui a DÉJÀ servi à voter.",
        'mobile_only': "Il n'est possible de voter qu'avec un numéro de téléphone mobile. Ce formulaire ne sert"
                       " qu'à débloquer un numéro qui a DÉJÀ servi à voter.",
        'unused': 'Ce numéro de téléphone n\'a pas été utilisé, vous pouvez déjà bien voter.',
        'unlisted': "La personne qui a voté avec ce numéro l'a fait en tant que non-inscrit sur les listes électorales,"
                    " ou a voté avant le lundi 12, 19h (nous ne sauvegardions alors pas les associations votant/numéro"
                    " de téléphone)."
                    " Il nous est donc malheureusement impossible de vérifier que la personne ayant effectivement voté"
                    " correspond à celle que vous nous déclarez. Nous nous excusons platement pour la gêne occasionnée.",
        'no_duplicate': 'Une requête de déblocage a déjà été validée pour ce numéro. Nous n\'acceptons pas'
                        ' de requête multiple pour le même numéro.',
        'in_review': 'Une requête de déblocage a déjà été reçu pour ce numéro et est en cours de'
                     ' traitement. Merci de bien vouloir patienter !',
    }

    phone_number = PhoneNumberField(label='Le numéro de téléphone à débloquer', required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Une adresse email de contact'
        self.fields['requester'].label = 'Vos nom et prénoms (personne qui souhaite pouvoir voter)'
        self.fields['declared_voter'].label = 'Les nom de naissance et prénoms de la personne qui a déjà voté'

        self.helper = FormHelper()
        self.helper.add_input(layout.Submit('submit', 'Valider'))

        self.helper.layout = layout.Layout(
            'email',
            'phone_number',
            'requester',
            'declared_voter'
        )

    def clean_phone_number(self):
        phone_number = normalize_mobile_phone(self.cleaned_data['phone_number'], self.error_messages)

        try:
            self.phone_number = PhoneNumber.objects.get(phone_number=phone_number)
        except PhoneNumber.DoesNotExist:
            raise ValidationError(self.error_messages['unused'])

        if not self.phone_number.validated:
            raise ValidationError(self.error_messages['unused'])

        if self.phone_number.voter is None:
            raise ValidationError(self.error_messages['unlisted'])

        requests = Counter(u.status for u in UnlockingRequest.objects.filter(phone_number=self.phone_number))

        if requests[UnlockingRequest.STATUS_OK]:
            raise ValidationError(self.error_messages['no_duplicate'])
        elif requests[UnlockingRequest.STATUS_REVIEW]:
            raise ValidationError(self.error_messages['in_review'])

        return phone_number

    def save(self, commit=True):
        self.instance.phone_number = self.phone_number
        self.instance.voter = self.phone_number.voter
        return super().save(commit)

    class Meta:
        model = UnlockingRequest
        fields = ('email', 'requester', 'declared_voter')
