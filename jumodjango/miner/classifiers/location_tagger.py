#!/usr/bin/env python
'''
Created on Jul 13, 2011

@author: al
'''

from decision_tree import *
from collections import defaultdict
import re
import cPickle as pickle

import logging
log = logging.getLogger('miner.classifiers')

Ambiguous = 'ambiguous'

class LocationClassifier(DecisionTree):
    cache_key = 'decision_trees/location_classifier'

    US = 'US'
    INTERNATIONAL = 'International'

    countries = set()

    us_cities = set()
    foreign_cities = set()

    us_states_verbose = set(['alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado', 'connecticut',
                             'delaware', 'district of columbia', 'florida', 'georgia', 'hawaii', 'idaho', 'illinois',
                             'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana', 'maine', 'maryland', 'massachusetts',
                             'michigan', 'minnesota', 'mississippi', 'missouri', 'montana', 'nebraska', 'nevada',
                             'new hampshire', 'new jersey', 'new mexico', 'new york', 'north carolina', 'north dakota',
                             'ohio', 'oklahoma', 'oregon', 'pennsylvania', 'rhode island', 'south carolina', 'south dakota',
                             'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington', 'west virginia',
                             'wisconsin', 'wyoming'])

    us_states = set(['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE',
              'FL', 'GA', 'HI', 'IA', 'ID', 'IN', 'IL', 'KS', 'KY',
              'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT',
              'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH',
              'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT',
              'VA', 'VT', 'WA', 'WI', 'WV', 'WY'])

    us_postal_code_regex = re.compile('^[\d]{5}(-[\d]{4})?$')

    def __init__(self, inst):
        self.inst = inst

    @property
    def label(self):
        return self.inst.classification

    @feature
    @property
    def country_is_us(self):
        if self.inst.country_name == 'United States':
            return True
        elif self.inst.country_name:
            return False
        else:
            return None

    @feature
    @property
    def us_state(self):
        if self.inst.region and self.inst.region.strip().upper() in self.us_states:
            return True
        elif self.inst.region:
            return False
        else:
            return None

    @feature
    @property
    def us_city(self):
        if not self.inst.locality:
            return None

        is_us = self.inst.locality.strip().lower() in self.foreign_cities
        is_foreign = self.inst.locality.strip().lower() in self.foreign_cities

        if is_us and not is_foreign:
            return True
        elif is_foreign and not is_us:
            return False
        elif is_foreign and is_us:
            return Ambiguous
        else:
            return None

    @feature
    @property
    def us_postal_code(self):
        if not self.inst.postal_code:
            return None
        else:
            return self.us_postal_code_regex.match(self.inst.postal_code.strip()) is not None

    @feature
    @property
    def name_is_us(self):
        name = (self.inst.name or '').strip().lower()
        if not name:
            return None
        if name == 'united states' or name in self.us_states_verbose:
            return True
        elif name in self.countries:
            return False
        else:
            return None

    @classmethod
    def prepare_data(cls, data):
        for location in data:
            if location.classification == LocationClassifier.US and location.locality:
                cls.us_cities.add(location.locality.strip().lower())
            elif location.classification == LocationClassifier.INTERNATIONAL and location.locality:
                cls.foreign_cities.add(location.locality.strip().lower())

            if location.country_name:
                cls.countries.add(location.country_name.strip().lower())

        training_data = [LocationClassifier(location) for location in data]
        return training_data

    @classmethod
    def get_model(cls):
        from django.core.cache import cache
        return cache.get(cls.cache_key)

def tag_unknown_locations_and_publish():
    import sys, os
    sys.path.append(os.path.realpath(os.sep.join([os.path.dirname(__file__), os.pardir, os.pardir])))
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)

    from django.db.models.loading import cache as model_cache
    model_cache._populate()

    from django.core.cache import cache

    from entity_items.models.location import Location
    classified = Location.objects.filter(classification__isnull=False)

    decision_tree = LocationClassifier.train(classified)
    log.info("Decision tree: %s" % decision_tree)
    if decision_tree:
        cache.set(LocationClassifier.cache_key, decision_tree.copy())    # Have to copy it so it's a normal dict again

    unclassified = Location.objects.filter(classification__isnull=True)
    for loc in unclassified:
        classification = LocationClassifier.classify(loc)
        if classification:
            log.info("Saving location")
            loc.classification = classification
            loc.save()

if __name__ == '__main__':
    log.setLevel(logging.INFO)
    tag_unknown_locations_and_publish()
