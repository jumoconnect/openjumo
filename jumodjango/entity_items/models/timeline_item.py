from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from etc import cache

class TimelineItem(models.Model):
    id = models.AutoField(db_column='timeline_item_id', primary_key=True)
    content_type = models.ForeignKey(ContentType, limit_choices_to={"model__in": ("Org", "Issue")},
                                    default=ContentType.objects.get(model='issue').id)
    object_id = models.PositiveIntegerField()
    entity = generic.GenericForeignKey()
    year = models.IntegerField(max_length=4)
    description = models.TextField(null=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "TimelineItem"
        verbose_name_plural = "TimelineItems"
        app_label = "entity_items"
        db_table="timeline_items"

    def save(self, *args, **kwargs):
        super(TimelineItem, self).save(*args, **kwargs)
        cache.bust(self)

    def __str__(self):
        return str(self.year)
