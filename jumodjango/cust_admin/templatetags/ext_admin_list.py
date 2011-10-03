import datetime

from django.conf import settings
from django.contrib.admin.util import lookup_field, display_for_field, label_for_field
from django.contrib.admin.views.main import ALL_VAR, EMPTY_CHANGELIST_VALUE
from django.contrib.admin.views.main import ORDER_VAR, ORDER_TYPE_VAR, PAGE_VAR, SEARCH_VAR
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.forms.forms import pretty_name
from django.utils import formats
from django.template.defaultfilters import escapejs
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode, force_unicode
from django.template import Library
from django.contrib.admin.templatetags.admin_list import result_headers, result_hidden_fields

register = Library()

"""
All this was copy and pasted so the custDismissRelatedLookupPopup could be inserted here.
Do a find.
"""

def ext_items_for_result(cl, result, form):
    """
    Generates the actual list of data.
    """
    first = True
    pk = cl.lookup_opts.pk.attname
    for field_name in cl.list_display:
        row_class = ''
        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except (AttributeError, ObjectDoesNotExist):
            result_repr = EMPTY_CHANGELIST_VALUE
        else:
            if f is None:
                allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)
                if boolean:
                    allow_tags = True
                    result_repr = _boolean_icon(value)
                else:
                    result_repr = smart_unicode(value)
                # Strip HTML tags in the resulting text, except if the
                # function has an "allow_tags" attribute set to True.
                if not allow_tags:
                    result_repr = escape(result_repr)
                else:
                    result_repr = mark_safe(result_repr)
            else:
                if value is None:
                    result_repr = EMPTY_CHANGELIST_VALUE
                if isinstance(f.rel, models.ManyToOneRel):
                    result_repr = escape(getattr(result, f.name))
                else:
                    result_repr = display_for_field(value, f)
                if isinstance(f, models.DateField) or isinstance(f, models.TimeField):
                    row_class = ' class="nowrap"'
        if force_unicode(result_repr) == '':
            result_repr = mark_safe('&nbsp;')
        # If list_display_links not defined, add the link tag to the first field
        if (first and not cl.list_display_links) or field_name in cl.list_display_links:
            table_tag = {True:'th', False:'td'}[first]
            first = False
            url = cl.url_for_result(result)
            # Convert the pk to something that can be used in Javascript.
            # Problem cases are long ints (23L) and non-ASCII strings.
            if cl.to_field:
                attr = str(cl.to_field)
            else:
                attr = pk
            value = result.serializable_value(attr)
            result_id = repr(force_unicode(value))[1:]

            #All this was copy and pasted so the custDismissRelatedLookupPopup could be inserted here.
            ext_attrib = ""
            if cl.is_popup:
                if cl.is_ext_popup:
                    ext_attrib = 'onclick="opener.custDismissRelatedLookupPopup(window, %s, \'%s\'); return false;"' % (result_id, escapejs(result_repr))
                else:
                    ext_attrib = ' onclick="opener.dismissRelatedLookupPopup(window, %s); return false;"' % result_id

            yield mark_safe(u'<%s%s><a href="%s" %s>%s</a></%s>' % \
                (table_tag, row_class, url, ext_attrib, result_repr, table_tag))
        else:
            # By default the fields come from ModelAdmin.list_editable, but if we pull
            # the fields out of the form instead of list_editable custom admins
            # can provide fields on a per request basis
            if form and field_name in form.fields:
                bf = form[field_name]
                result_repr = mark_safe(force_unicode(bf.errors) + force_unicode(bf))
            else:
                result_repr = conditional_escape(result_repr)
            yield mark_safe(u'<td%s>%s</td>' % (row_class, result_repr))
    if form and not form[cl.model._meta.pk.name].is_hidden:
        yield mark_safe(u'<td>%s</td>' % force_unicode(form[cl.model._meta.pk.name]))


def ext_results(cl):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            yield list(ext_items_for_result(cl, res, form))
    else:
        for res in cl.result_list:
            yield list(ext_items_for_result(cl, res, None))



def ext_result_list(cl):
    """
    Displays the headers and data list together
    """
    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': list(result_headers(cl)),
            'results': list(ext_results(cl))}
ext_result_list = register.inclusion_tag("admin/change_list_results.html")(ext_result_list)
