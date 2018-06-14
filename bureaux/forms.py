from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core.exceptions import ValidationError
from django import forms
from bureaux.models import Bureau

from votes.models import VoterListItem


class OpenBureauForm(forms.Form):
    place = forms.CharField(label='Lieu', max_length=255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Valider'))


class BureauResultsForm(forms.ModelForm):
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


class AssistantCodeForm(forms.Form):
    code = forms.CharField(help_text="Code de connexion")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Me connecter à mon bureau de vote'))

    def clean_code(self):
        code = self.cleaned_data['code'].upper().strip().replace(' ', '')

        return code


class SelectPersonByBirthdateField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.RadioSelect())
        super().__init__(*args, **kwargs)
        self.use_full_date = True

    def label_from_instance(self, obj):
        return obj.birth_date if self.use_full_date else obj.birth_date.year


class SelectHomonymForm(forms.Form):
    person = SelectPersonByBirthdateField(
        empty_label=None,
        queryset=VoterListItem.objects.filter(vote_status=VoterListItem.VOTE_STATUS_NONE),
        label='Date de naissance de la personne',
    )

    def __init__(self, ids, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qs = self.fields['person'].queryset = self.fields['person'].queryset.filter(pk__in=ids)

        if len({p.birth_date.year for p in qs}) == len(qs):
            self.fields['person'].use_full_date = False
            self.fields['person'].label = 'Année de naissance de la personne'

        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Marquer comme votant'))
