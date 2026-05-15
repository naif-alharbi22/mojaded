from django import forms

from accounts.models import Role, User
from accounts.permissions import ALL_PERMISSIONS
from organizations.models import Organization


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name"]


class NewUserForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    role = forms.ModelChoiceField(queryset=Role.objects.none(), required=False)

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if organization is not None:
            self.fields["role"].queryset = Role.objects.filter(organization=organization)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("اسم المستخدم مستخدم بالفعل")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("البريد الإلكتروني مستخدم بالفعل")
        return email


class EditUserForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    role = forms.ModelChoiceField(queryset=Role.objects.none(), required=False)
    is_active = forms.BooleanField(required=False)

    def __init__(self, *args, organization=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.user = user
        if organization is not None:
            self.fields["role"].queryset = Role.objects.filter(organization=organization)


class RoleForm(forms.ModelForm):
    permissions = forms.MultipleChoiceField(
        choices=[(p, p) for p in ALL_PERMISSIONS],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Role
        fields = ["name", "description"]

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if self.instance and self.instance.pk:
            self.fields["permissions"].initial = self.instance.permissions or []

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("الاسم مطلوب")
        qs = Role.objects.filter(organization=self.organization, name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("يوجد دور بنفس الاسم")
        return name

    def save(self, commit=True):
        role = super().save(commit=False)
        role.organization = self.organization
        if not role.slug:
            from django.utils.text import slugify
            base = slugify(role.name, allow_unicode=True) or "role"
            slug = base
            i = 1
            while Role.objects.filter(organization=self.organization, slug=slug).exclude(pk=role.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            role.slug = slug
        role.permissions = self.cleaned_data.get("permissions") or []
        if commit:
            role.save()
        return role
