#!/usr/bin/env python

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models.loading import cache as model_cache
model_cache._populate()

import facebook
 
from django.db import connection
from django.db.models import Q

import settings
import urllib2
import urlparse

from fabric.api import local
from org.models import Org
from miner.web.crawler import WebCrawler
from miner.jobs.org_social_media import OrgSocialMediaMapper, reducer

class FacebookMapper(OrgSocialMediaMapper):
    last_updated_column = 'facebook_last_fetched'
    
    def get_api(self):
        self.api = facebook.GraphAPI(settings.FACEBOOK_ACCESS_TOKEN)
 
    def has_links(self, post):
        return post['type'] == 'link'

    def extract_links(self, post):
        return [post['link'].encode('utf-8')]
    
    def default_text(self, post):
        return ' '.join([post.get('name', ''), post.get('message', ''), post.get('description', '')])
    
    def get_batch(self, org, limit=200, page=1, since=None):
        params = dict(limit=limit, offset=(page-1)*limit )
        
        # This is being urlencoded in python-facebook-sdk
        # so don't include the param if it's None
        if since:
            params['since'] = since
            
        try:
            posts = self.api.get_connections(str(org.facebook_id), 'posts', fields='message,link,name,caption,description,type', **params)    
        except Exception:
            return [], None, None
    
        # Can use this but doesn't really account for not fetching data twice
        paging = posts.get('paging', {})
        
        next_page = None
        
        if len(posts.get('data', [])) == limit:
            next_page = page + 1
        
        new_last_fetched_date = None
    
        if page==1:
            parsed_query_string = urlparse.parse_qs(urlparse.urlparse(paging.get('previous', '')).query)
            new_last_fetched_date = parsed_query_string.get('since', [None])[0]
    
        return posts['data'], next_page, new_last_fetched_date

def runner(job):
    job.additer(FacebookMapper, reducer)

def starter(program):
    tempfile_path = '/tmp/facebook'
    input_path = '/miner/search/inputs/facebook'
    output_path = '/miner/search/outputs/facebook'
    
    with open(tempfile_path, 'w') as tempfile:
        orgs = Org.objects.filter(is_active=True, facebook_id__isnull=False)[:10]
        for org in orgs:
            tempfile.write('\t'.join([str(org.id), str(org.facebook_id), str(org.facebook_last_fetched or '')]) +'\n')

    local('if hadoop fs -test -e ' + input_path +' ;  then hadoop fs -rm ' + input_path + '; fi')
    local('if hadoop fs -test -e ' + output_path + ' ;  then hadoop fs -rmr ' + output_path + '; fi')
    
    local('hadoop fs -copyFromLocal ' + tempfile_path + ' ' + input_path)

    program.addopt('input', input_path)
    program.addopt('output', output_path)

if __name__ == '__main__':
    import dumbo
    dumbo.main(runner, starter)