from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group, User as DjangoUser
from django.contrib.sites.models import Site
from djcelery.models import TaskState, WorkerState, IntervalSchedule, CrontabSchedule, PeriodicTask
from etc import cache
from issue.models import UserToIssueFollow
from org.models import UserToOrgFollow
from users.models import User, UserToUserFollow, Location
from cust_admin.views.main import ExtChangeList


######## INLINES ########

class UserFollowingInline(admin.StackedInline):
    model = UserToUserFollow
    fk_name = "follower"
    extra = 0
    raw_id_fields = ('followed',)
    related_field_lookups = {
        'fk': ['followed']
    }
    verbose_name = "Followed Users"
    verbose_name_plural = "Followed Users"

class OrgFollowingInline(admin.StackedInline):
    model = UserToOrgFollow
    fk_name = "user"
    extra = 0
    raw_id_fields = ('org',)
    related_field_lookups = {
        'fk': ['org']
    }
    verbose_name = "Followed Org"
    verbose_name_plural = "Followed Orgs"

class IssueFollowingInline(admin.StackedInline):
    model = UserToIssueFollow
    fk_name = "user"
    extra = 0
    raw_id_fields = ('issue',)
    related_field_lookups = {
        'fk': ['issue']
    }
    verbose_name = "Followed Issue"
    verbose_name_plural = "Followed Issues"

######## MODEL FORM AND ADMIN ########

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        widgets = {
            'facebook_id' : forms.TextInput(attrs={'class':'vTextField'}),
        }

class UserAdmin(admin.ModelAdmin):
    form = UserForm

    #List Page Values
    search_fields = ['username','email', 'first_name', 'last_name']
    search_fields_verbose = ['Username', 'Email', 'First Name', 'Last Name']
    list_display = ('get_name', 'username', 'last_login','is_active', 'likely_org', 'org_probability', 'admin_classification')

    list_editable = ['admin_classification']
    list_filter = ('is_active', 'likely_org', 'admin_classification')
    ordering = ('username',)

    change_list_template = "cust_admin/change_list.html"

    raw_id_fields = ('location',)
    related_field_lookups = {
        'fk': ['location']
    }

    change_list_template = "cust_admin/change_list.html"

    def get_changelist(self, request, **kwargs):
        return ExtChangeList


    #Change Page Values
    fieldsets = (
      ('User Profile', {
        'fields': (
            ('username', 'is_active', 'is_superuser','is_staff'),
            ('first_name', 'last_name',),
            ('email',),
            ('date_joined', 'last_login',),
            'bio',
            'picture',
            ('url','blog_url',),
            'gender',
            'birth_year',
            'location',
        )}),
      ('Settings', {
        'fields':(('enable_jumo_updates',
                  'enable_followed_notification',
                  'email_stream_frequency',
                  'post_to_fb',),),
      }),
      ('Social Settings', {
        'fields':(
                    ('facebook_id','flickr_id','twitter_id',),
                    ('vimeo_id','youtube_id',),
                 )
      }),
      ("Extra Nonsense", {
        'classes': ('collapse closed',),
        'fields':('mongo_id','password','fb_access_token')
      }),
    )

    readonly_fields = ['mongo_id','fb_access_token','date_joined','last_login']
    inlines = [UserFollowingInline,OrgFollowingInline,IssueFollowingInline]

    def save_model(self, request, obj, form, change):
        cache.bust(obj, update=False)
        super(self.__class__, self).save_model(request, obj, form, change)


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location

class LocationAdmin(admin.ModelAdmin):
    form = LocationForm

    #List Page Values
    search_fields = ['locality', 'region', 'country_name', 'postal_code', 'raw_geodata', 'classification']
    search_fields_verbose = ['City', 'State', 'Country', 'ZIP code', 'Geodata', 'Classification']
    list_display = ('__unicode__', 'locality', 'region', 'country_name','postal_code', 'classification')

    list_editable = ['classification']

    def get_changelist(self, request, **kwargs):
        return ExtChangeList
    change_list_template = "cust_admin/change_list.html"


    #Change Page Values
    fieldsets = (
      ('Geography', {
        'fields': (
            ('__unicode__', 'locality', 'region', 'country_name','postal_code', 'classification'),
            )}
        ),
    )

    readonly_fields = ['__unicode__', 'locality', 'region', 'country_name','postal_code']

admin.site.unregister(Group)
admin.site.unregister(Site)
admin.site.unregister(DjangoUser)
admin.site.register(User, UserAdmin)
admin.site.register(Location, LocationAdmin)


# Unregister djcelery while we're at it

admin.site.unregister(TaskState)
admin.site.unregister(WorkerState)

admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(PeriodicTask)
