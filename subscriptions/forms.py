from django import forms
from .models import Subscription



class NewSubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = [
            "customer",
            "plan",
            "subscription_type",
            "start_date",
            "duration_months",
            "amount",
            "status",
            "note",
        ]

        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3}),
            "subscription_type": forms.RadioSelect,
        }