from django.shortcuts import render

from common.toast_utils import toast_response
from setting.forms import OrganizationForm


def view_settings(request):
    org = request.user.organization

    if request.method == "POST":
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return toast_response("تم تحديث الإعدادات بنجاح", type="success", close_modal=False)
    else:
        form = OrganizationForm(instance=org)

    return render(request, "setting/index.html", {
        "form": form,
        "organization": org,
    })
