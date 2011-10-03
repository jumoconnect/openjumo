#!/usr/bin/env python

from crawler import WebCrawler, log

import logging
import os
import hashlib
from miner.text.util import strip_control_characters
import MySQLdb
from MySQLdb import cursors


class FeedItemWebCrawler(WebCrawler):
    temp_outfile_path = '/tmp/feed_items'
    outfile_base_path = '/tmp/scraped'
    hdfs_path = '/miner/classifiers/training_data/feed_items'
    
    def fetch_url(self, line):
        issue_id, url, data = line.split('\t')
        url = url.strip('"')
        
        outfile = os.sep.join([self.outfile_base_path, hashlib.md5(''.join([issue_id, url or data])).hexdigest()]) + '.out'
        
        if url and not os.path.exists(outfile):
            new_data = super(FeedItemWebCrawler, self).fetch_url(url)
            if new_data:
                data = new_data

        if not os.path.exists(outfile):            
            with open(outfile, 'w') as f:
                    f.write('\t'.join([issue_id, strip_control_characters(data)]))    
            return 'Wrote data'
        else:
            return 'Nada'
        
        
    @classmethod
    def write_to_temp(cls, temp_file, host, user, password, db):
        conn = MySQLdb.connect(host=host,
                               user=user,
                               passwd=password,
                               db=db)
                
        
        feed_item_query = """
        select target_id as issue_id, url, concat_ws(' ', replace(replace(replace(title, '\t', ' '), '\n', ' '), '\r', ' '), replace(replace(replace(description, '\t', ' '), '\n', ' '), '\r', ' ') ) as text
        into outfile '%s'
        fields terminated by '\t' optionally enclosed by '"'
        lines terminated by '\n'
        from feed_item fi
        join staff_users su
          on fi.origin_type='user'
          and fi.origin_id = su.user_id
        where fi.target_type='issue'
        and fi.item_type='user_story'    
        """ % temp_file
        
        cur = conn.cursor()
        cur.execute(feed_item_query)

if __name__ == '__main__':
    from fabric.api import local
    import time
    
    from optparse import OptionParser
    
    log.setLevel(logging.DEBUG)
    
    parser = OptionParser()

    parser.add_option('-d', '--hadoop-path', dest='hadoop_path')
    parser.add_option('-f', '--hdfs-path', dest='hdfs_path')
    
    parser.add_option('-t', '--temp-file-path', dest='tempfile_path', default=FeedItemWebCrawler.temp_outfile_path)
    parser.add_option('-m', '--mysql-host', dest='mysql_host', default='localhost')
    parser.add_option('-p', '--mysql-user', dest='mysql_user', default='root')
    parser.add_option('-w', '--mysql-password', dest='mysql_password', default='')
    parser.add_option('-b', '--mysql-database', dest='mysql_database', default='jumofeed')
    
    options, args = parser.parse_args()

    crawler = FeedItemWebCrawler()

    local('rm -f %s' % options.tempfile_path)
    crawler.write_to_temp(options.tempfile_path, options.mysql_host, options.mysql_user, options.mysql_password, options.mysql_database)

    log.info('Green pool time!')
    t1 = time.time()
    for result in crawler.crawl(open(options.tempfile_path, 'r')):
        log.info(result)
    t2 = time.time()
    
    log.info('DONE in %s seconds' % (t2 - t1))
    
    local('rm -f %s' % options.tempfile_path)
    local('for f in %(outfiles)s/*.out ; do cat $f >> %(final)s ; echo "" >> %(final)s ; done' % {'final': options.tempfile_path,
                                                                                                  'outfiles': FeedItemWebCrawler.outfile_base_path} )

    #local('rm -rf %s' % outfile_base_path)    
    local('%s dfs -copyFromLocal %s %s' % (options.hadoop_path, options.tempfile_path, options.hdfs_path))
