import sys
import os
import site

site.addsitedir('/cloud/virtual/lib/python2.7/site-packages/')

paths = ['/cloud/src/jumodjango', '/cloud/src']
for path in paths:
    if path not in sys.path:
        sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django.core.handlers.wsgi

# Have to do this cache._populate bit or get_model calls will try to do an import
# and cause circular import hell

from django.db.models.loading import cache
cache._populate()

application = django.core.handlers.wsgi.WSGIHandler()
