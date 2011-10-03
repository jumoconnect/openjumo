#!/usr/bin/env python

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db.models.loading import cache as model_cache
model_cache._populate()

from issue.models import Issue
from related_search import RelatedSearchClassifier
    
def train_issue_classifier(results_file):
    issue_words = []
    
    active_issues = dict((i.id, i) for i in Issue.objects.filter(is_active=True))
        
    for row in results_file:
        row_values = [eval(value) for value in  row.split('\t')]
        issue_id, features = row_values[1], row_values[2:]
        if issue_id in active_issues:
            issue_words.append((features, active_issues[issue_id].name))
                
    id = 0
    word_to_id = {}
    id_to_word = {}
    
    corpus =  []
    classifications = []
    
    for features, classification in issue_words:
        row = []
        for word, cnt in features:
            if word not in word_to_id:
                word_to_id[word] = id
                id_to_word[id] = word
                id += 1

            row.append((word_to_id[word], cnt))
        corpus.append(row)
        classifications.append(classification)
        
    del issue_words
        
    classifier = RelatedSearchClassifier.train(corpus, classifications, id_to_word)       
                                
    return classifier

if __name__ == '__main__':
    import os, sys
    import cPickle as pickle
    
    if len(sys.argv) < 2:
        print """Usage: python issues_from_text.py results_file"""
        sys.exit()   
    results_file = sys.argv[1]
    classifier = train_issue_classifier(open(results_file, 'r'))
    classifier.save_model()