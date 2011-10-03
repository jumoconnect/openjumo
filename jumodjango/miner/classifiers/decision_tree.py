'''
Created on Jul 15, 2011

@author: al
'''

from collections import defaultdict, deque, OrderedDict, Hashable
from itertools import chain
from classifier import *
import math
import logging
import os

log = logging.getLogger('miner.classifiers')


class nested_dict(dict):
    def __getitem__(self, keys):
        d = self
        if hasattr(keys, 'items'):
            keys = keys.items()
        if not hasattr(keys, '__iter__'):
            return dict.__getitem__(self, keys)
        keys = chain(*keys)
        for key in keys:
            d = dict.__getitem__(d, key)
        return d

    def __setitem__(self, keys, value):
        d = self
        if not hasattr(keys, '__iter__'):
            dict.__setitem__(self, keys, value)
            return

        if hasattr(keys, 'items'):
            keys = keys.items()

        keys = list(chain(*keys))

        for i, key in enumerate(keys[:-1]):
            try:
                d = d[key]
            except KeyError:
                dict.__setitem__(d, key, {})
                d = d[key]
                continue

        dict.__setitem__(d, keys[-1], value)

class DecisionTree(Classifier):

    @classmethod
    def create_model(cls, training_instances):
        Q = deque([None])
        working_set = []
        current_decision = None

        features = cls.get_features()

        def entropy(cat_totals):
            total = sum(cat_totals)
            return sum([ -(float(cat_total)/total) * math.log((float(cat_total)/total), 2)
                            for cat_total in cat_totals])

        ret = nested_dict()

        attr_index = defaultdict(lambda: defaultdict(set))
        for instance in training_instances:
            for attr in features:
                val = cls.select_feature(instance, attr)
                attr_index[attr][val].add(instance)

        # Iterative breadth-first search algorithm
        while Q:
            conditions = Q.popleft()
            # Initial node
            if conditions is None:
                conditions = OrderedDict()
                base_working_set = set(training_instances)

            if current_decision:
                features.remove(current_decision)

            if not features:
                break

            # Triple default dict OH YEAAAAAH
            classification_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

            # Working set would be all items given the conditions of this iteration (e.g. country_is_us=False, us_city=True)
            working_set = base_working_set
            for attr, val in conditions.iteritems():
                items = attr_index[attr][val]
                working_set = working_set & items

            for instance in working_set:
                for attr in features:
                    val = cls.select_feature(instance, attr)
                    classification_dict[attr][val][instance.label] += 1

            """
            classification_dict looks like this:

            {'country_is_us':
                {True: {'US': 9,
                        'International': 0
                        },
                 False: {'US': 1,
                         'International': 8}
                 }
            }
            """

            info_gains = defaultdict(float)

            for key, value_dict in classification_dict.iteritems():
                total_info = defaultdict(int)
                for distinct_value, class_dict in value_dict.iteritems():
                    info_gains[key] += entropy(class_dict.values())
                    for label, num in class_dict.iteritems():
                        total_info[label] += num

                total_info_gain = entropy(total_info.values())
                info_gains[key] = total_info_gain - info_gains[key]

            current_decision = sorted(info_gains, key=lambda attr: info_gains[attr], reverse=True)[0]

            for attr in attr_index[current_decision]:
                labels = classification_dict[current_decision][attr].keys()
                new_conditions = conditions.copy()
                new_conditions[current_decision] = attr
                if len(labels) > 1:
                    Q.append(new_conditions)
                elif len(labels) == 1:
                    ret[new_conditions] = labels[0]

        return ret


    @classmethod
    def classify(cls, node):
        if not hasattr(cls, 'decision_tree'):
            current_object = cls.get_model()
        else:
            current_object = cls.model

        if not current_object:
            log.warn("No decision tree model available, could not classify object '%s'" % unicode(node))
            return None

        node = cls(node)
        while True:
            attr = current_object.keys()[0]
            val = cls.select_feature(node, attr)
            current_object = current_object[attr].get(val)
            if current_object is None:
                log.info("Couldn't classify object: %s, attribute '%s' with value '%s' does not exist in decision tree" % (cls.__name__, attr, val))
                return None
            elif isinstance(current_object, basestring):
                log.debug("Successfully classified object: %s as '%s'" % (unicode(node), current_object))
                return current_object

__all__ = ['DecisionTree', 'feature', 'nested_dict']