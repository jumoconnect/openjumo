from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.html import strip_tags
from entity_items.models import MediaItem
from etc import cache
from utils.query_set import QuerySet

class ContentItemQS(QuerySet):
    def center(self):
        return self.filter(section=ContentItem.ContentSection.CENTER)

    def left(self):
        return self.filter(section=ContentItem.ContentSection.LEFT)

    def mission_statement(self):
        return self.get(title=ContentItem.MISSION_STATEMENT)

class ContentItem(models.Model):
    class ContentSection:
        LEFT = 'left'
        CENTER = 'center'

    MISSION_STATEMENT = 'Mission Statement'

    CONTENT_SECTION_CHOICES = (
        (ContentSection.LEFT, "Left"),
        (ContentSection.CENTER, "Center"),
    )

    id = models.AutoField(db_column='content_item_id', primary_key=True)
    content_type = models.ForeignKey(ContentType, limit_choices_to={"model__in": ("Org", "Issue")},
                                    default=ContentType.objects.get(model='issue').id)
    object_id = models.PositiveIntegerField()
    entity = generic.GenericForeignKey()
    section = models.CharField(max_length=100, choices=CONTENT_SECTION_CHOICES, default=ContentSection.CENTER)
    position = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    rich_text_body = models.TextField(blank=True)
    media_item = generic.GenericRelation(MediaItem)

    objects = ContentItemQS.as_manager()

    class Meta:
        verbose_name = "ContentItem"
        verbose_name_plural = "ContentItems"
        app_label = "entity_items"
        db_table = "content_items"
        ordering = ["position"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.body = strip_tags(self.rich_text_body)
        super(ContentItem, self).save(*args, **kwargs)
        cache.bust(self)


    @property
    def get_media_item(self):
        #Faking singular media item for possible future changes.
        media_items = self.media_item.all()
        return media_items[0] if media_items else None;

    def set_media_item(self, value):
        #Faking singular media item for possible future changes.
        self.media_item.clear()
        self.media_item.add(value)
