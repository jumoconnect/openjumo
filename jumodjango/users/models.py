import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User as DjangoUser
from django.forms.models import model_to_dict
from etc import cache
from lib.image_upload import upload_user_image
from entity_items.models.location import Location
import Image
import json
from tastypie.models import ApiKey


GENDER_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),
)

EMAIL_FREQ_CHOICES = (
    (86400,"once a day",),
    (604800,"once a week",),
    (1209600,"once every 2 weeks"),
    (0,"never"),
)

AGE_GROUPS = (
    (0, 11),
    (12, 17),
    (18, 24),
    (25, 35),
    (36, 45),
    (46, 65),
    (66, 110),
)

USER_OR_ORG = (
    ('org', 'Org'),
    ('user', 'User')
)

# User model must have corresponding field named: <size_name>_img_url
#
# Use 0 to say there's no limit on dimension. If setting limits on
# dimensions, image resizing currently only works for a square
# or when a max-width is set.
# (aka the dimensions should either be (x,x) or (x,0))

USER_IMAGE_SIZES = {
    'orig': (0,0),
    'thumb': (50,50),
    'large': (161,0),
}

class User(DjangoUser):
    type = 'user'
    # acct info
    fb_access_token = models.CharField(max_length = 128, blank=True)

    #Because overriding the django user email field was insane
    long_email = models.EmailField(max_length=200, unique=True, verbose_name="email")

    # settings stuff
    enable_jumo_updates = models.BooleanField(default = True, verbose_name="Feature Notifications",
                                              help_text="Email me with new features and functionality")
    enable_followed_notification = models.BooleanField(default = True, verbose_name="Notifications",
                                                       help_text="Email me when someone starts following me on Jumo")
    email_stream_frequency = models.PositiveIntegerField(default = 604800, choices=EMAIL_FREQ_CHOICES, verbose_name="Jumo Reader",)
    post_to_fb = models.BooleanField(default = True, verbose_name="Facebook Posting",
                                     help_text="Allow Jumo to post updates to my Facebook account")

    # profiley stuff
    mongo_id = models.CharField(max_length=24, blank=True, db_index = True) #For all those old urls out in the wild right now.
    bio = models.TextField(blank = True)
    picture = models.CharField(max_length = 32, blank=True)
    url = models.URLField(verify_exists = False, blank=True, verbose_name="Website URL")
    blog_url = models.URLField(verify_exists = False, blank=True, verbose_name="Blog URL")
    gender = models.CharField(max_length="6", blank = True, choices = GENDER_CHOICES)
    birth_year = models.PositiveSmallIntegerField(blank = True, null = True, verbose_name='Year of Birth')
    location = models.ForeignKey(Location, blank=True, null=True)
    thumb_img_url = models.URLField(verify_exists=False, blank=True)
    large_img_url = models.URLField(verify_exists=False, blank=True)
    orig_img_url = models.URLField(verify_exists=False, blank=True)

    #Internal stuff
    next_email_time = models.DateField(blank = True, null = True, db_index = True)

    #social web crap
    facebook_id = models.BigIntegerField(blank = True, null=True, db_index = True)
    twitter_id = models.CharField(blank = True, max_length = 32, verbose_name="Twitter Username")
    flickr_id = models.CharField(blank = True, max_length = 32, verbose_name="Flickr Username")
    vimeo_id = models.CharField(blank = True, max_length = 32, verbose_name="Vimeo Username")
    youtube_id = models.CharField(blank = True, max_length = 32, verbose_name="Youtube Username")

    # Org profile detection
    likely_org = models.BooleanField(default=False, verbose_name = 'Is Likely Org')
    org_probability = models.FloatField(default = 0.0, verbose_name = "Probability (is Org)")
    admin_classification = models.CharField(max_length=30, blank=True, null=True, choices=USER_OR_ORG, verbose_name = "Admin Override (User or Org)")

    # relationships
    followers = models.ManyToManyField('self', through = 'UserToUserFollow', symmetrical = False, related_name = 'followings')

    # static vars for saving ourselves db lookups...
    _location = None

    # For distinguishing in templates between Donors and Jumo users
    is_jumo_user = True

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __unicode__(self):
        return unicode(self.username)

    def save(self):
        super(User, self).save()
        cache.bust(self)

    @models.permalink
    def get_absolute_url(self):
        return ('entity_url', [self.username])

    @classmethod
    def get(cls, id, force_db=False):
        if force_db:
            org = User.objects.get(id=id)
            cache.bust(org)
            return org
        return cache.get(cls, id)

    @classmethod
    def multiget(cls, ids, force_db=False):
        if force_db:
            return User.objects.filter(id__in=ids)
        return cache.get(cls, ids)

    @property
    def get_type(self):
        return self.type

    @property
    def get_url(self):
        return '/%s' % self.username

    @property
    def get_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def get_active_followers(self):
        return self.followers.filter(following_user__is_following=True)

    def get_active_followings(self):
        return self.followings.filter(followed_user__is_following=True)

    @property
    @cache.collection_cache('users.user', '_all_followers')
    def get_all_followers(self):
        return self.get_active_followers()

    @property
    def get_all_follower_ids(self):
        return self.followed_user.filter(is_following = True).values_list('follower_id', flat = True)

    @property
    def get_num_followers(self):
        return self.get_active_followers().count()

    @property
    @cache.collection_cache('users.user', '_sample_followers')
    def get_sample_followers(self):
        return self.get_active_followers()[:16]


    @property
    @cache.collection_cache('users.user', '_all_users_following')
    def get_all_users_following(self):
        return self.get_active_followings()

    @property
    def get_users_following_ids(self):
        return self.following_user.filter(is_following = True).values_list('followed_id', flat = True)

    @property
    def get_num_users_following(self):
        return self.get_active_followings().count()

    @property
    #@cache.collection_cache('users.user', '_sample_users_following')
    def get_sample_users_following(self):
        return self.get_active_followings()[:16]


    def get_num_org_commitments(self):
        return self.commitments.with_orgs().count()

    @property
    @cache.collection_cache('org.Org', '_all_orgs_following')
    def get_all_orgs_following(self):
        org_commitments = self.commitments.with_orgs().fetch_generic_relations()
        return [commitment.entity for commitment in org_commitments]

    @property
    def get_orgs_following_ids(self):
        return self.commitments.with_orgs().values_list('object_id', flat=True)

    @property
    @cache.collection_cache('org.Org', '_sample_orgs_following')
    def get_sample_orgs_following(self):
        org_commitments = self.commitments.with_orgs()[:5].fetch_generic_relations()
        return [commitment.entity for commitment in org_commitments]

    @property
    @cache.collection_cache('org.Org', '_recommended_orgs')
    def get_recommended_orgs(self):
        []
#        from org.models import Org
#        ids = list(set(Org.objects.filter(recommended = True).values_list('id', flat = True)).difference(self.get_orgs_following_ids))[0:5]
#        return Org.objects.filter(id__in = ids)


    @property
    @cache.collection_cache('issue.Issue', '_all_issues_following')
    def get_all_issues_following(self):
        issue_commitments = self.commitments.with_issues().fetch_generic_relations()
        return [commitment.entity for commitment in issue_commitments]

    @property
    def get_issues_following_ids(self):
        return self.usertoissuefollow_set.filter(following = True).values_list('issue_id', flat = True)

    @property
    @cache.collection_cache('issue.Issue', '_sample_issues_following')
    def get_sample_issues_following(self):
        issue_commitments = self.commitments.with_issues()[:5].fetch_generic_relations()
        return [commitment.entity for commitment in issue_commitments]

    @property
    @cache.collection_cache('org.Org', '_get_orgs_admin_of')
    def get_orgs_admin_of(self):
        from org.models import Org
        return [o.org for o in Org.admins.through.objects.filter(user=self)]


    @property
    def get_age_group(self):
        if self.birth_year:
            current_year = datetime.datetime.now().year
            age = int(current_year) - int(self.birth_year)
            if age > 1:
                for age_group in AGE_GROUPS:
                    if age >= age_group[0] and age <= age_group[1]:
                        return '%s-%s' % (str(age_group[0]), str(age_group[1]))
        return ''

    @property
    def get_api_key(self):
        try:
            key = ApiKey.objects.get(user=self)
            return key.key
        except:
            return None

    @property
    def get_location(self):
        if self._location is not None:
            return self._location
        self._location = self.location
        cache.put_on_handle(self, self.username)
        return self._location


    @property
    def get_image_small(self):
        if self.thumb_img_url:
            return self.thumb_img_url
        elif self.facebook_id:
            return 'http://graph.facebook.com/%s/picture?type=square' % self.facebook_id
        else:
            return '%s/static/img/missing_profile_photo_small.png' % settings.STATIC_URL

    @property
    def get_image_large(self):
        if self.large_img_url:
            return self.large_img_url
        elif self.facebook_id:
            return 'http://graph.facebook.com/%s/picture?type=large' % self.facebook_id
        else:
            return '%s/static/img/missing_profile_photo_large.png' % settings.STATIC_URL


    def delete(self):
        cache.bust_on_handle(self, self.username, False)
        return super(self.__class__, self).delete()

    def update_fb_follows(self, fb_ids, send_notifications=True):
        accounts = User.objects.filter(facebook_id__in = fb_ids)
        for acc in accounts:
            uuf, created = UserToUserFollow.objects.get_or_create(followed = acc, follower = self)
            if created:
                uuf.is_following = True
                uuf.save()
                cache.bust_on_handle(acc, acc.username)
                if acc.enable_followed_notification and send_notifications:
                    from mailer.notification_tasks import send_notification, EmailTypes
                    send_notification(type=EmailTypes.FOLLOW, user=acc, entity=self)

    def is_subscribed_to(self, pub_id):
        return len(self.subscriptions.filter(id=pub_id, subscription__subscribed=True).values_list('id')) > 0

    def upload_profile_pic(self, image):
        if not image:
            return
        opened_image = Image.open(image)
        for size_name, (w, h) in USER_IMAGE_SIZES.iteritems():
            (url, width, height) = upload_user_image(opened_image, self.id, size_name, w, h)
            setattr(self, '%s_img_url' % size_name, url)

    def generate_new_api_key(self):
        key, created = ApiKey.objects.get_or_create(user = self)
        if not created:
            #DON'T TRY AND CHANGE THE KEY VALUE.  DELETE INSTEAD
            key.delete()
            key = ApiKey(user = self)
        key.save()
        return key.key

class ActiveManager(models.Manager):
    def get_query_set(self):
        return super(ActiveManager, self).get_query_set().filter(is_following=True)

class UserToUserFollow(models.Model):
    is_following = models.BooleanField(default = True, db_index = True)
    started_following = models.DateTimeField(auto_now_add = True)
    stopped_following = models.DateTimeField(blank = True, null = True)
    followed = models.ForeignKey('User', related_name = 'followed_user')
    follower = models.ForeignKey('User', related_name = 'following_user')
    objects = models.Manager()
    actives = ActiveManager()

    class Meta:
        unique_together = (("followed", "follower"),)

    def __unicode__(self):
        return "User '%s' following User '%s'" % (self.follower, self.followed)


class PasswordResetRequest(models.Model):
    user = models.ForeignKey(User)
    uid = models.CharField(max_length = 36, db_index = True)
