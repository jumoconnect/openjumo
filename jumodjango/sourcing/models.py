from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from etc.func import crc32

# Create your models here.

class SourceTag(models.Model):
    id = models.AutoField(db_column='source_tag_id', primary_key=True)
    tag = models.CharField(db_column='tag', max_length=255, null=True)
    tag_crc32 = models.PositiveIntegerField(db_column='tag_crc32')
    is_active = models.BooleanField(db_column='is_active', default=False)

    class Meta:
        db_table='source_tags'


class SourceTaggedItem(models.Model):
    id = models.AutoField(db_column='source_tagged_item_id', primary_key=True)
    item_type = models.ForeignKey(ContentType, db_column='item_type', null=True)
    item_id = models.PositiveIntegerField(db_column='item_id', null=True)
    object = generic.GenericForeignKey('item_type', 'item_id')
    tag = models.ForeignKey(SourceTag, db_column='tag_id', related_name='tags')

    class Meta:
        db_table = 'source_tagged_items'

    @classmethod
    def create(cls, obj, tag):
        tag, created = SourceTag.objects.get_or_create(tag=tag,
                                                       tag_crc32=crc32(tag))
        tagged_item = SourceTaggedItem(object=obj,
                                       tag=tag)
        tagged_item.save()
        return tagged_item