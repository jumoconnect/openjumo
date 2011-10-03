#!/usr/bin/env python
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models.loading import cache as model_cache
model_cache._populate()

import os
import logging

from org.models import OrgIssueRelationship, RelatedOrg
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from etc import cache

from datetime import datetime
import logging
import logging.handlers
from issue.models import Issue
from org.models import Org
from users.models import Location
from functools import partial

import settings
import MySQLdb
from MySQLdb import cursors
from collections import defaultdict
from itertools import groupby
from operator import itemgetter
import math

import multiprocessing

import nltk
from numpy import zeros
from numpy import dot
from numpy.linalg import norm

from miner.text.util import porter, stopwords, tokenizer
import gensim

log = logging.getLogger()
CURSOR_BATCH_SIZE = 1000
LIMIT = 20
db_settings = settings.DATABASES['default']



# Non-profit specific
#'bring','together', 'mission',
#'organization', 'work', 'non-profit',
#'make', 'difference',
#'solution', 'grassroots', 'communities', 'provide',
#'support', 'people','live', 'program', 'promote',
#'service', 'life', 'build', 'improve', 'individual', 'resource',
#'opportunity', 'dedicated', 'empower','help', 'committed']) |


# Add org ids for testing the algorithm
test_orgs = set([10188, 1051, 6599, 5539, 3764, 5102, 9909, 3739,4856,2301,6448, 3108, 12601, 12600, 10187, 10154, 10122, 8773, 4187, 9347, 5837, 7112, 5754, 6083, 6011, 5684])


def get_db_connection():
    c = MySQLdb.connect(host=db_settings.get('HOST', 'localhost'),
                        port= int(db_settings.get('PORT') or 3306),
                        user=db_settings.get('USER', 'root'),
                        passwd=db_settings.get('PASSWORD', ''),
                        db=db_settings.get('NAME', 'jumodjango'),
                        use_unicode=True,
                        charset='utf8'
                        )
    return c

# Probably move this to a lib or use the bebop one
def batched_db_iter(cur, query, batch_size=CURSOR_BATCH_SIZE):
    cur.execute(query)
    while True:
        batch = cur.fetchmany(batch_size)
        if not batch:
            break
        for row in batch:
            yield row

def insert_related(org, similar):
    log.debug('Inserting some related orgs')
    # Note: doing this with an INSERT ON DUPLICATE KEY UPDATE
    # which is efficient but if we decide to change the number of items we store
    # we'll probably want to just clear the table first
    q = """
    insert into related_orgs
    values
    (null, %s, %s, %s, utc_timestamp(), utc_timestamp())
    on duplicate key update related_org_id = values(related_org_id),
    date_updated=utc_timestamp()
    """

    params = [(org, related_org, i+1) for i, related_org in enumerate(similar) if related_org != org]

    # Difficult to use a connection pool across multiple processes, so doing this
    conn = get_db_connection()
    cur = conn.cursor()

    cur.executemany(q, params)

    conn.commit()


def setup():
    # Grab some data from the DB so we can crunch it
    active_orgs = Org.objects.filter(is_active=True)
    org_content_type = ContentType.objects.get(model='org').id

    org_dict = dict((o.id, o) for o in active_orgs)

    # That's right, pulled out the double defaultdict what whAAAAt!
    features = defaultdict(lambda: defaultdict(list))
    term_frequencies = defaultdict(int)

    # There is no way in Django to use a server-side cursor
    conn = get_db_connection()
    cur = conn.cursor(cursors.SSDictCursor)
    # group_concat is one of the best things ever, but its default max length before it starts truncating is far
    # too low for our purposes. Crank that up.
    cur.execute("set group_concat_max_len=65535")

    all_content = {}
    # Text we'll be analyzing, all content items associated with every org
    content_query = "select o.org_id as org_id, group_concat(ci.body separator ' ') as content from orgs o join content_items ci on ci.content_type_id = " + str(org_content_type) + " and ci.object_id = o.org_id and ci.section='center' group by o.org_id"
    for row in batched_db_iter(cur, content_query):
        org = row['org_id']
        if org not in org_dict:
            continue
        all_content[org] = row['content']

    issue_query = "select org_id, group_concat(i.name) as issues from org_orgissuerelationship oi join issues i using(issue_id) group by org_id"

    # See upstairs for implementation of batched_db_iter
    for row in batched_db_iter(cur, issue_query):
        org = row['org_id']
        if org not in org_dict:
            continue
        issues = [issue for issue in row['issues'].split(',')]
        for issue in issues:
            features[org]['issues'].append(issue)

    location_query = "select org_id, l.* from org_org_working_locations o join users_location l on o.location_id = l.id"

    #for row in batched_db_iter(cur, location_query):
    #    org = row.pop('org_id')
    #    features[org]['locations'].append(unicode(Location(**row)))

    # Could include followers as a feature for the "people who follow org x also follow org y"

    #followers_query = "select org_id, group_concat(user_id) as followers from org_usertoorgfollow where following = 1 group by org_id"
    #for row in batched_db_iter(cur, followers_query):
    #    org = row['org_id']
    #    followers = [long(user) for user in row['followers'].split(',')]
    #    features[org]['followers'] = followers

    # Deletes the rows that have been read into the cursor
    cur.close()
    conn.close()

    for org, content in all_content.iteritems():
        if org not in org_dict:
            continue

        org_name = org_dict[org].name
        content = content.replace(org_name, '')
        all_tokens = nltk.regexp_tokenize(content, tokenizer)

        #stemmed_tokens = [porter.stem(t.lower()) for t in all_tokens if t.lower() not in stopwords]
        gram_tokens = [t.lower() for t in nltk.regexp_tokenize(content, tokenizer) if t.lower() not in stopwords]
        features[org]['unigrams'] = gram_tokens
        features[org]['bigrams'] = nltk.bigrams(gram_tokens)   # bigrams('The cat in the hat') => [('The', 'cat'), ('cat', 'in'), ('in', 'the'), ('the', 'hat')]
        features[org]['trigrams'] = nltk.trigrams(gram_tokens)

        # Tried these but they were expensive in terms of computation time
        # Besides, once we get out to three or more words it's probably better to start looking at
        # sentence structure with nltk, things like: (org name) (helps/provides) [x] with [y]

    for k,v in features.iteritems():           # {org_id: {'bigrams': [('a','b') ...], 'issues': ['fracking','environment']}}
        for type, words in v.iteritems():
            # Using set so we're calculating unique documents
            for word in set(words):
                term_frequencies[(type, word)] += 1

    # Eliminate words which only pertain to one document (names, etc.)
    to_delete = set()
    for k, v in term_frequencies.iteritems():
        # only 1 occurrence in the whole doc set
        if v==1:
            to_delete.add(k)

    for k in to_delete:
        del term_frequencies[k]

    word_ids = dict((k, i) for i, k in enumerate(term_frequencies.keys()))
    num_orgs = len(all_content)

    weights = dict(trigrams=1,
                   bigrams=2,
                   unigrams=1.5,
                   issues=.2,
                   locations=.1,
                   followers=.1,
                   )

    return features, word_ids, term_frequencies, num_orgs, weights, active_orgs

def write_mm_corpus(features, word_ids, term_frequencies, num_orgs, weights):
    corpus = []

    id_to_index = {}
    index = 0

    # Create TF-IDF model
    for org, doc in features.iteritems():
        doc_length = dict((k, len(v)) for k,v in doc.iteritems())
        doc_occurences = defaultdict(int)
        for type, words in doc.iteritems():
            for word in words:
                doc_occurences[(type,word)] += weights[type]

        row = []

        # Term-frequency * inverse document frequency: similar to what Solr uses
        # reference: http://en.wikipedia.org/wiki/Tf%E2%80%93idf
        for type, words in doc.iteritems():
            for word in words:
                if (type,word) not in term_frequencies:
                    continue
                term_freq = float(doc_occurences[(type,word)]) / doc_length[type]  # Normalize for shorter/longer documents
                inverse_doc_freq = math.log(float(num_orgs) / (term_frequencies[(type,word)] + 1))
                tfidf = term_freq * inverse_doc_freq
                row.append((word_ids[(type,word)], tfidf))

        corpus.append(row)

        id_to_index[org] = index
        index += 1

    fname = '/tmp/corpus.mm'
    gensim.corpora.MmCorpus.serialize(fname, corpus)
    return fname, id_to_index, corpus


def main():
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option('-l', '--log-level', dest='log_level', choices=['DEBUG', 'INFO', 'WARN', 'ERROR'], default='INFO')
    (options, args) = parser.parse_args()
    log_level = getattr(logging, options.log_level)

    if os.path.exists('/cloud/logs'):
        handler = logging.handlers.RotatingFileHandler('/cloud/logs/org_relation.log', backupCount=10)
        log.addHandler(handler)

    log.setLevel(log_level)

    log.info("Doing setup")
    features, word_ids, term_frequencies, num_orgs, weights, all_orgs = setup()

    org_dict = dict((o.id, o) for o in all_orgs)

    log.info("Creating Matrix Market format corpus and saving to disk")
    fname, id_to_index, corpus = write_mm_corpus(features, word_ids, term_frequencies, num_orgs, weights)

    mm = gensim.corpora.MmCorpus(fname)
    id2word = dict((v,k) for k,v in word_ids.iteritems())

    log.info("Ok, now building the LSI corpus")

    lsi = gensim.models.LsiModel(corpus=mm, num_topics=500,id2word=id2word)

    log.info("Yayyy got topics")

    """
    Programmatic access to gensim's print_debug

    import numpy

    id2token=lsi.id2word
    u=lsi.projection.u
    s=lsi.projection.s
    topics=range(100)
    num_words=10
    num_neg=0
    log.info('computing word-topic salience for %i topics' % len(topics))
    topics, result = set(topics), {}

    words_per_topic = {}

    for uvecno, uvec in enumerate(u):
        uvec = numpy.abs(numpy.asarray(uvec).flatten())
        udiff = uvec / numpy.sqrt(numpy.sum(numpy.dot(uvec, uvec)))
        for topic in topics:
            result.setdefault(topic, []).append((udiff[topic], uvecno))

    log.debug("printing %i+%i salient words" % (num_words, num_neg))
    for topic in sorted(result.iterkeys()):
        weights = sorted(result[topic], key=lambda x: -abs(x[0]))
        _, most = weights[0]
        if u[most, topic] < 0.0: # the most significant word has a negative sign => flip sign of u[most]
            normalize = -1.0
        else:
            normalize = 1.0

        # order features according to salience; ignore near-zero entries in u
        words = []
        for weight, uvecno in weights:
            if normalize * u[uvecno, topic] > 0.0001:
                words.append((id2token[uvecno], u[uvecno, topic]))
                if len(words) >= num_words:
                    break

        words_per_topic[topic] = words
    """

    index = gensim.similarities.MatrixSimilarity(lsi[corpus])

    index_to_id = dict((v, k) for k,v in id_to_index.iteritems())

    for idx, doc in enumerate(corpus):
        org_id = index_to_id[idx]
        #if org_id not in test_orgs:
        #    continue
        # Convert document to vector space
        vector_lsi = lsi[doc]
        sims = index[vector_lsi]
        sims = [index_to_id[k] for k, v in sorted(enumerate(sims), key = lambda item:item[1], reverse=True)[:21]]
        insert_related(org_id, sims)
        #log.info("Org %s similar to: %s" % (org_dict[org_id] , ', '.join([org_dict[org2_id].name for org2_id in sims]) ))


    #lda = gensim.models.LdaModel(corpus=mm, num_topics=100, id2word=id2word,
    #                             chunksize=10000, passes=1, update_every=1)

    # Nuke the orgs in memcache but don't block the high-concurrency section
    #all_orgs = list(Org.objects.all())
    #cache.bust(all_orgs)

if __name__ == '__main__':
    main()
