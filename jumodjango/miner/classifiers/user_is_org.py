#!/usr/bin/env python

'''
Created on Jul 20, 2011

@author: al
'''

import sys, os
sys.path.append(os.path.realpath(os.sep.join([os.path.dirname(__file__), os.pardir, os.pardir])))
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models.loading import cache as model_cache
model_cache._populate()

from nltk.classify import NaiveBayesClassifier
from org.models import Org
from users.models import User
import math
import logging

log = logging.getLogger('miner.classifiers')

def word_features(name):
    return dict((word.lower(), True) for word in name.split())

"""
Tuning constant
defined as the ratio: log2( (P(is_org) + tiny constant) / (P(is_user) + tiny_constant) )
Keep in mind that each time this is run, we exclude users
who have this probability or higher so by excluding more org users
you exclude all the words associated with them, which can boost
other users above the threshold
"""

# Since I'm doing log base 2 of the ratio (they can get rather large)
# the actual ratio we'd be working with is 2^n, so 8.0 with a min ratio of 3.0
MIN_RATIO = 3.0

# Use this bad boy as a pseudocount (added to both numerator and denominator) so we don't divide by 0
# Very small number so it's practically insignificant in the division
NORMALIZING_CONST = 0.0000001

def main():
    org_names = Org.objects.values_list('name', flat=True)

    users = User.objects.filter(likely_org=False)
    user_names = [user.get_name for user in users]
    # Exclude the users we know are orgs (exact same name). This mostly gets run the first time and for new users with org names
    non_org_user_names = set(user_names) - set(org_names)

    org_features = [(word_features(name), 'org') for name in org_names]
    user_features = [(word_features(name), 'user') for name in non_org_user_names]

    classifier = NaiveBayesClassifier.train(user_features + org_features)

    counter = 0

    likely_orgs = []

    for user in users:
        prediction = classifier.prob_classify(word_features(user.get_name))
        if prediction.max() == 'org':
            # Log probability ratio, so if P(org) == 2.4 and P(user) == 0.3 then log2(P(org)/P(user)) = log2(8.0) = 3.0
            ratio = math.log(((float(prediction.prob('org')) + NORMALIZING_CONST) / (float(prediction.prob('user')) + NORMALIZING_CONST)), 2)
            if ratio >= MIN_RATIO and user.likely_org == False and user.admin_classification != 'user':
                log.info('User ID %d with name "%s" is probably an org. Saving.' % (user.id, user.get_name))
                user.likely_org = True
                user.org_probability = ratio
                user.save()
                counter += 1

    log.info("Processed %d users with org-like names" % counter)
    
if __name__ == '__main__':
    main()