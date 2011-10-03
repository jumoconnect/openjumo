from unittest import TestCase
from bebop import *

class TestGenerateSchema(TestCase):
    def test_schema(self):
        filename = './test/unit_test_schema.xml'
        schema = SolrSchema('test_schema',
                            field_types=SolrFieldTypes(Integer, Text),
                            fields = SolrSchemaFields(
                                Field('foo', Text),
                                DocumentId('bar', Integer)
                                )
                            )
        generate_schema(schema, path=filename)

        generated_file = open(filename).read()
        test_file = open('./test/test_schema.xml').read()
        
        self.assertEqual(generated_file, test_file)