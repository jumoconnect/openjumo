'''
Created on Feb 14, 2011

@author: al
'''

from bebop import *
from unittest import TestCase

class FooDB(object):
    def __init__(self, **kw):
        for attr, val in kw.iteritems():
            setattr(self, attr, val)

class BarDB(object):
    def __init__(self, **kw):
        for attr, val in kw.iteritems():
            setattr(self, attr, val)


@SearchIndex('foo')
class Foo(SearchableModel):
    _target=FooDB
    id = DocumentId('id', Integer, model_attr='id')
    name = Field('name', Title, model_attr='name')
   
@SearchIndex('bar', config=DismaxSolrConfig)
class Bar(SearchableModel):
    _target=BarDB
    id = DocumentId('id', Integer, model_attr='id')
    name = Field('name', Title, model_attr='name')
        
        
class TestModel(TestCase):

    def test_internals(self):
        self.assertEquals(Foo.__index__, 'foo')
        self.assertEquals(Foo._fields, ['id', 'name'])

    def test_equals(self):
        clause = Foo.name == 'blah'
        self.assertEquals(clause, "name:blah")

    def test_boolean_clause(self):
        clause = and_(Foo.id > 5, or_(Foo.name=='blah', Foo.name=='blee'))
        self.assertEquals(clause, "(id:[5 TO *] AND (name:blah OR name:blee))")