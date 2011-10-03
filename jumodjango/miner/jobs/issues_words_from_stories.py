#!/usr/bin/env python
# django environment setup

from dumbo import *

import nltk
import settings
from miner.text.util import search_features
from miner.web.etl import html_to_story
import urllib2
import settings


def mapper1(key, value):
    """ Starting with input like:
    K=>row_id, V=>1\t<html>...Earthquake strikes in <b>Chile!<b>...</html>
    where 1 is the issue ID
    
    Output:
    K=>(row_id, 'earthquake', 1), V=>1
    K=>(row_id, 'strike', 1), V=>1
    K=>(row_id, 'chile', 1), V=>1
    ...
    """
    issue_id, doc = value.split('\t')
    
    doc = html_to_story(doc)
    
    for word in search_features(doc):
        yield (key, issue_id, word), 1
        
def reducer1(key, values):
    """ Output:
    
    K=>(row1, 'earthquake', 1), V=>10,
    K=>(row2, 'strike', 1), V=>5
    """
    yield (key, sum(values))

def mapper2(key, value):
    doc_num, issue_id, word = key
    occurences = value
    yield (doc_num, issue_id), (word, occurences)
    
def reducer2(key, values):
    # Pulls it all into memory but that should be ok
    word_occurences = list(values)
    yield key, word_occurences
    
def runner(job):
    job.additer(mapper1, reducer1)
    job.additer(mapper2, reducer2)
    
if __name__ == '__main__':
    """ Usage:  dumbo start issues_from_text.py -input /some/hdfs/input -output /some/hdfs/output -hadoop /path/to/hadoop """
    import dumbo
    dumbo.main(runner)
    