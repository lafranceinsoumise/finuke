import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core.exceptions import ValidationError
from django.forms import Form, CharField, ChoiceField, ModelChoiceField, RadioSelect
from phonenumber_field.formfields import PhoneNumberField

from phones.models import PhoneNumber
from phones.sms import send_new_code, is_valid_code, SMSCodeException
from votes.models import Vote, VoterListItem

MOBILE_PHONE_RE = re.compile(r'^0[67]')


class BaseForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Valider'))


class FindPersonInListForm(Form):
    person = ModelChoiceField(queryset=VoterListItem.objects.filter(vote_status=VoterListItem.VOTE_STATUS_NONE), widget=None)


class ValidatePhoneForm(BaseForm):
    phone_number = PhoneNumberField(label='Numéro de téléphone portable')

    def __init__(self, ip, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ip = ip

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if phone_number.country_code != 33:
            raise ValidationError('Le numéro doit être un numéro de téléphone français.')

        if not phone_number.is_valid():
            raise ValidationError('Le numéro doit être un numéro de téléphone valide.')

        if not MOBILE_PHONE_RE.match(phone_number.as_national):
            raise ValidationError('Vous devez donner un numéro de téléphone mobile.')

        (self.phone_number, created) = PhoneNumber.objects.get_or_create(phone_number=self.cleaned_data['phone_number'])

        if self.phone_number.validated:
            raise ValidationError('Ce numéro a déjà été utilisé pour voter.')

        return self.cleaned_data['phone_number']

    def send_code(self):
        try:
            return send_new_code(self.phone_number, self.ip)
        except SMSCodeException:
            self.add_error('phone_number', 'Trop de SMS envoyés. Merci de réessayer dans quelques minutes.')
            return None


class ValidateCodeForm(BaseForm):
    code = CharField(label='Code reçu par SMS')

    def __init__(self, *args, phone_number, **kwargs):
        super().__init__(*args, **kwargs)
        self.phone_number = PhoneNumber.objects.get(phone_number=phone_number)

    def clean_code(self):
        code = self.cleaned_data['code'].replace(' ', '')

        if not is_valid_code(self.phone_number, code):
            raise ValidationError('Votre code est invalide ou expiré.')

        return code


class VoteForm(BaseForm):
    choice = ChoiceField(label='Vote', choices=Vote.VOTE_CHOICES, widget=RadioSelect, required=True)
