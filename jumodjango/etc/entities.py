from users.models import User
from org.models import Org
from issue.models import Issue
import re
from etc.func import slugify
from etc.constants import RESERVED_USERNAMES

def create_handle(name):
    if isinstance(name, unicode):
        handle = slugify(name)[:25]
    elif isinstance(name, str):
        handle = slugify(unicode(name, 'utf-8'))[:25]
    else:
        raise Exception('Name must be instance of basestring')

    working = True
    found = False
    while working:
        try:
            test = User.objects.get(username = handle)
            found = True
        except Exception, inst:
            pass
        try:
            test = Org.objects.get(handle = handle)
            found = True
        except Exception, inst:
            pass

        if handle in RESERVED_USERNAMES:
            found = True

        if found:
            found = False
            handle = '%s_' % handle
            continue
        else:
            working = False
            break
    return handle


class EntityTypes:
    ORG = 'org'
    ISSUE = 'issue'
    USER = 'user'

_entity_types_to_models = {EntityTypes.ORG: Org,
                           EntityTypes.ISSUE: Issue,
                           EntityTypes.USER: User,
                         }

_models_to_entity_types = {Org: EntityTypes.ORG,
                           Issue: EntityTypes.ISSUE,
                           User: EntityTypes.USER,
                         }

def class_to_type(cls):
    return _models_to_entity_types.get(cls)

def obj_to_type(obj):
    return _models_to_entity_types.get(obj.__class__)

def type_to_class(type):
    return _entity_types_to_models.get(type)

def register_entity(type, entity):
    _models_to_entity_types[entity] = type
    _entity_types_to_models[type] = entity
