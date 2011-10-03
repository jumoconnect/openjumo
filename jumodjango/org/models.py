from action.models import Action
from django.conf import settings
from django.contrib.contenttypes import generic
from django.db import models
from entity_items.models import Advocate, ContentItem, MediaItem, TimelineItem
from entity_items.models.location import Location
from etc import cache
from etc.templatetags.tags import _create_static_url
from issue.models import Issue
from lib.image_upload import ImageSize, ImageType, S3EnabledImageField
from users.models import User
from commitment.models import Commitment

REVENUE_CHOICES = (
    ("less than $100,000","less than $100,000",),
    ("$100,000 - $1,000,000","$100,000 - $1,000,000",),
    ("$1m - $5m","$1m - $5m",),
    ("$5m - $20m","$5m - $20m",),
    ("more than $20m","more than $20m",),
)

SIZE_CHOICES = (
    ("1-10","1-10"),
    ("10-50","10-50",),
    ("51-100","51-100",),
    ("100+","100+",),
)

class Org(models.Model):

    #Public Properties
    id = models.AutoField(db_column='org_id', primary_key=True)
    name = models.CharField(max_length=200, verbose_name="Organization Name")
    summary = models.CharField(max_length=255, verbose_name="Vision Statement")
    handle = models.CharField(max_length=210, unique=True, verbose_name="Organization Handle",
                help_text="Your organization's unique handle used for your public Jumo page: www.jumo.com/<b>HANDLE</b>")
    ein = models.CharField(max_length=12, blank=True, verbose_name="EIN",
            help_text="*Not required, but must be provided for 501(c)(3)'s that wish to receive donations on Jumo. Find your organization's EIN <a target='_blank' href='http://nccsdataweb.urban.org/PubApps/990search.php?a=a&bmf=1'>here</a>.")
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=50, blank=True, verbose_name="Phone")
    img_small_url = S3EnabledImageField(image_type=ImageType.ORG, image_size=ImageSize.SMALL, blank=True)
    img_large_url = S3EnabledImageField(image_type=ImageType.ORG, image_size=ImageSize.LARGE, blank=True)
    year_founded = models.IntegerField(max_length=4, blank=True, null=True, verbose_name="Year Founded")
    revenue = models.CharField(max_length=32, blank=True, choices=REVENUE_CHOICES, verbose_name="Revenue Size")
    size = models.CharField(max_length=32, blank=True, choices=SIZE_CHOICES, verbose_name="# of Employees")
    blog_url = models.URLField(verify_exists = False, blank=True, verbose_name="Blog")
    site_url = models.URLField(verify_exists = False, blank=True, verbose_name="Website")
    facebook_id = models.BigIntegerField(max_length=41, blank=True, null=True, verbose_name="Facebook ID")
    twitter_id = models.CharField(max_length=64, blank=True, verbose_name="Twitter Username")
    youtube_id = models.CharField(max_length=64, blank=True, verbose_name="YouTube Username")
    flickr_id = models.CharField(max_length=64, blank=True, verbose_name="Flickr Username")
    location = models.ForeignKey(Location, null=True, blank=True, related_name='location', verbose_name="Headquarters")

    #Internal Properties
    is_vetted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, verbose_name="Is Active") #Replaces the old ignore field.
    donation_enabled = models.BooleanField(default=False, verbose_name="Is Donation Enabled")
    claim_token = models.CharField(max_length = 32, blank = True, verbose_name="Claim Token")
    is_claimed = models.BooleanField(default=False, verbose_name="Is Claimed")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    date_updated = models.DateTimeField(auto_now=True, verbose_name="Date Updated")

    facebook_last_fetched = models.CharField(max_length=24, null=True, blank=True, default=None, verbose_name='Facebook Last Fetched')
    twitter_last_status_id = models.BigIntegerField(null=True, verbose_name='Twitter Last Status ID')

    #Relationship Properties
    admins = models.ManyToManyField(User, related_name = 'admins', db_table='org_org_admins')
    content = generic.GenericRelation(ContentItem, related_name='content')
    actions = generic.GenericRelation(Action, related_name='org_actions')
    advocates = generic.GenericRelation(Advocate, related_name='advocates')
    timeline = generic.GenericRelation(TimelineItem, related_name='timeline')
    media = generic.GenericRelation(MediaItem, related_name='media')
    followers = models.ManyToManyField(User, symmetrical=False, through='UserToOrgFollow', related_name='followed_orgs')
    related_orgs = models.ManyToManyField('self', symmetrical = False, through='RelatedOrg', related_name="orgrelatedorgs")
    working_locations = models.ManyToManyField(Location, null=True, symmetrical=False, related_name="working_locations",
                                               db_table="org_working_locations", verbose_name="Working In")
    issues = models.ManyToManyField(Issue, through='OrgIssueRelationship', verbose_name="Working On")
    commitments = generic.GenericRelation(Commitment)
    #aliases

    class Meta:
        verbose_name = "Org"
        verbose_name_plural = "Orgs"
        db_table = "orgs"

    def __unicode__(self):
        return self.name

    def save(self):
        #Note: I want to move all this img stuff to the forms that set them...
        #not here on the model. This is a hack so we ensure the model id is
        #used in the filename.
        if not self.id and not self.img_large_url._committed:
            #most likely you need to watch small img too
            small_url_comm = self.img_url._committed
            self.img_small_url._committed = True
            self.img_large_url._committed = True
            super(Org, self).save()
            self.img_large_url._committed = False
            self.img_small_url._committed = small_url_comm

        if not self.id and not self.img_small_url._committed:
            self.img_small_url._committed = True
            super(Org, self).save()
            self.img_small_url._committed = False

        self.img_large_url.storage.inst_id = self.id
        self.img_small_url.storage.inst_id = self.id
        super(Org, self).save()
        cache.bust(self)

    @models.permalink
    def get_absolute_url(self):
        return ('entity_url', [self.handle])

    @classmethod
    def get(cls, id, force_db=False):
        if force_db:
            org = Org.objects.get(id=id)
            cache.bust(org)
            return org
        return cache.get(cls, id)

    @classmethod
    def multiget(cls, ids, force_db=False):
        if force_db:
            return Org.objects.filter(id__in=ids)
        return cache.get(cls, ids)

    @property
    def get_image_small(self):
        if self.img_small_url:
            return self.img_small_url.url
        if self.facebook_id:
            return 'http://graph.facebook.com/%s/picture?type=square' % self.facebook_id
        return ''

    @property
    def get_image_large(self):
        if self.img_large_url:
            return self.img_large_url.url
        if self.facebook_id:
            return 'http://graph.facebook.com/%s/picture?type=large' % self.facebook_id
        return ''

    @property
    def get_url(self):
        return '/%s' % self.handle

    @property
    def get_name(self):
        return self.name

    @property
    @cache.collection_cache(Action, '_all_actions')
    def get_all_actions(self):
        return self.actions.all().order_by('rank')

    @property
    @cache.collection_cache(Advocate, '_all_advocates')
    def get_all_advocates(self):
        return self.advocates.all()

    @property
    @cache.collection_cache(TimelineItem, '_all_timeline_items')
    def get_all_timeline_items(self):
        return self.timeline.all().order_by('year')

    @property
    @cache.collection_cache(MediaItem, '_all_media_items')
    def get_all_media_items(self):
        return self.media.all().order_by('position')

    @property
    @cache.collection_cache(MediaItem, '_photo_media_items')
    def get_all_photos(self):
        return self.media.filter(media_type="photo").order_by('position')

    @property
    @cache.collection_cache(ContentItem, '_all_content')
    def get_all_content(self):
        return self.content.all().order_by('position')

    @property
    def get_sub_heading_text(self):
        t = ""
        if self.year_founded:
            t += "Since %s" % self.year_founded

        if self.get_location:
            if self.year_founded:
                t += " // "
            print t
            t += str(self.get_location)
            print t

        if self.size:
            if self.year_founded or self.get_location:
                t += " // "
            t += "%s employees" % self.size

        if self.revenue:
            if self.year_founded or self.size or self.get_location:
                t += " // "
            t += "%s revenue" % self.revenue

        if self.site_url:
            if self.year_founded or self.revenue or self.get_location or self.size:
                t += " // "
            t += self.site_url

        return t

    @property
    def get_left_section_content(self):
        return [item for item in self.get_all_content if item.section == ContentItem.ContentSection.LEFT]

    @property
    def get_center_section_content(self):
        return [item for item in self.get_all_content if item.section == ContentItem.ContentSection.CENTER]

    _location = None
    @property
    def get_location(self):
        if self._location is not None:
            return self._location
        self._location = self.location
        cache.put_on_handle(self, self.handle)
        return self._location

    @property
    @cache.collection_cache(Location, '_working_locations')
    def get_working_locations(self):
        return self.working_locations.all()

    @property
    @cache.collection_cache(User, '_admins')
    def get_admins(self):
        return self.admins.all()

    @property
    @cache.collection_cache(User, '_all_followers')
    def get_all_followers(self):
        commitments = self.commitments.active().select_related()
        return [c.user for c in commitments]

    @property
    def get_all_follower_ids(self):
        return self.usertoorgfollow_set.filter(following = True).values_list('user', flat=True)

    @property
    def get_num_followers(self):
        return self.commitments.active().count()

    @property
    def get_sample_followers(self):
        commitments = self.commitments.active()[:16].select_related()
        return [c.user for c in commitments]

    @property
    @cache.collection_cache(Issue, '_all_issues')
    def get_all_issues(self):
        return Issue.objects.filter(id__in = self.get_all_issues_ids)

    @property
    def get_all_issues_ids(self):
        return self.orgissuerelationship_set.values_list('issue', flat = True)

    @property
    @cache.collection_cache('org.Org', '_all_related_orgs')
    def get_all_related_orgs(self):
        return self.related_orgs.all()

    def get_related_orgs_for_user(self, user):
        if not hasattr(self, '_all_related_orgs') or getattr(self, '_all_related_orgs') is None:
            self.get_all_related_orgs
        pos = dict((id, idx) for idx, id in enumerate(self._all_related_orgs['ids']))
        orgs = sorted(list(set(self._all_related_orgs['ids']).difference(user.get_orgs_following_ids)), key=lambda id: pos[id])
        return list(cache.get(Org, orgs[0:5]))

    def delete(self):
        cache.bust_on_handle(self, self.handle, False)
        return super(self.__class__, self).delete()

    def is_editable_by(self, user):
        return not self.is_vetted and (user.is_staff or user in self.admins.all())

class Alias(models.Model):
    """
    Another name an org might be known as.
    """
    org = models.ForeignKey(Org)
    alias = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    date_updated = models.DateTimeField(auto_now=True, verbose_name="Date Updated")

    class Meta:
        unique_together = (("org", "alias"),)
        db_table = 'org_alias'

    def __unicode__(self):
        return self.alias

class UserToOrgFollow(models.Model):
    following = models.BooleanField(default = True, db_index = True)
    started_following = models.DateTimeField(auto_now_add = True)
    stopped_following = models.DateTimeField(blank = True, null = True)
    user = models.ForeignKey(User)
    org = models.ForeignKey(Org)

    class Meta:
        unique_together = (("user", "org"),)
        verbose_name = "User Following Org"
        verbose_name = "Users Following Orgs"
        db_table = 'org_usertoorgfollow'

    def __unicode__(self):
        return "User '%s' following Org '%s'" % (self.user, self.org)


class RelatedOrg(models.Model):
    org = models.ForeignKey(Org, related_name="org")
    related_org = models.ForeignKey(Org, related_name="related_org")
    rank = models.FloatField()  #Value determined by magic algo that generated this item.
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    date_updated = models.DateTimeField(auto_now=True, verbose_name="Date Updated")

    class Meta:
        db_table = 'related_orgs'
        ordering = ['rank']
        unique_together = (("org", "rank"),)
        verbose_name = "Org's Related Org"
        verbose_name_plural = "Org's Related Orgs"


    def __unicode__(self):
        return "%s" % self.related_org

class OrgIssueRelationship(models.Model):
    org = models.ForeignKey(Org)
    issue = models.ForeignKey(Issue)
    rank = models.IntegerField(default=0) #This is manually managed for each org:issues relations.
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    date_updated = models.DateTimeField(auto_now=True, verbose_name="Date Updated")

    class Meta:
        ordering = ['rank']
        unique_together = (("org", "issue"),)
        verbose_name = "Org's Issue"
        verbose_name_plural = "Org's Issues"
        db_table = 'org_orgissuerelationship'

    def __unicode__(self):
        return "%s" % self.issue
