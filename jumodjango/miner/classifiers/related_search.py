import numpy

from scipy.sparse import coo_matrix, csc_matrix
from scikits.learn.naive_bayes import MultinomialNB
from scikits.learn.externals import joblib
from miner.text.util import search_features

import os

import settings
import urlparse
import hashlib
import cPickle as pickle
import itertools

parsed_cache_url = urlparse.urlparse(settings.CACHE_BACKEND)
cache_url = parsed_cache_url.netloc

import pylibmc

classification_dict_cache_key = 'miner/related_search/classifications'
num_features_key = 'miner/related_search/num_features'

def hash_key(feature):
    if hasattr(feature, '__iter__'):
        return 'miner/related_search/bigram_ids/%s' % hashlib.md5('|*|'.join(feature)).hexdigest()
    else:
        return 'miner/related_search/unigram_ids/%s' % hashlib.md5(feature).hexdigest()

def feature_cache_key(feature):
    if hasattr(feature, '__iter__'):
        return 'miner/related_search/bigram_ids/%s' % ''.join(feature)
    else:
        return 'miner/related_search/unigram_ids/%s' % feature
        
def get_cache():
    return pylibmc.Client([cache_url], binary=True,
                               behaviors={'tcp_nodelay': True,
                                          'ketama': True})    

class RelatedSearchClassifier(object):
    
    model_file = 'related_search_classifier.model'
    features_file = 'features.dict'
    classifications_file = 'classifications.dict'
    
    def create_model(self, corpus, classifications, id_to_feature):        
        self.id_to_feature = id_to_feature

        # This it the kind of odd way scikits.learn returns probability distributions
        # It will be a numpy array of probabilities of each class. Each index corresponds
        # to the same index in an array of alphanumerically-sorted classifications
        classification_dict = dict(enumerate(sorted(set(classifications))))
        feature_to_id = dict((hash_key(feature), id) for id, feature in id_to_feature.iteritems())
        self.num_features = len(feature_to_id)

        memcache = get_cache()

        # Cache the whole class dict, it's small (length = num_issues) and will be used every time
        memcache.set(classification_dict_cache_key, classification_dict)
        
        # Keep this count around since we'll only be pulling down the features we need from memcache (no len)
        memcache.set(num_features_key, self.num_features) 

        # These are important, and while memcache will be the primary store,
        # save them to disk so we can reload them later it memcache dies
        pickle.dump(feature_to_id, open(os.sep.join([settings.RELATED_SEARCH_MODEL_BASE_DIR, self.features_file ]), 'w'))
        pickle.dump(classification_dict, open(os.sep.join([settings.RELATED_SEARCH_MODEL_BASE_DIR, self.classifications_file ]), 'w'))

        memcache.set_multi(feature_to_id)

        num_docs = len(corpus)
        num_features = len(id_to_feature)
        num_nonzeros = sum([len(doc) for doc in corpus])
                
        current_position, index_pointer = 0, [0]
                
        indices = numpy.empty((num_nonzeros,), dtype=numpy.int32)
        data = numpy.empty((num_nonzeros,), dtype=numpy.int32)
        for doc_num, doc in enumerate(corpus):
            next_position = current_position + len(doc)
            indices[current_position : next_position] = [feature_id for feature_id, _ in doc]
            data[current_position : next_position] = [cnt for feature_id, cnt in doc]
            index_pointer.append(next_position)
            current_position = next_position

        del corpus

        matrix = csc_matrix((data, indices, index_pointer), shape=(num_features, num_docs), dtype=numpy.int32)
        
        matrix = matrix.transpose()
        
        # Since the number of news stories about a particular issue 
        #For the purposes of this, assume there is no prior probability
        # e.g. if we have published more stories about Democracy, that doesn't mean
        # that democracy is any more relevant to a user's search than the environment
        model = MultinomialNB(fit_prior=False)
        classifications = numpy.array(classifications)

        model.fit(matrix, classifications)
        
        del matrix
        
        self.model =  model
        return self
        
    @classmethod
    def train(cls, corpus, classifications, id_to_feature):
        return RelatedSearchClassifier().create_model(corpus, classifications, id_to_feature)
        
    def save_model(self):
        joblib.dump(self.model, os.sep.join([settings.RELATED_SEARCH_MODEL_BASE_DIR, self.model_file ]) )

    @classmethod
    def get_model(cls):
        classifier = RelatedSearchClassifier()
        classifier.model = joblib.load(os.sep.join([settings.RELATED_SEARCH_MODEL_BASE_DIR, cls.model_file]), mmap_mode='r')
        mc = get_cache()
        classifier.classification_dict = mc.get(classification_dict_cache_key)
        classifier.num_features = mc.get(num_features_key)
        return classifier

    def classify(self, words):
        memcache = get_cache()
        doc_features = search_features(words)
        row_vals = []
        
        cache_keys = [hash_key(feature) for feature in doc_features]
        row_vals.extend(memcache.get_multi(cache_keys).values())        
        
        # Words are unknown
        if not row_vals:
            return []
        rows = numpy.array(row_vals)
        cols = numpy.array([0 for row in row_vals])
        data = numpy.array([1 for row in row_vals])
        matrix = csc_matrix( (data, (rows, cols)), shape=(self.num_features, 1) )
        matrix = matrix.transpose()
        probs = self.model.predict_log_proba(matrix)
        if not probs.any() or len(probs)==0:
            return []

        return sorted( [(self.classification_dict.get(idx), prob) for idx, prob in enumerate(probs[0])], key=lambda item: item[1], reverse=True)[:5]
