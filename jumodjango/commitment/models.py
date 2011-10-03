from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from users.models import User
from etc.gfk_manager import GFKQuerySet
from utils.query_set import QuerySet
from etc import cache

class CommitmentQuerySet(QuerySet, GFKQuerySet):
    def active(self):
        return self.filter(user__is_active=True)

    def with_orgs(self):
        org_type = ContentType.objects.get(app_label='org', model='org')
        return self.filter(content_type=org_type)

    def with_issues(self):
        issue_type = ContentType.objects.get(app_label='issue', model='issue')
        return self.filter(content_type=issue_type)

class Commitment(models.Model):
    PENDING = 'pending'
    COMPLETED = 'completed'
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
    )

    id = models.AutoField(db_column='commitment_id', primary_key=True)
    user = models.ForeignKey(User, related_name='commitments')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    entity = generic.GenericForeignKey()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    goal_date = models.DateTimeField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    objects = CommitmentQuerySet.as_manager()

    class Meta:
        db_table = 'commitments'
        unique_together = ('user', 'content_type', 'object_id')

    def save(self, *args, **kwargs):
        super(Commitment, self).save(*args, **kwargs)
        cache.bust(self)

    def delete(self, *args, **kwargs):
        super(Commitment, self).delete(*args, **kwargs)
        cache.bust(self)
