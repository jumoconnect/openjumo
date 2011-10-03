#!/usr/bin/env python
# django environment setup

import sys,os
sys.path.append(os.path.realpath(os.sep.join([os.path.dirname(__file__), os.pardir])))

from django.core.management import setup_environ
from django.core import serializers
import settings
setup_environ(settings)

from django.contrib.contenttypes.models import ContentType
from discovery.models import TopCategory, SubCategory, DiscoveryItem
from org.models import Org
from issue.models import Issue


def output(obj,name):
    file = open('data/fixtures/%s.json' % name, 'w')
    file.write(serializers.serialize('json',objs,indent=1))
    file.close()

if __name__ == '__main__':
    issues = [{'name' : 'MALARIA_ISSUE', 'obj' : Issue.objects.get(name='Malaria')}]
    orgs = [{'name' : 'FREEDOM_ORG', 'obj' : Org.objects.get(name='Freedom to Marry')}, {'name' : 'HRW_ORG', 'obj' : Org.objects.get(name='Human Rights Watch')}]


    for iss in issues:
        i = iss['obj']
        content = [m for m in i.get_all_content]
        objs = [i] + [m for m in i.get_all_actions] + [m for m in i.get_all_advocates] + [m for m in i.get_all_media_items] + [m for m in i.get_all_timeline_items] + content + [m.get_media_item for m in content if m.get_media_item != None]
        output(objs,iss['name'])

    for org in orgs:
        i = org['obj']
        content = [m for m in i.get_all_content]
        objs = [i] + [m for m in i.get_all_actions] + [m for m in i.get_all_media_items] + [m for m in i.get_all_timeline_items] + content + [m.get_media_item for m in content if m.get_media_item != None]
        output(objs,org['name'])




