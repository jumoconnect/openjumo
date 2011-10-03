#!/usr/bin/env python
# django environment setup
import sys, os
sys.path.append(os.path.realpath(os.sep.join([os.path.dirname(__file__), os.pardir])))

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models.loading import cache
cache._populate()


from bebop import *

from django.contrib.contenttypes.models import ContentType
from django.db import models
from indexes import Autocomplete
from org.models import Org
from issue.models import Issue
from users.models import User, Location
from config import solr

import MySQLdb
from MySQLdb import cursors

# Get the content types up front for the queries
org_content_type = str(ContentType.objects.get(model='org').id)
issue_content_type = str(ContentType.objects.get(model='issue').id)
user_content_type = str(ContentType.objects.get(app_label='users',model='user').id)

queries = {Org: """
    select
    o.org_id,
    o.name as search_exact_name,
    o.name as search_all_names,
    o.handle,
    img_small_url,
    img_large_url,
    facebook_id,
    concat_ws(',', o.location_id, group_concat(distinct owl.location_id)) as location_ids,
    group_concat(oi.issue_id) as issue_ids,
    count(distinct c.user_id) as search_popularity,
    o.summary,
    o.is_vetted as search_jumo_vetted,
    group_concat(distinct ci.body separator ' ') as search_keywords
    from
    orgs o
    left join content_items ci
        on ci.content_type_id=""" + org_content_type + """
        and ci.object_id = o.org_id
    left join users_location l
        on o.location_id = l.id
    left join commitments c
        on c.content_type_id=""" + org_content_type + """
        and c.object_id = o.org_id
    left join org_working_locations owl
        using(org_id)
    left join org_orgissuerelationship oi
        using(org_id)
    where o.is_active=1
    group by o.org_id""",
    
Issue: """
    select
    i.issue_id,
    i.handle,
    i.name as search_exact_name,
    i.name as search_all_names,
    count(distinct c.user_id) as search_popularity,
    i.location_id as location_ids,
    i.summary,
    i.img_large_url,
    i.img_small_url,
    i.content_upgraded as search_jumo_vetted,
    group_concat(ci.body separator ' ') as search_keywords
    from
    issues i
    left join content_items ci
        on ci.content_type_id=""" + issue_content_type + """
        and ci.object_id = i.issue_id
    left join commitments c
        on c.content_type_id=""" + issue_content_type + """
        and c.object_id = i.issue_id
    where i.is_active = 1
    group by i.issue_id
    """,
User: """
    select
    au.id,
    au.username,
    u.thumb_img_url,
    u.facebook_id,
    concat_ws(' ', au.first_name, au.last_name) search_exact_name,
    case when u.likely_org = 1 and not u.admin_classification <=> 'user' then '' else concat_ws(' ', au.first_name, au.last_name) end as search_all_names,
    u.location_id as location_ids,
    count(distinct case when uu.is_following=1 then uu.follower_id end) as search_popularity,
    concat(rtrim(substring(bio, 1, 255)), if(char_length(bio) > 255, '...', '')) as summary,
    null as search_keywords,
    0 as search_jumo_vetted
    from
    auth_user au
    join users_user u
      on au.id = u.user_ptr_id
    left join users_usertouserfollow uu
      on uu.followed_id = u.user_ptr_id
    where au.is_active = 1
    group by u.user_ptr_id
    """
}


class JumoSolrIndexer(DBAPIBatchIndexer):
    def with_model(self, model):
        self.model = model
        self.model_mapper = dict((field.column, field.name) for field in model._meta.fields)
        return self

    def populate_issues(self):
        self.issue_dict = dict((i.id, i) for i in Issue.objects.only('id', 'name', 'handle', 'content_upgraded'))
        return self

    def populate_locations(self):
        # Keep an object cache of the locations so we're not issuing too many queries
        self.location_dict = dict((l.id, l) for l in Location.objects.all())
        return self

    def transform_locations(self, row):
        location_ids = row.pop('location_ids', [])
        if location_ids is None:
            location_ids = []
        else:
            location_ids = str(location_ids).split(',')
        if not hasattr(location_ids, '__iter__'):
            location_ids = [location_ids]

        # Preserve order but remove dupes
        location_ids = OrderedSet(location_ids)
        row['search_all_locations'] = [self.location_dict.get(int(location_id)) for location_id in location_ids if location_id]

    def transform_issues(self, row):
        issue_ids = row.pop('issue_ids', [])
        if issue_ids:
            issue_ids = str(issue_ids).split(',')
        elif issue_ids is None:
            issue_ids = []

        if not hasattr(issue_ids, '__iter__'):
            issue_ids = [issue_ids]

        issue_ids = OrderedSet(issue_ids)
        if issue_ids:
            row['search_all_issues'] = [self.issue_dict.get(int(issue_id)) for issue_id in issue_ids if issue_id]

    def transform_names(self, row):
        row['search_all_names'] = row['search_all_names'].split(',')

    def handle_row(self, row):
        if row.has_key('location_ids'):
            self.transform_locations(row)

        self.transform_names(row)
        self.transform_issues(row)
        # Again, write a nicer way to do this part and just call super
        model = self.model()
        [setattr(model, self.model_mapper.get(k, k), v) for k,v in row.iteritems()]

        return Autocomplete.from_model(model)

        #self.solr_conn.add(docs, commit=False)

    def commit(self):
        self.solr_conn.commit()

def main():
    database = settings.DATABASES['default']

    db_conn = MySQLdb.connect(
        host = database['HOST'],
        user = database['USER'],
        passwd = database['PASSWORD'],
        db = database['NAME'],
        cursorclass = cursors.SSDictCursor, # USE A SERVER-SIDE CURSOR FOR ETL!!! MUY IMPORTANTE!
        charset = 'utf8',
        use_unicode=True
    )
    cur = db_conn.cursor()

    indexer = solr.batch_index(Autocomplete, indexer=JumoSolrIndexer).populate_locations().populate_issues().cursor(cur)
    indexer.db_cursor.execute("set group_concat_max_len=65535")

    for model, query in queries.iteritems():
        indexer.with_model(model)

        print "Doing", model.__name__,"now..."
        indexer.execute(query)

        indexer.index_all()

    indexer.solr_conn.commit()

    db_conn.close()

if __name__ == '__main__':
    main()
