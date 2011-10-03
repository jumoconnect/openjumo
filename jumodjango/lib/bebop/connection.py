'''
Created on Feb 18, 2011

@author: al
'''

import pysolr

_solr_conns = {}

class Bebop(object):
    def __init__(self, host, port, solr_dir='solr', id='main'):   
        self._solr = _solr_conns[id] = _solr_conns.get(id) or pysolr.Solr('http://%s:%s/%s/' % (host, port, solr_dir))
      
    @property
    def raw_conn(self):
        return _solr_conns[self.id]
              
    def search(self, query, id='main'):
        return self._solr.search(query)
    
    def add(self, doc, commit=True):
        self._solr.add(doc._to_solr_doc(),commit=commit)

    def batch_add(self, docs, commit=False):
        self._solr.add([doc._to_solr_doc() for doc in docs], commit=commit)
        
    def commit(self):
        self._solr.commit()
        
    def optimize(self):
        self._solr.optimize()
        
    def rollback(self):
        self._solr.rollback()