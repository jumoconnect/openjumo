from django.db import models
import datetime
from etc.entities import type_to_class, obj_to_type
from etc import cache
from collections import defaultdict, OrderedDict
from itertools import groupby
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Sections:
    HOME = 1
    SIGNED_IN_HOME = 2

class TopListItem(models.Model):
    id = models.AutoField(db_column='list_item_id', primary_key=True)
    list = models.ForeignKey('popularity.TopList', db_column='list_id')
    entity_content_type = models.ForeignKey(ContentType, db_column='entity_content_type',
                                            default=ContentType.objects.get(model="Issue").id,
                                            limit_choices_to={"model__in": ("Org", "Issue", "User"), "app_label__in": ("org", "issue", "users")})
    entity_type = models.CharField(max_length=50, db_column='entity_type')
    entity_id = models.PositiveIntegerField(db_column='entity_id')
    entity = generic.GenericForeignKey('entity_content_type', 'entity_id')
    rank = models.PositiveIntegerField(db_column='rank')
    date_created = models.DateTimeField(db_column='date_created', auto_now_add=True)
    last_modified = models.DateTimeField(db_column='last_modified', auto_now=True)

    class Meta:
        db_table = 'top_list_items'
        ordering = ['rank']

    def __unicode__(self):
        return u' - '.join([unicode(self.rank), unicode(self.entity)])

    def save(self):
        if not self.entity_type:
            self.entity_type=obj_to_type(self.entity)
        self.last_modified = datetime.datetime.utcnow()
        super(TopListItem, self).save()

class ListType(models.Model):
    id = models.AutoField(db_column='list_type_id', primary_key=True)
    name = models.CharField(max_length=75, db_column='name')

    class Meta:
        db_table = 'top_list_types'

    def __unicode__(self):
        return self.name

class TopList(models.Model):
    id = models.AutoField(db_column='list_id', primary_key=True)
    title = models.CharField(max_length=75, db_column='title')
    valid_from = models.DateField(db_column='valid_from', default=datetime.date.today)
    valid_to = models.DateField(db_column='valid_to', default=datetime.date(9999,12,31))
    is_current = models.BooleanField(db_column='is_current', default=True)
    section = models.ForeignKey('popularity.Section', db_column='section_id', null=True, blank=True, default=Sections.HOME)
    position = models.PositiveIntegerField(db_column='position', default=0)
    date_created = models.DateTimeField(db_column='date_created', auto_now_add=True)
    last_modified = models.DateTimeField(db_column='last_modified', auto_now=True)

    class Meta:
        db_table='top_lists'

    def __unicode__(self):
        return self.title

    def save(self):
        self.last_modified = datetime.datetime.utcnow()
        cache.bust(self)
        super(TopList, self).save()

    @classmethod
    def get(cls, id, force_db=False):
        if force_db:
            top_list = TopList.objects.get(id=id)
            cache.bust(top_list)
            return top_list
        return cache.get(cls, id)

    @classmethod
    def multiget(cls, ids, force_db=False):
        if force_db:
            return TopList.objects.filter(id__in=ids)
        return cache.get(cls, ids)

    @property
    @cache.collection_cache(TopListItem, '_list_item_ids')
    def get_items(self):
        return list(TopListItem.objects.filter(list=self).order_by('rank'))

    @classmethod
    def multiget_items(cls, ids):
        return TopListItem.objects.filter(list__in=ids).order_by('list', 'rank')

    @classmethod
    def get_entities_for_lists(cls, ids):
        """ This method actually returns the orgs, etc. for some lists """

        lists = TopList.multiget(ids)
        list_names = dict((l.id, l.title) for l in lists)

        # list of lists, return value
        top_lists = OrderedDict()
        
        # item_id => entity
        item_id_dict = {}
        entity_dict = {}

        list_id_dict = defaultdict(list)
        
        all_items=TopList.multiget_items(ids)
        # Spits out a dict like {1: [TopListItem(...), TopListItem(...)] }
        [list_id_dict[item.list_id].append(item) for item in all_items]

        keyfunc = lambda item: item.entity_content_type_id

        # Can potentially have hybrid featured lists,
        # so use groupby
        for entity_type, list_items in groupby(sorted(all_items, key=keyfunc), keyfunc):
            item_entity_dict = dict((i.id, i.entity_id) for i in list_items)
            
            cls = ContentType.objects.get(id=entity_type).model_class()            
            entities = cls.multiget(set(item_entity_dict.values()))
            for ent in entities:
                entity_dict[(entity_type, ent.id)] = ent
 
        for list_id in ids:
            entities = [entity_dict[(item.entity_content_type_id, item.entity_id)] for item in list_id_dict[list_id]]
            top_lists[list_names[list_id]] = entities

        return top_lists

class Section(models.Model):
    id = models.AutoField(db_column='section_id', primary_key=True)
    name = models.CharField(max_length=100, db_column='name')

    class Meta:
        db_table='sections'

    def __unicode__(self):
        return self.name

    @classmethod
    def get_lists(cls, id):
        return list(TopList.objects.filter(section=id, is_current=True).order_by('position'))
