from django import forms
from etc.entities import create_handle
from entity_items.models import ContentItem
from org.models import Org, OrgIssueRelationship
from issue.models import Issue
from users.models import Location
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from utils.widgets import MultipleLocationWidget, LocationWidget
import json

class OrgForm(forms.ModelForm):
    class Meta:
        model = Org
        widgets = {
            'location': LocationWidget(),
            'working_locations': MultipleLocationWidget(),
            'facebook_id': forms.TextInput(attrs={'placeholder':1234567890}),
            'site_url': forms.TextInput(attrs={'placeholder':'http://www.your.org'}),
            'email': forms.TextInput(attrs={'placeholder':'example@your.org'}),
            'phone_number': forms.TextInput(attrs={'placeholder':'(555) 555-5555'}),
            'twitter_id': forms.TextInput(attrs={'placeholder':'yourorg'}),
            'blog_url': forms.TextInput(attrs={'placeholder':'http://your.org/blog'}),
            'youtube_id': forms.TextInput(attrs={'placeholder':'yourorg'}),
            'flickr_id': forms.TextInput(attrs={'placeholder':'yourorg'}),
            'summary': forms.Textarea(attrs={'placeholder': 'Describe the organization\'s vision.'}),
        }

    class Media:
        css = {
            'all':['css/admin/widgets.css',]
        }
        js = ['/admin/jsi18n/',]

    def __init__(self, *args, **kwargs):
        super(OrgForm, self).__init__(*args, **kwargs)
        if 'working_locations' in self.fields:
            self.fields['working_locations'].help_text = ''
        if 'issues' in self.fields:
            self.fields['issues'].widget = FilteredSelectMultiple('Issues', False)
            self.fields['issues'].queryset = Issue.objects.order_by('name')
            self.fields['issues'].help_text = ''

    def save(self, commit=True):
        instance = super(OrgForm, self).save(commit=False)
        if 'issues' in self.fields:
            old_issues = instance.issues.all()
            new_issues = self.cleaned_data['issues']
            to_delete = set(old_issues) - set(new_issues)
            to_create = set(new_issues) - set(old_issues)

            OrgIssueRelationship.objects.filter(org=instance, issue__in=to_delete).delete()
            for issue in to_create:
                relationship = OrgIssueRelationship(org=instance, issue=issue)
                try:
                    relationship.full_clean()
                    relationship.save()
                except ValidationError, e:
                    pass
            del(self.cleaned_data['issues'])
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class ManageOrgForm(OrgForm):
    mission = forms.CharField(label="Mission Statement", widget=forms.Textarea)

    class Meta(OrgForm.Meta):
        fields = ['name', 'handle', 'ein', 'location', 'summary', 'mission', 'issues', 'working_locations']

    def __init__(self, *args, **kwargs):
        super(ManageOrgForm, self).__init__(*args, **kwargs)
        try:
            content_item = self.instance.content.center().mission_statement()
            self.fields['mission'].initial = content_item.rich_text_body
        except ContentItem.DoesNotExist:
            pass

    def save(self, commit=True):
        instance = super(ManageOrgForm, self).save(False)
        try:
            content_item = instance.content.center().mission_statement()
        except ContentItem.DoesNotExist:
            content_item = ContentItem(entity=instance, section=ContentItem.ContentSection.CENTER, title=ContentItem.MISSION_STATEMENT)
        content_item.rich_text_body = self.cleaned_data['mission']
        content_item.save()

        if commit:
            instance.save()
            self.save_m2m()
        return instance

class ManageOrgConnectForm(OrgForm):
    class Meta(OrgForm.Meta):
        fields = ['facebook_id', 'site_url', 'email', 'phone_number', 'twitter_id',
                  'blog_url', 'youtube_id', 'flickr_id',]

class ManageOrgMoreForm(OrgForm):
    class Meta(OrgForm.Meta):
        fields = ['img_large_url', 'size', 'revenue', 'year_founded']

    def save(self, commit=True):
        from django.core.files.uploadedfile import InMemoryUploadedFile
        instance = super(ManageOrgMoreForm, self).save(False)
        if isinstance(self.cleaned_data['img_large_url'], InMemoryUploadedFile):
            instance.img_small_url = self.cleaned_data['img_large_url']

        if commit:
            instance.save()
            self.save_m2m()
        return instance

    def __init__(self, *args, **kwargs):
        super(ManageOrgMoreForm, self).__init__(*args, **kwargs)
        self.fields['img_large_url'].label = 'Image'

class CreateOrgForm(OrgForm):
    YES = 'yes'
    SOCIAL_MISSION_CHOICES = ((YES, 'Yes'), ('no', 'No'))

    social_mission = forms.ChoiceField(choices=SOCIAL_MISSION_CHOICES, widget=forms.RadioSelect)

    class Meta(OrgForm.Meta):
        fields = ['name', 'summary']

    def save(self, commit=True):
        instance = super(CreateOrgForm, self).save(False)
        instance.handle = create_handle(instance.name)

        if commit:
            instance.save()
            self.save_m2m()
        return instance

    def clean_social_mission(self):
        data = self.cleaned_data['social_mission']
        if data != self.YES:
            raise forms.ValidationError('''We appreciate your interest in Jumo. Unfortunately we cannot
                accept your organization on the platform. Jumo is a registered
                501(c)(3) and accepting organizations that are not mission-driven
                could violate our IRS status.''')
        return data

class DetailsOrgForm(OrgForm):
    class Meta(OrgForm.Meta):
        fields = ['working_locations', 'issues', 'facebook_id', 'twitter_id']

    def __init__(self, *args, **kwargs):
        super(DetailsOrgForm, self).__init__(*args, **kwargs)
        self.fields['working_locations'].help_text = "Please enter the cities or countries in which you work."
        self.fields['issues'].help_text = "Please choose up to six issues your organization works on."
