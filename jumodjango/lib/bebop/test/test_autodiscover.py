'''
Created on Mar 7, 2011

@author: al
'''

from bebop import autodiscover_indexes, generate_solr_configs
from unittest import TestCase

class TestModel(TestCase):
        
    def test_autodiscover(self):
        import bebop.test
        indexes = autodiscover_indexes(bebop.test)
        generate_solr_configs(indexes)
        self.assertTrue(True)