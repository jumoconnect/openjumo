from action.models import Action
from django.contrib.contenttypes import generic
from django.db import models
from entity_items.models import Advocate, ContentItem, MediaItem, TimelineItem
from etc import cache
from etc.templatetags.tags import _create_static_url
from lib.image_upload import ImageSize, ImageType, S3EnabledImageField
from users.models import User, Location
from commitment.models import Commitment

class Issue(models.Model):

    #Public Properties
    id = models.AutoField(db_column='issue_id', primary_key=True)
    name = models.CharField(max_length=50, unique=True, db_index = True)
    handle = models.CharField(max_length=60, unique=True, db_index = True)
    summary = models.CharField(max_length=255, blank=True)
    img_small_url = S3EnabledImageField(image_type=ImageType.ISSUE, image_size=ImageSize.SMALL, blank=True)
    img_large_url = S3EnabledImageField(image_type=ImageType.ISSUE, image_size=ImageSize.LARGE, blank=True)

    #Internal Properties
    is_active = models.BooleanField(default = True)
    content_upgraded = models.BooleanField(default = False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    #Relationship Properties
    content = generic.GenericRelation(ContentItem)
    actions = generic.GenericRelation(Action, related_name='issue_actions')
    advocates = generic.GenericRelation(Advocate)
    timeline = generic.GenericRelation(TimelineItem)
    media = generic.GenericRelation(MediaItem)
    location = models.ForeignKey(Location, null=True, blank=True)
    commitments = generic.GenericRelation(Commitment)

    #This is legacy property.  Old data still used but no new follows allowed.
    followers = models.ManyToManyField(User, related_name='followed_issues', through='UserToIssueFollow')
    children_issues = models.ManyToManyField('self', symmetrical = False, through='IssueRelation')

    class Meta:
        verbose_name = "Issue"
        verbose_name_plural = "Issues"
        db_table="issues"

    def __str__(self):
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
            super(Issue, self).save()
            self.img_large_url._committed = False
            self.img_small_url._committed = small_url_comm

        if not self.id and not self.img_small_url._committed:
            self.img_small_url._committed = True
            super(Issue, self).save()
            self.img_small_url._committed = False

        self.img_large_url.storage.inst_id = self.id
        self.img_small_url.storage.inst_id = self.id
        super(Issue, self).save()
        cache.bust(self)


    @models.permalink
    def get_absolute_url(self):
        return ('entity_url', [self.handle])

    @classmethod
    def get(cls, id, force_db=False):
        if force_db:
            issue = Issue.objects.get(id=id)
            cache.bust(issue)
            return issue
        return cache.get(cls, id)

    @classmethod
    def multiget(cls, ids, force_db=False):
        if force_db:
            return Issue.objects.filter(id__in=ids)
        return cache.get(cls, ids)


    @property
    def get_image_small(self):
        if self.img_small_url:
            return self.img_small_url.url
        return ''

    @property
    def get_image_large(self):
        if self.img_large_url:
            return self.img_large_url.url
        return ''

    @property
    def get_name(self):
        return self.name

    @property
    def get_url(self):
        return '/%s' % self.handle

    @property
    @cache.collection_cache('issue.Issue', '_get_related_geo_children')
    def get_related_geo_children(self):
        return [i.child for i in IssueRelation.objects.filter(parent=self, relation_type=IssueRelation.IssueRelationType.GEO)]

    @property
    @cache.collection_cache('issue.Issue', '_get_related_type_children')
    def get_related_type_children(self):
        return [i.child for i in IssueRelation.objects.filter(parent=self, relation_type=IssueRelation.IssueRelationType.TYPE)]

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
    def get_left_section_content(self):
        return [item for item in self.get_all_content if item.section == ContentItem.ContentSection.LEFT]

    @property
    def get_center_section_content(self):
        return [item for item in self.get_all_content if item.section == ContentItem.ContentSection.CENTER]

    @property
    @cache.collection_cache(User, '_all_followers')
    def get_all_followers(self):
        commitments = self.commitments.active().select_related()
        return [c.user for c in commitments]

    @property
    def get_all_followers_ids(self):
        return self.usertoissuefollow_set.filter(following = True).values_list('user', flat=True)

    @property
    def get_num_followers(self):
        return self.commitments.active().count()

    @property
    def get_sample_followers(self):
        commitments = self.commitments.active()[:16].select_related()
        return [c.user for c in commitments]

    @property
    @cache.collection_cache('org.Org', '_all_orgs_working_in')
    def get_all_orgs_working_in(self):
        return [rel.org for rel in OrgIssueRelationship.objects.filter(issue = self).order_by('-org__is_vetted')]

    @property
    def get_sample_orgs_working_in(self):
        from org.models import OrgIssueRelationship
        return [rel.org for rel in OrgIssueRelationship.objects.filter(issue = self).order_by('-org__is_vetted')[:3]]

    @property
    def get_all_orgs_working_in_ids(self):
        return OrgIssueRelationship.objects.filter(issue = self).order_by('-org__is_vetted').values_list('org', flat=True)

    def delete(self):
        cache.bust_on_handle(self, self.handle, False)
        return super(self.__class__, self).delete()


class UserToIssueFollow(models.Model):
    following = models.BooleanField(default = True, db_index = True)
    started_following = models.DateTimeField(auto_now_add = True)
    stopped_following = models.DateTimeField(blank = True, null = True)
    user = models.ForeignKey(User)
    issue = models.ForeignKey(Issue)

    class Meta:
        unique_together = (("user", "issue"),)

    def __unicode__(self):
        return "User '%s' following Issue '%s'" % (self.user, self.issue)


class IssueRelation(models.Model):
    class IssueRelationType:
        GEO = 'geo'
        TYPE = 'type'
    ISSUE_RELATION_TYPE_CHOICES = (
        (IssueRelationType.GEO, "Geo"),
        (IssueRelationType.TYPE, "Type"),
    )

    id = models.AutoField(db_column='issue_relation_id', primary_key=True)
    child = models.ForeignKey(Issue, related_name='child_issue')
    parent = models.ForeignKey(Issue, related_name='parent_issue')
    relation_type = models.CharField(max_length=100, choices=ISSUE_RELATION_TYPE_CHOICES, default=IssueRelationType.GEO)

    class Meta:
        db_table = 'issue_relations'
