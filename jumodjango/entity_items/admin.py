from action.models import Action
from cust_admin.forms import HiddenRankModelForm
from cust_admin.models import LinkedGenericStackedInline
from cust_admin.widgets import ForeignKeyToObjWidget
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.generic import GenericTabularInline, GenericStackedInline
from entity_items.models import Advocate, ContentItem, MediaItem, TimelineItem



class MediaItemInlineForm(forms.ModelForm):
    class Meta:
        model = MediaItem
        widgets = {
            'position': forms.HiddenInput,
        }
    media_info = forms.CharField(widget = forms.Textarea(), required=False)

    def __init__(self, *args, **kwargs):
        super(MediaItemInlineForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            instance = kwargs.get('instance')
            if instance.media_type == MediaItem.MediaTypes.PULLQUOTE:
                self.fields['media_info'].initial = instance.get_pullquote
            elif instance.media_type == MediaItem.MediaTypes.VIDEO:
                self.fields['media_info'].initial = "http://www.youtube.com/watch?v=%s" % instance.get_youtube_id


    def save(self, force_insert=False, force_update=False, commit=True):
        model = super(MediaItemInlineForm, self).save(commit=False)
        if model.media_type == MediaItem.MediaTypes.PULLQUOTE:
            model.set_pullquote(self.cleaned_data["media_info"])
        elif model.media_type == MediaItem.MediaTypes.VIDEO:
            model.set_video_data(self.cleaned_data["media_info"])
        if commit:
            model.save()
        return model

class MediaItemInline(GenericStackedInline):
    model = MediaItem
    extra = 0
    classes = ('collapse closed',)
    form = MediaItemInlineForm
    fieldsets = (None, { 'fields': (
                    ('media_type', 'position',),
                    'img_url',
                    'thumbnail_url',
                    'media_info',
                    'caption','metadata',)}),

    sortable_field_name = 'position'
    def __init__(self, *args, **kwargs):
        super(MediaItemInline, self).__init__(*args, **kwargs)

class ActionInline(GenericTabularInline):
    model = Action
    form = HiddenRankModelForm
    extra = 0
    classes = ('collapse closed',)
    verbose_name = ""
    verbose_name_plural = "Actions"
    fields = ('title','link','type','rank')
    sortable_field_name = 'rank'


class AdvocateInline(GenericTabularInline):
    model = Advocate
    extra = 0
    classes = ('collapse closed',)
    verbose_name = "Advocate"
    verbose_name_plural = "Advocates"
    fieldsets = (None, {
        'fields': (('name', 'twitter_id', 'user',),)}),
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'user':
            kwargs['widget'] = ForeignKeyToObjWidget(rel=Advocate._meta.get_field('user').rel)
        return super(AdvocateInline,self).formfield_for_dbfield(db_field,**kwargs)


class TimelineInline(GenericStackedInline):
    model = TimelineItem
    extra = 0
    classes = ('collapse closed',)
    verbose_name = ""
    verbose_name_plural = "Timeline"


class DefaultContentItemInlineForm(forms.ModelForm):
    class Meta:
        model = ContentItem
        widgets = {'position':forms.HiddenInput}

    rich_text_body = forms.CharField(widget = forms.Textarea(attrs = {'class':'inlineEditor'}))

class DefaultContentItemInline(LinkedGenericStackedInline):
    model = ContentItem
    extra = 0
    classes = ('collapse closed',)
    sortable_field_name = 'position'
    fieldsets = (None, {
        'fields': (
            ('title', 'position', 'section',),
            'rich_text_body',)}),

    class Media:
        js = ['media/admin/tinymce/jscripts/tiny_mce/tiny_mce.js', 'media/admin/tinymce_setup/tinymce_setup.js']


class CenterContentItemInlineForm(DefaultContentItemInlineForm):
    section = forms.CharField(initial=ContentItem.ContentSection.CENTER, widget=forms.HiddenInput)

class CenterContentItemInline(DefaultContentItemInline):
    form = CenterContentItemInlineForm
    verbose_name = ""
    verbose_name_plural = "Center Content Items"
    def queryset(self, request):
        qs = super(CenterContentItemInline, self).queryset(request)
        return qs.filter(section = ContentItem.ContentSection.CENTER)


class LeftContentItemInlineForm(DefaultContentItemInlineForm):
    section = forms.CharField(initial=ContentItem.ContentSection.LEFT, widget=forms.HiddenInput)

class LeftContentItemInline(DefaultContentItemInline):
    form = LeftContentItemInlineForm
    verbose_name = ""
    verbose_name_plural = "Left Content Items"
    def queryset(self, request):
        qs = super(LeftContentItemInline, self).queryset(request)
        return qs.filter(section = ContentItem.ContentSection.LEFT)





class ContentItemForm(forms.ModelForm):
    class Meta:
        model = ContentItem
    rich_text_body = forms.CharField(widget = forms.Textarea(attrs = {'class':'mceEditor'}))

class ContentItemAdmin(admin.ModelAdmin):
    inlines = [MediaItemInline,]
    form = ContentItemForm
    fieldsets = (None, {
        'fields': (
            ('title', 'section',),
            'rich_text_body',)}),
    class Media:
        js = ['media/admin/tinymce/jscripts/tiny_mce/tiny_mce.js', 'media/admin/tinymce_setup/tinymce_setup.js']


admin.site.register(ContentItem, ContentItemAdmin)
