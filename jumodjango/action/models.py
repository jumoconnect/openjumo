from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

ACTION_TYPES = (
    ('link', 'Link'),
)

class Action(models.Model):
    id = models.AutoField(db_column='action_id', primary_key=True)
    title = models.CharField(max_length=255)
    link = models.URLField(verify_exists=False, blank=True)
    rank = models.PositiveIntegerField()
    type = models.CharField(max_length=25, choices=ACTION_TYPES, default=ACTION_TYPES[0][0])

    content_type = models.ForeignKey(ContentType, limit_choices_to={"model__in": ("Org", "Issue")},
                                    default=ContentType.objects.get(model='issue').id)
    object_id = models.PositiveIntegerField()
    entity = generic.GenericForeignKey()

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'actions'
        ordering = ('rank',)

    def __unicode__(self):
        return self.title
