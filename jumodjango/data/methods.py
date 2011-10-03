from django.utils.encoding import smart_str
from django.core.cache import cache
from django.db.models.base import ModelBase
from django.db import transaction

def _cache_key(cls, id):
  if type(cls) == ModelBase:
    prefix = cls.__name__
  else:
    prefix = cls.__class__.__name__
  return '%s%s' % (prefix, id)

def _get(cls, id):
  if type(cls) == ModelBase:
    if type(id) == list:
      return cls().objects.get(id__in = [str(l) for l in id])
    else:
      return cls().objects.get(id = str(id))
  else:
    if type(id) == list:
      return cls.__class__.base__().objects.get(id__in = [str(l) for l in id])
    else:
      return cls.__class__.base__().objects.get(id = str(id))

def get(cls, id):
  if getattr(cls, '_cacheable', False):
    c = cache.get(cache_key(cls, str(id)))
    if c is not None:
      return c
  return _get(cls, id)

def multiget(cls, ids):
  if len(ids) == 1:
    return [get(ids[0])]
  if getattr(cls, '_cacheable', False):


  else:
    return _get(cls, ids)

@transaction.autocommit
def update(model):
  model.save()
  if model._cacheable:
    cache.set(cache_key(model, model.id), model)
  return model

