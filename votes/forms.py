from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Field
from django.core.exceptions import ValidationError
from django.forms import Form, CharField, ChoiceField, ModelChoiceField
from phonenumber_field.formfields import PhoneNumberField

from phones.models import PhoneNumber
from phones.sms import send_new_code, is_valid_code, SMSCodeException
from votes.models import Vote, VoterListItem


class BaseForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Valider'))


class FindPersonInListForm(Form):
    person = ModelChoiceField(queryset=VoterListItem.objects.filter(vote_status=VoterListItem.VOTE_STATUS_NONE), widget=None)


class ValidatePhoneForm(BaseForm):
    phone_number = PhoneNumberField(label='Numéro de téléphone portable')

    def clean_phone_number(self):
        if self.cleaned_data['phone_number'].country_code != 33:
            raise ValidationError('Le numéro doit être un numéro de téléphone français.')

        (phone_number, created) = PhoneNumber.objects.get_or_create(phone_number=self.cleaned_data['phone_number'])

        if phone_number.validated:
            raise ValidationError('Ce numéro a déjà été utilisé pour voter.')

        try:
            send_new_code(phone_number)
        except SMSCodeException:
            raise ValidationError('Trop de SMS envoyés. Merci de réessayer dans quelques minutes.')

        return self.cleaned_data['phone_number']


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
    choice = ChoiceField(label='Vote', choices=Vote.VOTE_CHOICES)
