from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Form, fields

from bureaux.models import Bureau


class OpenBureauForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Valider'))

    class Meta:
        model = Bureau
        fields = ('place',)


class CloseBureauForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Fermer le bureau'))

    def clean(self):
        if self.instance.end_time is not None:
            raise ValidationError("Ce bureau est déjà fermé.")

    class Meta:
        model = Bureau
        fields = []


class BureauResultsForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Valider ces résultats'))
        for key in self.fields:
            self.fields[key].required = True

    def clean(self):
        if self.instance.end_time is None:
            raise ValidationError("Vous devez d'abord fermer le bureau avant de remonter les résultats.")

    class Meta:
        model = Bureau
        fields = (
            'result1_yes',
            'result1_no',
            'result1_blank',
            'result1_null',
            'result2_yes',
            'result2_no',
            'result2_blank',
            'result2_null',
            'results_comment'
        )


class AssistantCodeForm(Form):
    code = fields.CharField(help_text="Code de connexion")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Me connecter à mon bureau de vote'))

    def clean_code(self):
        try:
            Bureau.objects.get(assistant_code=self.cleaned_data['code'])
        except Bureau.DoesNotExist:
            raise ValidationError("Ce code n'existe pas ou est invalide.")

        return self.cleaned_data['code']