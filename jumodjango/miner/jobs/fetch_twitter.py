#!/usr/bin/env python

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models.loading import cache as model_cache
model_cache._populate()

from fabric.api import local
import twitter
from org.models import Org
from miner.jobs.org_social_media import OrgSocialMediaMapper, reducer

class TwitterMapper(OrgSocialMediaMapper):
    last_updated_column = 'twitter_last_status_id'

    # Delegate methods...okie I've been doing too much iOS
    def get_api(self):
        self.api = twitter.Api(use_gzip_compression=True)
    
    def has_links(self, post):
        return len(post.urls) > 0

    def extract_links(self, post):
        return [u.url for u in post.urls]
    
    def default_text(self, post):
        return ' '.join([post.text] + [h.text for h in post.hashtags] )
    
    def get_batch(self, org, limit=200, page=1, since=None):
        try:
            statuses = self.api.GetUserTimeline(org.twitter_id, since_id=since, count=limit, page=page, include_entities=True)
        except Exception:
            statuses = []

        last_status_id = statuses[0].id if page == 1 and len(statuses) > 0 else None
        next_page = None
        if len(statuses) == limit:
            next_page = page + 1

        return statuses, next_page, last_status_id

def starter(program):
    tempfile_path = '/tmp/twitter'
    input_path = '/miner/search/inputs/twitter'
    output_path = '/miner/search/outputs/twitter'
    
    with open(tempfile_path, 'w') as tempfile:
        orgs = Org.objects.filter(is_active=True, twitter_id__isnull=False).exclude(twitter_id='')[:10]
        for org in orgs:
            tempfile.write('\t'.join([str(org.id), org.twitter_id, str(org.twitter_last_status_id or '')]) +'\n')
    # Only way I could figure out to do a replace
    local('if hadoop fs -test -e ' + input_path +' ;  then hadoop fs -rm ' + input_path + '; fi')
    local('if hadoop fs -test -e ' + output_path + ' ;  then hadoop fs -rmr ' + output_path + '; fi')
    
    local('hadoop fs -copyFromLocal ' + tempfile_path + ' ' + input_path)

    program.addopt('input', input_path)
    program.addopt('output', output_path)

def runner(job):
    job.additer(TwitterMapper, reducer)


if __name__ == '__main__':
    import dumbo
    dumbo.main(runner, starter)