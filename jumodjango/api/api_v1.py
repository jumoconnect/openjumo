from django.conf.urls.defaults import patterns
from django.conf import settings
from issue.models import Issue
from org.models import Org
from tastypie import fields
from tastypie.api import Api
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource
from tastypie.throttle import CacheDBThrottle
from users.models import User

class JumoModelResource(ModelResource):
    class Meta:
        authentication = ApiKeyAuthentication()
        throttle = CacheDBThrottle(throttle_at=3600, timeframe=3600)


class IssueResource(JumoModelResource):
    follower_count = fields.IntegerField('get_num_followers')
    img_thumb_url = fields.CharField('get_image')
    img_url = fields.CharField('get_image_large')
    parent_issue_id = fields.IntegerField('parent_issue_id')
    parent_issue_uri = fields.ForeignKey('self', 'parent_issue')
    stats = fields.ListField('get_all_statistics')
    url = fields.CharField('get_url')

    class Meta(JumoModelResource.Meta):
        queryset = Issue.objects.filter(is_active=True)

        allowed_methods = ['get']
        fields = ['date_created', 'date_updated', 'description', 'follower_count', 'handle', 'id', 'img_url',
                  'img_thumb_url', 'name', 'orgs', 'parent_issue_id', 'parent_issue_uri', 'stats', 'url']
        resource_name = 'issue'


class OrgResource(ModelResource):
    accomplishments = fields.ListField('get_accomplishments')
    follower_count = fields.IntegerField('get_num_followers')
    img_thumb_url = fields.CharField('get_image')
    img_url = fields.CharField('get_image_large')
    issues = fields.ToManyField(IssueResource, 'issues')
    location = fields.CharField('location', default='')
    methods = fields.ListField('get_all_methods')
    org_url = fields.CharField('url')
    related_orgs = fields.ToManyField('self', 'related_orgs')
    social_mission = fields.CharField('social_mission', default='')
    url = fields.CharField('get_url')
    working_locations = fields.ListField('get_working_locations')

    class Meta(JumoModelResource.Meta):
        queryset = Org.objects.filter(is_active=True)

        allowed_methods = ['get']
        fields = ['accomplishments', 'blog_url', 'date_created', 'date_updated', 'donation_enabled',
                  'ein', 'facebook_id', 'follower_count', 'handle', 'id', 'img_thumb_url', 'img_url',
                  'issues', 'location', 'methods', 'mission_statement', 'name', 'org_url', 'recommended',
                  'revenue', 'size', 'social_mission', 'twitter_id', 'url', 'vision_statement',
                  'working_locations', 'year_founded', 'youtube_id']
        resource_name = 'org'


class UserResource(ModelResource):
    badges = fields.ListField('get_badges')
    img_thumb_url = fields.CharField('get_image')
    img_url = fields.CharField('get_image_large')
    location = fields.CharField('location', default='')
    followed_issues = fields.ToManyField(IssueResource, 'usertoissuefollow_set')
    followed_orgs = fields.ToManyField(OrgResource, 'usertoorgfollow_set')
    followed_users = fields.ToManyField('self', 'followers')
    following_users = fields.ToManyField('self', 'following_user')
    user_url = fields.CharField('url')
    url = fields.CharField('get_url')

    class Meta(JumoModelResource.Meta):
        queryset = User.objects.filter(is_active=True)

        allowed_methods = ['get']
        fields = ['badges', 'bio', 'first_name', 'facebook_id', 'followed_issues', 'followed_orgs',
                  'followed_users', 'following_users', 'id', 'img_url', 'img_thumb_url',
                  'last_name', 'location', 'twitter_id', 'user_url', 'url', 'username', 'youtube_id']
        resource_name = 'user'



def api_urls():
    api = Api(api_name=settings.API_VERSION)
    api.register(IssueResource())
    api.register(OrgResource())
    api.register(UserResource())
    return api.urls
