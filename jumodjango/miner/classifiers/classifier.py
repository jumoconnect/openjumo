'''
Created on Jul 20, 2011

@author: al
'''

from collections import defaultdict, Hashable

features = defaultdict(set)
defined_features = set()

def register_feature(cls, obj):
    # properties
    if hasattr(obj, 'fget'):
        name = obj.fget.__name__
    # classmethods
    elif hasattr(obj, '__func__'):
        name = obj.__func__.__name__
    # instancemethods
    else:
        name = obj.__name__

    features[cls].add(name)

def feature(f):
    defined_features.add(f)
    return f

class ClassifierMeta(type):
    def __init__(cls, name, bases, dict):
        super(ClassifierMeta, cls).__init__(name, bases, dict)
        for name, obj in dict.iteritems():
            if isinstance(obj, Hashable) and obj in defined_features:
                register_feature(cls, obj)

class Classifier(object):
    __metaclass__ = ClassifierMeta

    @classmethod
    def get_features(cls):
        return features[cls].copy()

    @classmethod
    def select_feature(cls, instance, attr):
        try:
            val = getattr(instance, attr)
        except AttributeError:
            try:
                val = getattr(cls, attr)
            except AttributeError:
                raise Exception('Attribute "%s" was not found on either the training instance "%s" or class "%s"' % (attr, instance, cls))

        if callable(val):
            return val(instance)
        else:
            return val

    @classmethod
    def train(cls, data):
        training_instances = cls.prepare_data(data)
        cls.model = cls.create_model(training_instances)
        return cls.model

    @classmethod
    def prepare_data(cls, data):
        """ No-op, override as needed """
        return data

    @classmethod
    def create_model(cls, training_instances):
        raise NotImplementedError('Children must implement their own')

    @classmethod
    def get_model(cls):
        raise NotImplementedError('Children must implement their own')