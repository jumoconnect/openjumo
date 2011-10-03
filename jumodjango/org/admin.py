from django import forms
from django.contrib import admin
from etc import cache
from entity_items.admin import MediaItemInline, ActionInline, AdvocateInline, TimelineInline, CenterContentItemInline, LeftContentItemInline
from issue.models import Issue
from org.models import Org, RelatedOrg, OrgIssueRelationship, Alias
from users.models import User, Location
from cust_admin.views.main import ExtChangeList
from cust_admin.widgets import ForeignKeyToObjWidget

######## INLINES ########
class AliasInline(admin.TabularInline):
    model = Alias
    extra = 0
    classes = ('collapse closed',)
    verbose_name = "Alias"
    verbose_name_plural = "Aliases"

class AdminsInline(admin.TabularInline):
    model = Org.admins.through
    extra = 0
    classes = ('collapse closed',)
    related_field_lookups = {
        'fk': ['user']
    }
    verbose_name = "Admin"
    verbose_name_plural = "Admins"
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'user':
            kwargs['widget'] = ForeignKeyToObjWidget(rel=Org.admins.through._meta.get_field('user').rel)
        return super(AdminsInline,self).formfield_for_dbfield(db_field,**kwargs)

class IssuesInlineForm(forms.ModelForm):
    class Meta:
        model = Org.issues.through
        widgets = {'rank':forms.HiddenInput}

class IssuesInline(admin.TabularInline):
    model = Org.issues.through
    extra = 0
    form = IssuesInlineForm
    classes = ('collapse closed',)
    sortable_field_name = "rank"
    related_field_lookups = {
        'fk': ['issue']
    }
    verbose_name = ""
    verbose_name_plural = "Working On"
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'issue':
            kwargs['widget'] = ForeignKeyToObjWidget(rel=Org.issues.through._meta.get_field('issue').rel)
        return super(IssuesInline,self).formfield_for_dbfield(db_field,**kwargs)

class LocationsInline(admin.TabularInline):
    model = Org.working_locations.through
    extra = 0
    classes = ('collapse closed',)
    related_field_lookups = {
        'fk': ['location']
    }

    verbose_name = ''
    verbose_name_plural = 'Working In'
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'location':
            kwargs['widget'] = ForeignKeyToObjWidget(rel=Org.working_locations.through._meta.get_field('location').rel)
        return super(LocationsInline,self).formfield_for_dbfield(db_field,**kwargs)

######## MODEL FORM AND ADMIN ########

class OrgForm(forms.ModelForm):
    class Meta:
        model = Org
        widgets = {
            'location': ForeignKeyToObjWidget(rel=Org._meta.get_field('location').rel),
            'facebook_id' : forms.TextInput(attrs={'class':'vTextField'}),
            'summary': forms.Textarea(),
            }

    class Media:
        js = ['cust_admin/js/widgets.js']
        css = {'all':('cust_admin/css/extend_admin.css',)}


class OrgAdmin(admin.ModelAdmin):
    form = OrgForm

    #Org List Page Values
    search_fields = ['name','email', 'handle']
    search_fields_verbose = ['Name', 'Email']
    list_display = ('name', 'date_updated','is_active', 'is_vetted')
    list_filter = ('is_active',)
    ordering = ('name',)

    change_list_template = "cust_admin/change_list.html"

    def get_changelist(self, request, **kwargs):
        return ExtChangeList


    #Org Change Page Values
    fieldsets = (
      ('Org Profile', {
        'fields': (('name','handle',),
                   ('is_active', 'is_vetted', 'donation_enabled','is_claimed'),
                   ('email', 'ein',),
                   ('phone_number','year_founded','revenue','size',),
                   ('site_url', 'blog_url',),
                   'img_small_url', 'img_large_url','summary','location',
                   ('date_created','date_updated',),)
      }),
      ('Social Settings', {
        'fields':(
                    ('facebook_id', 'twitter_id', ),
                    ('youtube_id', 'flickr_id',),
                 )
      }),
      ("Extra Nonsense", {
        'classes': ('collapse closed',),
        'fields':('claim_token',),
      }),
    )

    readonly_fields = ['date_created','date_updated']
    inlines = [CenterContentItemInline, LeftContentItemInline, MediaItemInline, TimelineInline, ActionInline, AdvocateInline, AliasInline, AdminsInline, IssuesInline, LocationsInline, ]

    def save_model(self, request, obj, form, change):
        cache.bust(obj, update=False)
        super(self.__class__, self).save_model(request, obj, form, change)

admin.site.register(Org,OrgAdmin)
