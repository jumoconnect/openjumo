'''
Created on Apr 12, 2011

@author: al
'''

import sys, os
sys.path.append(os.path.realpath(os.sep.join([os.path.dirname(__file__), os.pardir])))

from django.core.management import setup_environ
import settings
setup_environ(settings)

from util.base_daemon import *
from donation.models import Donation
from donation.tasks import process_donation

class CollectionsDaemon(BaseDaemon):
    process_name = 'collectionsd'
    sleep_interval = 60*60 # 1 hour

    def run_iteration(self):
        donations_to_retry = Donation.get_retryable_donations()
        for donation in donations_to_retry:
            process_donation.delay(donation.id)
        return self.sleep_interval


if __name__ == '__main__':
    CollectionsDaemon.start(settings)