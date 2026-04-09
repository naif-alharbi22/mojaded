from django import forms
from organizations.models import Organization


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name"]
