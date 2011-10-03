from unittest import TestCase
from bebop import *

class TestGenerateConfig(TestCase):
    
    def test_generate_config(self):

        config = DismaxSolrConfig

        path = './test/unit_test_config.xml'
        generate_config(config, path=path)
    
        expected = open('./test/test_config.xml').read()
        generated = open(path).read()

        self.assertEqual(expected, generated)
