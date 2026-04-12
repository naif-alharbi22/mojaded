from django import forms
from .models import Plan, Subscription
from customers.models import Customer


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

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields["customer"].queryset = Customer.objects.for_org(organization)
            self.fields["plan"].queryset = Plan.objects.for_org(organization)


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["name", "description", "amount", "billing_cycle"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
