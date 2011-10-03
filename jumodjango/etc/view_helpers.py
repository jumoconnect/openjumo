from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
try:
    import simplejson as json
except:
    import json

import datetime
from decimal import Decimal
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.db.models import ImageField, FileField
from django.db.models import Model
from django.db.models.query import QuerySet
from django.utils.encoding import smart_unicode
from urllib import urlencode
import logging
from django.template import Template


from django.conf import settings

def json_response(obj, status_code=200):
    """returns a HttpResponse wrapped with a json dump of the obj"""
    return HttpResponse(json.dumps({'result' : obj}), mimetype='application/json', status=status_code)

def json_error(status_code, error=None):
    if isinstance(error, Exception):
        error = error.message
    return HttpResponse(error, status=status_code, mimetype='application/json')

def json_encode(data):
    def _any(data):
        ret = None
        if isinstance(data, list):
            ret = _list(data)
        elif isinstance(data, dict):
            ret = _dict(data)
        elif isinstance(data, Decimal):
            ret = str(data)
        elif isinstance(data, QuerySet):
            ret = _list(data)
        elif isinstance(data, Model):
            ret = _model(data)
        elif isinstance(data, basestring):
            ret = smart_unicode(data, encoding='utf-8')
            #ret = unicode(data.decode('utf-8'))
        elif isinstance(data, datetime.datetime):
            ret = str(data).replace(' ', 'T')
        elif isinstance(data, datetime.date):
            ret = str(data)
        elif isinstance(data, datetime.time):
            ret = "T" + str(data)
        else:
            ret = data
        return ret

    def _model(data):
        ret = {}
        for f in data._meta.fields:
            if isinstance(f, ImageField) or isinstance(f, FileField):
                ret[f.attname] = unicode(getattr(data, f.attname))
            else:
                ret[f.attname] = _any(getattr(data, f.attname))
        fields = dir(data.__class__) + ret.keys()
        add_ons = [k for k in dir(data) if k not in fields and k not in ('delete', '_state',)]
        for k in add_ons:
            ret[k] = _any(getattr(data, k))
        return ret

    def _list(data):
        ret = []
        for v in data:
            ret.append(_any(v))
        return ret

    def _dict(data):
        ret = {}
        for k,v in data.items():
            ret[k] = _any(v)
        return ret

    ret = _any(data)
    return json.dumps(ret, cls=DateTimeAwareJSONEncoder)


def render(request, template, variables = {}):
    return render_to_response(template, variables, context_instance = RequestContext(request))

def render_string(request, template, variables = {}):
    return render_to_string(template, variables, context_instance = RequestContext(request))

def render_inclusiontag(request, tag_string, tag_file, dictionary=None):
    dictionary = dictionary or {}
    context_instance = RequestContext(request)
    context_instance.update(dictionary)
    t = Template("{%% load %s %%}{%% %s %%}" % (tag_file, tag_string))
    return t.render(context_instance)

def url_with_qs(path, **kwargs):
    return "%s?%s" % (path, urlencode(kwargs))
