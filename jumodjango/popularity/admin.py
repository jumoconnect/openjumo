from django import forms
from django.contrib import admin

from django.forms.models import BaseModelFormSet
from django.contrib.sites.models import Site
from popularity.models import TopList, TopListItem, Section
from etc.entities import obj_to_type
from cust_admin.views.main import ExtChangeList
from cust_admin.widgets import ForeignKeyToObjWidget
from cust_admin.forms import HiddenRankModelForm

#class TopListItemInline(admin.StackedInline):
#    model = TopListItem
#    extra = 0
#    verbose_name = 'List Item'
#    verbose_name_plural = 'List Items'

class TopListItemInline(admin.TabularInline):
    model = TopListItem
    extra = 0
    fields = ('entity_content_type', 'entity_id', 'rank')
    form = HiddenRankModelForm

    sortable_field_name = "rank"

    verbose_name = "Item"
    verbose_name_plural = "Items"

    related_lookup_fields = {
        'generic': [['entity_content_type', 'entity_id']],
    }

class TopListAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'is_current')
    list_editable = ('section', 'is_current',)
    inlines = [TopListItemInline]


class TopListInline(admin.TabularInline):
    model = TopList
    extra = 0
    fields = ('title', 'is_current', 'position')
    form = HiddenRankModelForm

    sortable_field_name = 'position'
    verbose_name = 'List'
    verbose_name_plural = 'Lists'

class SectionAdmin(admin.ModelAdmin):
    inlines = [TopListInline]

admin.site.register(TopList, TopListAdmin)
admin.site.register(Section, SectionAdmin)
