from django import template
from django.conf import settings
try:
    import simplejson as json
except ImportError:
    import json

from etc.view_helpers import json_encode as _json_encode
from etc.view_helpers import render_string
from etc.func import wrap
#from textwrap import wrap << this thing is SO DUMB
from django.template.loader import render_to_string

from django.utils.encoding import force_unicode # brennan imported these for text truncation
from django.utils.functional import allow_lazy
from django.template.defaultfilters import stringfilter
register = template.Library()


@register.simple_tag
def url_target_blank(text):
    return text.replace('<a ', '<a target="_blank" ')
url_target_blank = register.filter(url_target_blank)
url_target_blank.is_safe = True

@register.simple_tag
def url_sans_http(text):
    return text.replace('>http://', '>').replace('>www.', '>').replace('.com/<', '.com<').replace('.org/<', '.org<')
url_sans_http = register.filter(url_sans_http)
url_sans_http.is_safe = True

def _create_static_url(token):
    return '%s/static%s%s?v=%s' % (
                                      settings.STATIC_URL,
                                      ('' if token[0] == '/' else '/'),
                                      token,
                                      settings.ASSET_HASH
                                  )

def contains(value, arg):
    return arg in value
register.filter('contains', contains)

@register.simple_tag
def get_fb_storyid(fb_story_id):
    if fb_story_id.find('_'):
        return fb_story_id.split('_')[1]
    return fb_story_id

@register.simple_tag
def static_url(token):
    return _create_static_url(token)

@register.simple_tag
def full_url(url):
    return "http://%s%s" % (settings.HTTP_HOST, url)

@register.simple_tag
def get_humanized_type(text):
    if text:
        ty = text.lower()
        if ty == "org":
            return "Organizations"
        elif ty == "user":
            return "People"
        elif ty == "issue":
            return "Issues"
    return text

@register.simple_tag
def json_encode(obj):
    return _json_encode(obj)

@register.simple_tag
def possessive(value):
    """
    Returns a possessive form of a name according to English rules
    Mike returns Mike's, while James returns James'
    """
    if value[-1] == 's':
        return "%s'" % value
    return "%s's" % value


def truncate_chars(s, num):
    """
    Template filter to truncate a string to at most num characters respecting word
    boundaries.
    """
    s = force_unicode(s)
    length = int(num)
    if len(s) > length:
        length = length - 3
        if s[length-1] == ' ' or s[length] == ' ':
            s = s[:length].strip()
        else:
            words = s[:length].split()
            if len(words) > 1:
                del words[-1]
            s = u' '.join(words)
        s += '...'
    return s
truncate_chars = allow_lazy(truncate_chars, unicode)

def truncatechars(value, arg):
    """
    Truncates a string after a certain number of characters, but respects word boundaries.

    Argument: Number of characters to truncate after.
    """
    try:
        length = int(arg)
    except ValueError: # If the argument is not a valid integer.
        return value # Fail silently.
    return truncate_chars(value, length)
truncatechars.is_safe = True
truncatechars = stringfilter(truncatechars)

register.filter(truncatechars)



# @register.filter("truncate_chars")
# def truncate_chars(value, max_length):
#         if len(value) <= max_length:
#                     return value

#         truncd_val = value[:max_length]
#         if value[max_length] != " ":
#             rightmost_space = truncd_val.rfind(" ")
#             if rightmost_space != -1:
#                 truncd_val = truncd_val[:rightmost_space]

#         return truncd_val + "..."



@register.filter
def partition(my_list, n):
    '''
    Partitions a list into sublists, each with n (or fewer) elements.
    my_list = [1,2,3,4,5]
    partion(my_list, 2) => [[1,2],[3,4],[5]]
    '''

    try:
        n = int(n)
        my_list = list(my_list)
    except ValueError:
        return [my_list]
    return [my_list[i:i+n] for i in range(0, len(my_list), n)]
