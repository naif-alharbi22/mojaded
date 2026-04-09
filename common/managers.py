from django.db import models


class TenantQuerySet(models.QuerySet):
    def for_org(self, organization):
        return self.filter(organization=organization)


TenantManager = models.Manager.from_queryset(TenantQuerySet)
