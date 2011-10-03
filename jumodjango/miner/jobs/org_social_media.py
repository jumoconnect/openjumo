import urllib2

from collections import deque

from org.models import Org
from miner.web.etl import html_to_story

from miner.web.social_media import SocialMediaCrawler

import logging

log = logging.getLogger(__name__)

class OrgSocialMediaMapper():
    def __init__(self, batch_size=200):
        self.batch_size = batch_size
    
    # Delegate methods...okie I've been doing too much iOS
    def get_api(self):
        raise NotImplementedError('Children must implement')
    
    def has_links(self, post):
        raise NotImplementedError('Children must implement')

    def extract_links(self, post):
        raise NotImplementedError('Children must implement')
    
    def default_text(self, post):
        raise NotImplementedError('Children must implement')
    
    def get_batch(self, org, **kw):
        raise NotImplementedError('Children must implement')        
    
    def __call__(self, key, value):
        """
        K => line number
        V => '10188\tPIH\t1274838358735
        """
        org_id, social_id, last_status_pull = value.split('\t')
        api = self.get_api()

        org = Org.get(org_id)
        
        since = last_status_pull
        page = 1
        
        params = dict(limit=200)
        
        queue = deque([page])
        
        urls = []

        log.info("Creating pools")
         # URL crawlers, just use 20 greenlets for now
        crawler = SocialMediaCrawler(pool_size=20)
        
        while queue:
            page = queue.popleft()
            
            log.info("Got page %s" % page)
            
            posts, next_page, new_last_fetched = self.get_batch(org, limit=self.batch_size, page=page, since=since)
            
            log.info("Got %s posts, next page %s" % (len(posts), next_page ) )
            
            if new_last_fetched:
                setattr(org, self.last_updated_column, str(new_last_fetched))
                org.save()
                    
            if next_page:
                queue.append(next_page)
            
            for post in posts:
                if self.has_links(post):
                    log.info("Post has links")
                    # These are just URLs to crawl and get back HTML to throw in with the rest of the data
                    urls.extend( self.extract_links(post) )
                
                log.info("Yielding post data")
                
                yield (org_id, self.default_text(post))
                    
        
        log.info("Getting %s urls" % len(urls))
        for doc in crawler.crawl(urls):
            yield (org_id, doc)


def reducer(key, values):
    # Pull it all into memory
    values = list(values)
    yield (key, ' '.join(values))
    