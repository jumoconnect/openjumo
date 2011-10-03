from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from etc.gfk_manager import GFKManager

class TopCategory(models.Model):
    id = models.AutoField(db_column='top_category_id', primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    rank = models.PositiveIntegerField()

    class Meta:
        db_table = 'top_categories'
        verbose_name_plural = 'top categories'

    def __unicode__(self):
        return self.name

    def sub_category_count(self):
        return self.subcategory_set.count()

class SubCategory(models.Model):
    id = models.AutoField(db_column='sub_category_id', primary_key=True)
    name = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey(TopCategory, db_column='top_category_id')
    rank = models.PositiveIntegerField()

    class Meta:
        db_table = 'sub_categories'
        verbose_name_plural = 'sub categories'
        ordering = ['rank']

    def discovery_item_count(self):
        return self.discoveryitem_set.count()
    discovery_item_count.__name__ = 'Item Count'

class DiscoveryItem(models.Model):
    CONTENT_TYPE_CHOICES = (
        ContentType.objects.get(app_label='org', model='org').id,
        ContentType.objects.get(app_label='issue', model='issue').id,
    )

    id = models.AutoField(db_column='discovery_item_id', primary_key=True)
    parent = models.ForeignKey(SubCategory, db_column='sub_category_id')
    content_type = models.ForeignKey(ContentType, limit_choices_to={'id__in': CONTENT_TYPE_CHOICES},
                                     default=CONTENT_TYPE_CHOICES[0], related_name='content_type')
    object_id = models.PositiveIntegerField()
    entity = generic.GenericForeignKey()
    rank = models.PositiveIntegerField()

    objects = GFKManager()

    class Meta:
        db_table = 'discovery_items'
        ordering = ['rank']

class DiscoveryMap(object):
    @classmethod
    def get_map(cls):
        map = {}

        ''' Assumes all top categories and sub categories that we want displayed
            will have discovery items '''
        items = DiscoveryItem.objects.all().order_by('rank').select_related().fetch_generic_relations()
        for item in items:
            sub_category = item.parent
            top_category = sub_category.parent
            map.setdefault(top_category, {}).setdefault(sub_category, []).append(item)
        return map

    @classmethod
    def get_lists(cls):
        discovery_map = cls.get_map()
        top_categories = sorted(discovery_map.keys(), key=lambda tc: tc.rank)
        sub_category_groups = []
        discovery_item_groups = []
        for top_category, sub_category_map in discovery_map.iteritems():
            sorted_sub_cats = sorted(sub_category_map.keys(), key=lambda sc: sc.rank)
            sub_category_groups.append((sorted_sub_cats, top_category))
            for sub_category, discovery_items in sub_category_map.iteritems():
                discovery_item_groups.append((discovery_items, top_category, sub_category))

        # Sort sub category groups by ranking of parent
        sub_category_groups = sorted(sub_category_groups, key=lambda group: group[1].rank)
        # Sort discovery item groups by ranking of top_category first, and then sub_category
        discovery_item_groups = sorted(discovery_item_groups, key=lambda group: 10*group[1].rank+group[2].rank)

        return top_categories, sub_category_groups, discovery_item_groups
