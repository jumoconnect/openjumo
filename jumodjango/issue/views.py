from django.core.urlresolvers import reverse
from django.http import HttpResponsePermanentRedirect, Http404
from issue.models import Issue
from users.models import User
from django.shortcuts import get_object_or_404
from etc.view_helpers import json_error, json_response, render_inclusiontag, render_string

def old_issuename_permalink(request, issuename):
    try:
        i = Issue.objects.get(name = issuename)
        return HttpResponsePermanentRedirect(reverse('entity_url', args=[i.handle]))
    except:
        raise Http404


def old_issue_permalink(request, mongo_id):
    try:
        i = Issue.objects.get(mongo_id = mongo_id)
        return HttpResponsePermanentRedirect(reverse('entity_url', args=[i.handle]))
    except:
        raise Http404

def followed_issue_list(request, user_id):
    start = int(request.GET.get('start', 0))
    end = int(request.GET.get('end', 20))
    user = get_object_or_404(User, id=user_id)
    issue_commitments = user.commitments.with_issues()[start:end].fetch_generic_relations()
    issues = [commitment.entity for commitment in issue_commitments]
    num_issues = user.commitments.with_issues().count()

    html = render_string(request, "issue/includes/followed_issue_list.html", {
        'issues': issues,
        'start_index': start,
    })

    return json_response({
        'html': html,
        'has_more': end < num_issues,
    })
