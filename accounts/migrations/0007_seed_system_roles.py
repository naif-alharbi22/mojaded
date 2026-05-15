from django.db import migrations


SYSTEM_ROLE_SPECS = [
    {
        "slug": "admin",
        "name": "مسؤول",
        "description": "صلاحيات كاملة عدا حذف المنشأة",
        "permissions": [
            "customers.view", "customers.create", "customers.edit", "customers.delete",
            "subscriptions.view", "subscriptions.create", "subscriptions.edit", "subscriptions.delete",
            "plans.view", "plans.create", "plans.edit", "plans.delete",
            "billing.view", "billing.create", "billing.edit", "billing.delete",
            "users.view", "users.create", "users.edit", "users.delete",
            "settings.view", "settings.edit",
        ],
    },
    {
        "slug": "manager",
        "name": "محرر بيانات",
        "description": "إدخال وتعديل البيانات دون إدارة المستخدمين أو الإعدادات",
        "permissions": [
            "customers.view", "customers.create", "customers.edit",
            "subscriptions.view", "subscriptions.create", "subscriptions.edit",
            "plans.view", "plans.create", "plans.edit",
            "billing.view", "billing.create", "billing.edit",
            "settings.view",
        ],
    },
    {
        "slug": "viewer",
        "name": "مشاهد",
        "description": "اطلاع فقط على البيانات دون أي تعديل",
        "permissions": [
            "customers.view",
            "subscriptions.view",
            "plans.view",
            "billing.view",
            "settings.view",
        ],
    },
]


def seed_roles(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    Role = apps.get_model("accounts", "Role")
    for org in Organization.objects.all():
        for spec in SYSTEM_ROLE_SPECS:
            Role.objects.update_or_create(
                organization=org,
                slug=spec["slug"],
                defaults={
                    "name": spec["name"],
                    "description": spec["description"],
                    "permissions": list(spec["permissions"]),
                    "is_system": True,
                },
            )


def remove_seeded_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(is_system=True, slug__in=[s["slug"] for s in SYSTEM_ROLE_SPECS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_role_user_role"),
    ]

    operations = [
        migrations.RunPython(seed_roles, remove_seeded_roles),
    ]
