from django.db.models import Manager
from django.db.models.query import QuerySet
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey

# Adapted from django snippet 1773: http://djangosnippets.org/snippets/1773/
# Use this manager to eager load generic relations in 1 batch per content type (rather than n+1)
# Example: Model.objects.filter(...).fetch_generic_relations()

class GFKManager(Manager):
    def get_query_set(self):
        return GFKQuerySet(self.model)

class GFKQuerySet(QuerySet):
    def fetch_generic_relations(self):
        qs = self._clone()

        gfk_fields = [g for g in self.model._meta.virtual_fields if isinstance(g, GenericForeignKey)]

        ct_map = {}
        item_map = {}
        data_map = {}

        for item in qs:
            for gfk in gfk_fields:
                ct_id_field = self.model._meta.get_field(gfk.ct_field).column
                ct_id = getattr(item, ct_id_field)
                obj_id = getattr(item, gfk.fk_field)
                ct_map.setdefault(ct_id, []).append(obj_id)
            item_map[item.id] = item

        for ct_id, obj_ids in ct_map.iteritems():
            if ct_id:
                ct = ContentType.objects.get_for_id(ct_id)
                for o in ct.model_class().objects.select_related().filter(id__in=obj_ids).all():
                    data_map[(ct_id, o.id)] = o

        for item in qs:
            for gfk in gfk_fields:
                obj_id = getattr(item, gfk.fk_field)
                if obj_id != None:
                    ct_id_field = self.model._meta.get_field(gfk.ct_field).column
                    ct_id = getattr(item, ct_id_field)
                    setattr(item, gfk.name, data_map[(ct_id, obj_id)])

        return qs
