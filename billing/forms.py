from django import forms
from .models import Invoice
from subscriptions.models import Subscription


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["subscription", "invoice_type", "amount", "issue_date", "due_date", "status"]
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields["subscription"].queryset = Subscription.objects.for_org(organization)
