from django.contrib import admin
from django.contrib.contenttypes.generic import GenericTabularInline
from discovery.models import TopCategory, SubCategory, DiscoveryItem
from cust_admin.models import LinkedTabularInline
from cust_admin.forms import HiddenRankModelForm

class SubCategoryInline(LinkedTabularInline):
    model = SubCategory
    form = HiddenRankModelForm
    show_edit_link = True
    extra = 0
    sortable_field_name = "rank"
    fields = ('name', 'discovery_item_count', 'rank',)
    readonly_fields = ('discovery_item_count',)

class DiscoveryItemInline(admin.TabularInline):
    model = DiscoveryItem
    form = HiddenRankModelForm
    extra = 0
    sortable_field_name = "rank"

    related_lookup_fields = {
        'generic': [['content_type', 'object_id']],
    }

class TopCategoryAdmin(admin.ModelAdmin):
    inlines = [SubCategoryInline]
    list_display = ('name', 'rank', 'sub_category_count',)
    list_editable = ('rank',)
    ordering = ('rank',)

class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('parent', 'name', 'rank', 'discovery_item_count')
    list_display_links = ('name',)
    inlines = [DiscoveryItemInline]

    def get_changelist(self, request):
        from django.contrib.admin.views.main import ChangeList
        class MultipleOrderingChangelist(ChangeList):
            def get_query_set(self):
                qs = super(MultipleOrderingChangelist, self).get_query_set()
                return qs.order_by('parent', 'rank')
        return MultipleOrderingChangelist

admin.site.register(TopCategory, TopCategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
