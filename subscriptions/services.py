from subscriptions.models import Subscription
from django.utils import timezone


def create_subscription(*, organization, customer, plan, start_date):

    
    subscription = Subscription.objects.create(
        organization=organization,
        customer=customer,
        plan=plan,
        start_date=start_date,
    )
    return subscription
