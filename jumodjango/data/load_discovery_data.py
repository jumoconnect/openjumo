#!/usr/bin/env python
# django environment setup
import sys,os
sys.path.append(os.path.realpath(os.sep.join([os.path.dirname(__file__), os.pardir])))

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.contrib.contenttypes.models import ContentType
from discovery.models import TopCategory, SubCategory, DiscoveryItem
from org.models import Org

ISSUE_TYPE = ContentType.objects.get(app_label='issue', model='issue')
ORG_TYPE = ContentType.objects.get(app_label='org', model='org')
ORGS = Org.objects.all()[:30]

CATEGORIES = [
    ("Arts & Culture", ["Artist Support", "Performing Arts", "Film", "Museums",]),
    ("Education", ["After School Programs", "Girls Education", "Charter Schools", "Teacher Training",]),
    ("Health", ["Early Childhood Health", "Malaria", "Mental Health", "Mobile Clinics",]),
    ("Human Rights", ["Child Slavery", "Legal Assistance", "Reproductive Rights", "Refugees' Rights",]),
    ("Peace & Governance", ["Democracy", "Citizen Participation", "Government Accountability", "Public Media",]),
    ("Poverty", ["Poverty Alleviation", "Microfinance", "Housing", "Small Business Support",]),
]

def load_discovery_data():
    for tc_rank, (tc_name, sub_categories) in enumerate(CATEGORIES):
        tc = TopCategory(name=tc_name, rank=tc_rank)
        tc.save()
        for sc_rank, sc_name in enumerate(sub_categories):
            sc = SubCategory(name=sc_name, parent=tc, rank=sc_rank)
            sc.save()
            for di_rank in range(4):
                di = DiscoveryItem(entity=ORGS[4*sc_rank+di_rank], parent=sc, rank=di_rank)
                di.save()

if __name__ == '__main__':
    load_discovery_data()
