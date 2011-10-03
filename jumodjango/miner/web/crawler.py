import string
import urllib2

import logging
import httplib

# This is the kind of task where coroutines really shine

green_lib = None

try:
    import gevent
    import gevent.pool
    from gevent import monkey
    monkey.patch_all()
    green_lib = 'gevent'
except ImportError:
    import eventlet
    from eventlet import monkey_patch
    monkey_patch()
    green_lib = 'eventlet'
        
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('miner.web.crawler')

class WebCrawler(object):
    def __init__(self, pool_size=200):
        self.pool = None
        if green_lib == 'gevent':
            self.pool = gevent.pool.Pool(pool_size)
        elif green_lib == 'eventlet':
            self.pool = eventlet.greenpool.GreenPool(pool_size)

    def fetch_url(self, url):
        try:
            log.debug('Making request to %s' % url)
            request = urllib2.Request(url, headers={'User-Agent': 'Your Mom'})
            u = urllib2.urlopen(request)
            if u.headers.type=='text/html':
                data = u.read()
                log.debug('Success')
            else:
                data = ''
                log.debug('Non-HTML content type')
            return data
        except urllib2.URLError, e:
            log.warn('Boo, got a url error for %s: %s' % (url, e))
            return ''
        except httplib.HTTPException, e:
            log.warn('Boo, got an HTTP error for %s: %s' % (url, e))
            return ''            

    def crawl(self, urls):
        for result in self.pool.imap(self.fetch_url, urls):
            yield result