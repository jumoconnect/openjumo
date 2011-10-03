from collections import namedtuple
from django.core.cache import cache
from django.db.models.query import ValuesListQuerySet
from django.db.models.loading import get_model
from itertools import groupby


_process_cache = {}

def _cache_key(obj, id = None):
    class_name = obj.__name__ if hasattr(obj, "__name__") else obj.__class__.__name__
    if id is None:
        id = obj.id
    return '%s_%s' % (class_name, id)

TypedId = namedtuple('TypedId', 'cls,id')

def _split_cache_key(key):
    return TypedId(key.split('_'))

def put(obj):
    if type(obj) == list:
        cache.set_many(dict(zip([_cache_key(o) for o in obj], [o for o in obj])))
        for o in obj:
            _process_cache[_cache_key(o)] = obj
    else:
        cache.set(_cache_key(obj), obj)
        _process_cache[_cache_key(obj)] = obj

def get(cls, id, using_db=None):
    if type(id) == ValuesListQuerySet:
        id = list(id)
    if hasattr(id, '__iter__'):
        _pcresult = []
        for i in id:
            pcr = _process_cache.get(_cache_key(cls, i))
            if pcr is not None:
                _pcresult.append(pcr)

        if len(_pcresult) == len(id):
            return _pcresult

        _mcresult = cache.get_many([_cache_key(cls, i) for i in id])
        if len(_mcresult) == len(id):
            mc_result = map(lambda t: _mcresult[t], [_cache_key(cls, l) for l in id])
            for mc in mc_result:
                _process_cache[_cache_key(mc)] = mc
            return mc_result

        _id_diffs = set(id).difference([_mcresult[l].id for l in _mcresult])

        #There's probably a more "pythony" way of doing the following.
        _fetch = {}
        manager = cls.objects
        if using_db is not None:
            manager = manager.using(using_db)

        _db_results = list(manager.filter(id__in = _id_diffs))
        for l in _id_diffs:
            for fi in _db_results:
                if fi.id == l:
                    _fetch[_cache_key(cls, l)] = fi
                    break

        for _i in _fetch:
            put(_fetch[_i])
        _fetch.update(dict(zip(_mcresult, [_mcresult[l] for l in _mcresult])))

        results = []
        for l in id:
            if _fetch.has_key(_cache_key(cls, l)):
                results.append(_fetch[_cache_key(cls, l)])
        return results
    else:
        _obj = None
        try:
            _obj = _process_cache.get(_cache_key(cls, id))
            if _obj is None:
                _obj = cache.get(_cache_key(cls, id))
        except:
            pass
        if _obj is None:
            _obj = cls.objects.get(id = id)
            put(_obj)
        return _obj

def bust(obj, update = False):
    if type(obj) == list:
        cache.delete_many([_cache_key(o) for o in obj])
        for o in obj:
            if _cache_key(o) in _process_cache:
                del _process_cache[_cache_key(o)]
    else:
        _k = _cache_key(obj)
        cache.delete(_k)
        if _k in _process_cache:
            del _process_cache[_cache_key(obj)]
    if update:
        put(obj)


########### HANDLE CACHING ##############

def get_on_handle(cls, handle):
    id = cache.get(_cache_key(cls, handle))
    if id:
        return get(cls, id)
    return None

def put_on_handle(obj, handle):
    put(obj)
    cache.set(_cache_key(obj, handle), obj.id)

def bust_on_handle(obj, handle, update = False):
    bust(obj, False)
    cache.delete(_cache_key(obj, handle))
    if update:
        put_on_handle(obj, handle)


########### RELATION SET CACHING ##############
def _relation_cache_key(owner_obj, relation_obj, id):
    owner_class_name = owner_obj.__name__ if hasattr(owner_obj, "__name__") else owner_obj.__class__.__name__
    relation_class_name = relation_obj.__name__ if hasattr(relation_obj, "__name__") else relation_obj.__class__.__name__
    return '%s_%s_%s' % (owner_class_name, relation_class_name, id)

def relation_put(owner_obj, relation_obj, id, data):
    cache.set(_relation_cache_key(owner_obj, relation_obj, id), data)

def relation_get(owner_cls, relation_cls, id):
    return cache.get(_relation_cache_key(owner_cls, relation_cls, id))

def relation_bust(owner_obj, relation_obj, id):
    cache.delete(_relation_cache_key(owner_obj, relation_obj, id))


########### Decorator ################

def get_class_by_model_or_name(cls):
    collection_class = None
    if isinstance(cls, basestring):
        app_label, model_name = cls.split('.')
        try:
            collection_class=get_model(app_label, model_name)
        except ImportError:
            # This is a Django internal thing. If all the models are not yet loaded,
            # you can't get one out of the cache so it will try to do an import and then
            # you get circular dependencies. This just prepopulates the cache with all the models
            from django.db.models.loading import cache as app_cache
            app_cache._populate()
            # If it fails here you actually didn't specify a valid model class
            # remember it's "users.User" not just "User"
            collection_class=get_model(app_label, model_name)

    else:
        collection_class = cls
    return collection_class

def collection_cache(cls, local_var):
    """
    For use with properties or methods which take only the self argument.

    @param cls: a collection class (or Django-style model name such as "users.User" as the first argument.
    @param local_var: some variable name, conventionally a pseudo-private beginning with and underscore (e.g. "_list_ids")
                      This will store a dictionary on the object like {'cls': MyCollectionClass, 'ids': [1,2,3,4,5]}.
                      When the whole item is cached, it will only store the collection class and the ids
    """
    def _func(f):
        def _with_args(self):
            collection_class = get_class_by_model_or_name(cls)
            if not hasattr(self, local_var) or getattr(self, local_var, None) is None: # Just to be safe, you can define the local and set to None
                ret = f(self) or []
                setattr(self, local_var, {'cls': collection_class, 'ids': [item.id for item in ret]})
                put(self)
                return ret
            return list(get(collection_class, getattr(self, local_var)['ids']))
        return _with_args
    return _func
