from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from lib.image_upload import ImageSize, ImageType, S3EnabledImageField
from utils.regex_tools import youtube_url_magic
import json
from etc import cache

class MediaItem(models.Model):
    class MediaTypes:
        VIDEO = 'video'
        PHOTO = 'photo'
        PULLQUOTE = 'pullquote'

    MEDIA_TYPE_CHOICES = (
        (MediaTypes.VIDEO, 'Video'),
        (MediaTypes.PHOTO, 'Photo'),
        (MediaTypes.PULLQUOTE, 'Pullquote')
    )

    id = models.AutoField(db_column='media_item_id', primary_key=True)
    content_type = models.ForeignKey(ContentType, limit_choices_to={"model__in": ("Org", "Issue", "ContentItem")},
                                     default=ContentType.objects.get(model='issue').id)
    object_id = models.PositiveIntegerField()
    media_type = models.CharField(max_length=100, choices=MEDIA_TYPE_CHOICES)
    entity = generic.GenericForeignKey()
    caption = models.TextField(blank=True)
    img_url = S3EnabledImageField(image_type=ImageType.MEDIAITEM, image_size=ImageSize.LARGE, blank=True)
    thumbnail_url = S3EnabledImageField(image_type=ImageType.MEDIAITEM, image_size=ImageSize.SMALL, blank=True)
    position = models.PositiveIntegerField(default=0)
    metadata = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MediaItem"
        verbose_name_plural = "MediaItems"
        app_label = "entity_items"
        db_table="media_items"

    def __str__(self):
        return str(self.media_type)


    def save(self):
        #Note: I want to move all this img stuff to the forms that set them...
        #not here on the model. This is a hack so we ensure the model id is
        #used in the filename.
        if not self.id and not self.img_url._committed:
            #most likely you need to watch small img too
            thumbnail_url_comm = self.img_url._committed
            self.img_url._committed = True
            self.thumbnail_url._committed = True
            super(MediaItem, self).save()
            self.img_url._committed = False
            self.thumbnail_url._committed = thumbnail_url_comm

        if not self.id and not self.thumbnail_url._committed:
            self.thumbnail_url._committed = True
            super(MediaItem, self).save()
            self.thumbnail_url._committed = False

        self.img_url.storage.inst_id = self.id
        self.thumbnail_url.storage.inst_id = self.id
        super(MediaItem, self).save()
        cache.bust(self)

    @property
    def get_image_small(self):
        if self.thumbnail_url:
            return self.thumbnail_url.url
        return ''

    @property
    def get_image_large(self):
        if self.img_url:
            return self.img_url.url
        return ''


    def set_pullquote(self, value):
        if self.media_type == self.MediaTypes.PULLQUOTE:
            self.metadata = json.dumps({"quote_text" : value})

    def set_video_data(self, value):
        if self.media_type == self.MediaTypes.VIDEO:
            yt_data = youtube_url_magic(value)
            if yt_data:
                self.metadata = json.dumps(yt_data)
            else:
                self.metadata = ""

    @property
    def get_pullquote(self):
        result = ""
        if self.media_type == self.MediaTypes.PULLQUOTE:
            try:
                result = json.loads(self.metadata)["quote_text"]
            except Exception:
                pass
        return result

    @property
    def get_youtube_id(self):
        result = ""
        if self.media_type == self.MediaTypes.VIDEO:
            try:
                result = json.loads(self.metadata)["source_id"]
            except Exception:
                pass
        return result
