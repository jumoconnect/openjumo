from schema import *
from model import *
from config import *
from data_import import *

import pkgutil
import sys

def autodiscover_indexes(*packages):
    indexes = {}
    for package in packages:
        pkg_path = os.path.dirname(package.__file__)
        module_names = [name for _, name, _ in pkgutil.iter_modules([pkg_path])]
        for module_name in module_names:
            qualified_name = package.__name__ + '.' + module_name
            __import__(qualified_name)
            module=sys.modules[qualified_name]
            for attr, value in inspect.getmembers(module):
                if hasattr(value, 'schema'):
                    indexes[value.__index__] = {'schema': value.schema,
                                                'config': value.config}
    return indexes

def generate_solr_configs(indexes, core_admin_conf=None):
    if len(indexes) > 1:
        generate_multicore_schema(core_admin_conf, **indexes)
    else:
        index_specs = indexes.values()[0]
        conf, schema = index_specs['config'], index_specs['schema']
        generate_schema(schema)
        generate_config(conf)
