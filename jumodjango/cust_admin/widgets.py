from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe

class AdminImageFieldWithThumbWidget(AdminFileWidget):
    def render(self, name, value, attrs=None):
        thumb_html = ''
        if value and hasattr(value, "url"):
            thumb_html = '<img src="%s" width="60" width="60"/>' % value.url
        return mark_safe("%s%s" % (thumb_html, super(AdminImageFieldWithThumbWidget, self).render(name, value,attrs)))


class ForeignKeyToObjWidget(forms.TextInput):
    """
    This is used to get the __unicode__ representation of an object rather than just the ID.
    It has the benefit of doing a few things you expect like showing the changed object rather
    than just the changed ID when you change the related field before saving.
    """
    input_type = 'hidden'
    is_hidden = True

    def render_mini_model_inline(self, obj, name, change_url):
        return "<a id='name_id_%s' href='%s'>%s</a>" % (name, change_url, smart_unicode(obj))

    def __init__(self, rel, attrs=None, using=None):
        self.rel = rel
        self.db = using
        super(ForeignKeyToObjWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        #Generate date for the lookup link
        if attrs is None:
            attrs = {}
        related_url = '../../../%s/%s/' % (self.rel.to._meta.app_label, self.rel.to._meta.object_name.lower())
        params = self.url_parameters()
        if params:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.items()])
        else:
            url = ''
        if not attrs.has_key('class'):
            attrs['class'] = 'vForeignKeyRawIdAdminField' # The JavaScript looks for this hook.

        #Generate Link and Object for the render name.
        key = self.rel.get_related_field().name
        rendered_obj = "<a id='name_id_%s'><i>Nothing Selected</i></a>" % name
        try:
            obj = self.rel.to._default_manager.using(self.db).get(**{key: value})
            change_url = reverse(
                "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.object_name.lower()),
                args=(obj.pk,)
            )
            rendered_obj = self.render_mini_model_inline(obj, name, change_url)
        except (ValueError, self.rel.to.DoesNotExist):
            pass

        output = [super(ForeignKeyToObjWidget, self).render(name, value, attrs)]
        output.append(rendered_obj)
        output.append('<a href="%s%s" class="related-lookup" id="lookup_id_%s" onclick="return custShowRelatedObjectLookupPopup(this);"> ' % (related_url, url, name))
        output.append('<img src="%simg/admin/selector-search.gif" width="16" height="16" alt="%s" /></a>' % (settings.ADMIN_MEDIA_PREFIX, _('Lookup')))
        return mark_safe(u''.join(output))

    def base_url_parameters(self):
        params = {}
        if self.rel.limit_choices_to and hasattr(self.rel.limit_choices_to, 'items'):
            items = []
            for k, v in self.rel.limit_choices_to.items():
                if isinstance(v, list):
                    v = ','.join([str(x) for x in v])
                else:
                    v = str(v)
                items.append((k, v))
            params.update(dict(items))
        return params

    def url_parameters(self):
        from django.contrib.admin.views.main import TO_FIELD_VAR
        params = self.base_url_parameters()
        params.update({TO_FIELD_VAR: self.rel.get_related_field().name})
        return params
