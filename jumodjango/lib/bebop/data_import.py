'''
Created on Mar 7, 2011

@author: al
'''

class BatchIndexer(object):
    def __init__(self, solr_conn, db_conn, index_query, batch_size=1000):
        self.batch_size = batch_size
        self.solr_conn = solr_conn
        self.db_conn = db_conn
        self._index_cursor = db_conn.cursor()
        self.index_query = index_query

    def exec_query(self):
        self._index_cursor.execute(self.index_query)
        
    def next_batch(self):
        self.batch = self._index_cursor.fetchmany(self.batch_size)
        return self.batch
        
    def index_batch(self, batch):
        self.solr_conn.add(batch)
        
    def index_all(self):
        count = 0
        while self.next_batch():
            count += 1
            print "Indexing batch", count
            self.index_batch(self.batch)
        
if __name__ == '__main__':
    import MySQLdb
    from MySQLdb import cursors
    import pysolr
    
    solr_conn = pysolr.Solr('http://localhost:8983/solr')
    solr_conn.delete(q="*:*")

    db_conn = MySQLdb.connect(host='localhost', user='root', db='test',
                              cursorclass=cursors.SSDictCursor
                              )
    
    indexer = BatchIndexer(solr_conn, db_conn, "select * from solr_test", batch_size=1000)
    print "Executing query..."
    indexer.exec_query()
    print "Running indexer..."
    indexer.index_all()