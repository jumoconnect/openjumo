from datetime import datetime
from django.core.cache import cache as django_cache
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError, Http404
from django.views.decorators.cache import cache_page
from etc import cache
from etc.view_helpers import render, render_string, json_error
from issue.models import Issue
import logging
from org.models import Org
from popularity.models import Section, Sections, TopList
import random
import re
import settings
from users.forms import LoginForm
from users.models import User
from users.views import home
from discovery.models import DiscoveryMap

def throw_error(request):
    r = HttpResponseRedirect('/')
    l = dir(r)
    heh = request.get_host()
    a = b

def return_org(request, org):
    if request.user.is_authenticated():
        related_orgs = org.get_related_orgs_for_user(request.user)[:5]
    else:
        related_orgs = org.get_all_related_orgs[:5]

    is_allowed_to_edit = org.is_editable_by(request.user)

    return render(request, 'org/profile.html', {
        'entity' : org,
        'title' : org.name,
        'related_orgs' : related_orgs,
        'is_allowed_to_edit': is_allowed_to_edit,
    })

def return_issue(request, issue):
    return render(request, 'issue/profile.html', {
        'entity' : issue,
        'title' : issue.name,
    })

def return_user(request, user):
    return render(request, 'user/profile.html', {
        'entity' : user,
        'title' : user.get_name,
    })

def clean_url(request, handle):
    org_id = None
    issue_id = None
    user_id = None
    org = None
    issue = None
    user = None

    handle = re.sub(r'[^a-zA-Z0-9\-_]+', '', handle).lower()

    # try first for cache!
    org_id = django_cache.get(cache._cache_key(Org, handle))
    if org_id:
        org = django_cache.get(cache._cache_key(Org, org_id))
        if org:
            return return_org(request, org)

    issue_id = django_cache.get(cache._cache_key(Issue, handle))
    if issue_id:
        issue = django_cache.get(cache._cache_key(issue, handle))
        if issue:
            return return_issue(request, issue)

    user_id = django_cache.get(cache._cache_key(user, handle))
    if user_id:
        user = django_cache.get(cache._cache_key(user, handle))
        if user:
            return return_user(request, user)

    # try second for db!
    org = None
    issue = None
    user = None


    try:
        org = Org.objects.get(handle = handle)
        cache.put_on_handle(org, handle)
        return return_org(request, org)
    except Org.DoesNotExist:
        logging.error("Org Handle %s doesn't exist." % handle)
    except:
        logging.exception("Org Handler Exception")

    try:
        user = User.objects.get(username = handle, is_active = True)
        cache.put_on_handle(user, handle)
        return return_user(request, user)
    except User.DoesNotExist:
        logging.error("User Username %s doesn't exist." % handle)
    except:
        logging.exception("User Handler Exception")

    try:
        issue = Issue.objects.get(handle = handle)
        cache.put_on_handle(issue, handle)
        return return_issue(request, issue)
    except Issue.DoesNotExist:
        logging.error("Issue Handle %s doesn't exist." % handle)
    except:
        logging.exception("Issue Handler Exception")

    raise Http404

def about(request):
    return render(request, 'etc/about.html', {
            "title": "About"
            })

def blog(request):
    return render(request, 'etc/blog.html', {
            "title": "Jumo and GOOD Combine Forces to Create Content and Social Engagement Platform"
            })

def contact(request):
    return render(request, 'etc/contact.html', {
            "title": "Contact Us"
            })

def team(request):
    return render(request, 'etc/team.html', {
            "title": "Our Team"
            })

def help(request):
    return render(request, 'etc/help.html', {
            "title": "Help"
            })

def jobs(request):
    return render(request, 'etc/jobs.html', {
            "title": "Jobs"
            })

def privacy(request):
    return render(request, 'etc/privacy.html', {
            "title": "Privacy Policy"
            })

def terms(request):
    return render(request, 'etc/terms.html', {
            "title": "Terms of Service"
            })

def signed_out_home(request):
    lists = Section.get_lists(Sections.HOME)
    list_ids = [l.id for l in lists]
    top_lists = TopList.get_entities_for_lists(list_ids)

    top_categories, sub_category_groups, discovery_item_groups = DiscoveryMap.get_lists()

    return render(request, 'etc/home.html', {
            'title' : None,
            'login_form':LoginForm(),
            'top_categories': top_categories,
            'sub_category_groups': sub_category_groups,
            'discovery_item_groups': discovery_item_groups,
            'top_lists': top_lists
        })

#if not settings.DEBUG:
#    signed_out_home = cache_page(signed_out_home, 60*15)


def index(request):
    if request.user.id:
        return home(request)

    return signed_out_home(request)

def error_404(request):
    if request.is_ajax():
        exception = getattr(request, 'exception', None)
        return json_error(404, exception)

    return HttpResponseNotFound(render_string(request, 'errors/error.html', {
            }))

def error_500(request):
    if request.is_ajax():
        exception = getattr(request, 'exception', None)
        return json_error(500, exception)

    return HttpResponseServerError(render_string(request, 'errors/error.html', {
            }))

def health_check(request):
    return HttpResponse('')
