from cust_admin.views.main import ExtChangeList
from cust_admin.widgets import ForeignKeyToObjWidget
from django import forms
from django.contrib import admin
from etc import cache
from entity_items.admin import MediaItemInline, ActionInline, AdvocateInline, TimelineInline, CenterContentItemInline, LeftContentItemInline
from issue.models import Issue, IssueRelation
from org.models import Org


######## INLINES ########
class IssueChildrenInline(admin.TabularInline):
    model = IssueRelation
    extra = 0
    classes = ('collapse closed',)
    fields = ('child', 'relation_type',)
    fk_name = "parent"
    verbose_name = "Related Issue"
    verbose_name_plural = "Related Issues"

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'child':
            kwargs['widget'] = ForeignKeyToObjWidget(rel=IssueRelation._meta.get_field('child').rel)
        return super(IssueChildrenInline,self).formfield_for_dbfield(db_field,**kwargs)


######## MODEL FORM AND ADMIN ########
class IssueAdminForm(forms.ModelForm):
    class Meta:
        model = Issue
        widgets = {'location': ForeignKeyToObjWidget(rel=Issue._meta.get_field('location').rel),
                   'summary': forms.Textarea(),}
    class Media:
        js = ['cust_admin/js/widgets.js']
        css = {'all':('cust_admin/css/extend_admin.css',)}

class IssueAdmin(admin.ModelAdmin):
    #Issue List Page Values
    form=IssueAdminForm
    search_fields = ['name','handle']
    search_fields_verbose = ["Name",]
    list_display = ('name', 'date_updated', 'is_active', 'content_upgraded')
    list_filter = ('is_active', 'content_upgraded',)
    ordering = ('name',)

    def get_changelist(self, request, **kwargs):
        return ExtChangeList

    change_list_template = "cust_admin/change_list.html"

    #Issue Change Page Values
    fieldsets = (
        ('Issue Profile', {
            'fields': (
                ('is_active','content_upgraded'),
                ('name', 'handle',),
                'img_small_url', 'img_large_url','summary','location',
                ('date_created','date_updated',),
        )
        }),
    )

    readonly_fields = ['date_created','date_updated',]
    inlines = [CenterContentItemInline, LeftContentItemInline, MediaItemInline, TimelineInline, ActionInline, AdvocateInline, IssueChildrenInline]

    def save_model(self, request, obj, form, change):
        cache.bust(obj, update=False)
        super(self.__class__, self).save_model(request, obj, form, change)


admin.site.register(Issue,IssueAdmin)
