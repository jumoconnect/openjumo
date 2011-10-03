from django.contrib import admin
from django.contrib.contenttypes.generic import GenericInlineModelAdmin

class LinkedInline(admin.options.InlineModelAdmin):
    template = ''
    admin_model_path = None
    admin_app_label = None

    def __init__(self, *args):
        super(LinkedInline, self).__init__(*args)
        if self.admin_model_path is None:
            self.admin_model_path = self.model._meta.object_name.lower()
        if self.admin_app_label is None:
            self.admin_app_label = self.model._meta.app_label

class LinkedStackedInline(LinkedInline):
    template = 'cust_admin/edit_inline/linked_stacked_inline.html'

class LinkedTabularInline(LinkedInline):
    template = 'cust_admin/edit_inline/linked_tabular_inline.html'

class LinkedGenericInline(GenericInlineModelAdmin):
    template = ''
    admin_model_path = None
    admin_app_label = None
    def __init__(self, *args):
        super(LinkedGenericInline, self).__init__(*args)
        if self.admin_model_path is None:
            self.admin_model_path = self.model._meta.object_name.lower()
        if self.admin_app_label is None:
            self.admin_app_label = self.model._meta.app_label

class LinkedGenericStackedInline(LinkedGenericInline):
    template = 'cust_admin/edit_inline/linked_stacked_inline.html'

class LinkedGenericTabularInline(LinkedGenericInline):
    template = 'cust_admin/edit_inline/linked_tabular_inline.html'
