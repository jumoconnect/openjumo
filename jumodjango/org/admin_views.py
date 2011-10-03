from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from org.models import Org


def report(request):
    return render_to_response(
        "admin/org/report.html",
        {'org_list' : Org.objects.order_by('name'), 'title': 'List of Orgs'},
        RequestContext(request, {}),
    )
report = staff_member_required(report)
