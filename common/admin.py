from django.contrib import admin


class TenantModelAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization=request.user.organization)

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, "organization") and not obj.organization_id:
            obj.organization = request.user.organization
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser and db_field.related_model:
            related_model = db_field.related_model
            if hasattr(related_model, "organization"):
                kwargs["queryset"] = related_model.objects.filter(
                    organization=request.user.organization
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
