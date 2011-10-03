
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from etc.constants import ACCOUNT_COOKIE_SALT, ACCOUNT_COOKIE
from etc.user import check_cookie
from etc.view_helpers import json_error

def PostOnly(viewfunc):
    """returns HttpResponseBadRequest if request is not a post"""
    def posted(*args, **kwargs):
        request = args[0]
        if request.method == 'POST':
            return viewfunc(*args, **kwargs)
        return HttpResponseBadRequest()
    return posted

def AjaxPostOnly(viewfunc):
    """returns HttpResponseBadRequest if request is not a post"""
    def posted(*args, **kwargs):
        request = args[0]
        if request.method == 'POST':
            return viewfunc(*args, **kwargs)
        return HttpResponseBadRequest(json_error('Post only.'))
    return posted

def SimpleAjaxPostOnly(viewfunc):
    def posted(*args, **kwargs):
        request = args[0]
        if request.method == 'POST':
            if 'query' in request.POST:
                return viewfunc(*args, **kwargs)
            else:
                return HttpResponseBadRequest(json_error('Query missing.'))
        else:
            return HttpResponseBadRequest(json_error('Post only.'))
    return posted

def AccountRequired(viewfunc):
    def posted(*args, **kwargs):
        request = args[0]
        if ACCOUNT_COOKIE in request.COOKIES and ACCOUNT_COOKIE_SALT in request.COOKIES:
            if check_cookie(request.COOKIES[ACCOUNT_COOKIE], request.COOKIES[ACCOUNT_COOKIE_SALT]):
                return viewfunc(*args, **kwargs)
            else:
                return HttpResponseRedirect('/login?redirect_to=%s' % request.path)
        else:
            return HttpResponseRedirect('/login?redirect_to=%s' % request.path)
    return posted

def NotLoggedInRequired(viewfunc):
    def posted(*args, **kwargs):
        request = args[0]
        if ACCOUNT_COOKIE in request.COOKIES and ACCOUNT_COOKIE_SALT in request.COOKIES:
            if check_cookie(request.COOKIES[ACCOUNT_COOKIE], request.COOKIES[ACCOUNT_COOKIE_SALT]):
                return HttpResponseRedirect('/')
            else:
                return viewfunc(*args, **kwargs)
        else:
            return viewfunc(*args, **kwargs)
    return posted
