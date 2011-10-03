from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from users.models import User

class Advocate(models.Model):
    id = models.AutoField(db_column='advocate_id', primary_key=True)
    content_type = models.ForeignKey(ContentType, limit_choices_to={"model__in": ("Org", "Issue")},
                                    default=ContentType.objects.get(model='issue').id)
    object_id = models.PositiveIntegerField()
    entity = generic.GenericForeignKey()
    user = models.ForeignKey(User, null=True, blank=True)
    name = models.CharField(max_length=200) #In the event they don't have a jumo user.
    twitter_id = models.CharField(blank = True, max_length = 32)
    url = models.URLField(verify_exists=False, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Advocate"
        verbose_name_plural = "Advocates"
        app_label = "entity_items"
        db_table="advocates"

    def __str__(self):
        if self.user:
            return str(self.user)
        else:
            return self.name
