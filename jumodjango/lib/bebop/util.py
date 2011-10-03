'''
Created on Jan 19, 2011

@author: al
'''

from lxml import etree
from lxml import builder
from lxml import objectify
from collections import defaultdict, deque, MutableSet
import os
import inspect
        
__E = objectify.ElementMaker(annotate=False)

def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

    
def memoize(f):
    arg_cache = {}
    def _new_f(arg):
        cache_it = True
        try:
            cached = arg_cache.get(arg, None)
            if cached is not None:
                return cached
        except TypeError:
            cache_it = False
        uncached = f(arg)
        if cache_it:
            arg_cache[arg] = uncached
        return uncached
    return _new_f

class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def to_camelcase(s):
    return ''.join([token.title() if i > 0 else token.lower() 
                    for i, token in enumerate(s.split('_'))])
    
@memoize
def _stringify(obj):
    # TODO: write your own PyObject > string conversion
    # or find a better way to do this
    return __E._dummy_node(obj).text

def _sorted_update(elem, d):
    elem.attrib.update(sorted(d.iteritems()))    

def get_class(obj):
    if inspect.isclass(obj):
        return obj
    else:
        return obj.__class__

def _collect_dependencies(obj, deps=defaultdict(set), refs=defaultdict(int)):
    for attr, value in obj.__dict__.iteritems():
        # Dependencies are XML orderings, so we don't care about non-XMLable attributes
        if hasattr(value, 'dependency'):
            # deps[SolrFieldTypes]=set(UniqueKey('foo'))
            deps[get_class(value.dependency)].add(value)
            # ref_counts[elem]==1 means that elem is waiting on 1 node to complete
            refs[value]+=1
            
        if hasattr(value, 'to_xml'):
            deps, refs = _collect_dependencies(value, deps, refs)
        elif hasattr(value, '__iter__') and hasattr(iter(value).next(), 'to_xml'):
            for val in value:
                deps, refs = _collect_dependencies(val, deps, refs)
            
    return deps, refs
        
def _to_xml(node):
    root=None
    # Topsort: schedule items with no dependers
    # Queue items are a tuple of (obj, parent)
    q=deque([(node, None)])
    dependency_graph, ref_counts = _collect_dependencies(node)
     
    #[q.append((value,node)) for value in node.__dict__.itervalues() if hasattr(value, 'to_xml') and ref_counts[value] == 0]

    while q:
        obj, parent = q.popleft()

        element = etree.Element(obj.tag)
        if obj is node:
            root=element
        
        definitions = {}
        options = {}
        for attr, transformed in obj.required.iteritems():
            definitions[transformed] = _stringify(getattr(obj, attr))

        for attr, value in obj.__dict__.iteritems():
            if attr in obj.required:
                definitions[obj.required[attr]] = _stringify(value)
            elif attr in obj.optional:
                options[obj.optional[attr]] = _stringify(value)
            elif attr=='value':
                element.text=value
            # For referencing elements without throwing them in the schema, use an underscore
            elif attr.startswith('_'):
                continue
            # Append children (recursive, but we don't need many levels)
            elif hasattr(value, 'to_xml') and not hasattr(value, 'dependency'):
                q.append((value, element))
            # Example: filters
            # TODO: are there any use cases where this is not the expected behavior?
            elif hasattr(value, '__iter__'):
                i = iter(value)
                first = i.next()
                del(i)
                if hasattr(first, 'to_xml') and not hasattr(value, 'dependency'):
                    #parent_node = parent if hasattr(first, 'dependency') else element
                    q.extend([(child, element) for child in value])

                
        _sorted_update(element, definitions)
        _sorted_update(element, options)
        
        

        cls = get_class(obj)
        if cls in dependency_graph:
            for dep in dependency_graph[cls]:
                ref_counts[dep]-=1
                if ref_counts[dep]==0:
                    q.appendleft((dep, parent))
            del(dependency_graph[cls])
                
        if parent is not None:
            parent.append(element)
    

                        
    return root

class BaseSolrXMLElement(object):
    required = {}
    options = []
    tag = None
    ref_count = 0
        
    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)
            
        # So class.to_xml will call _to_xml(cls) and self.to_xml will call _to_xml(self)
        self.to_xml = self.instance_to_xml
    
    def instance_to_xml(self):
        return _to_xml(self)
    
    
    @classmethod
    def to_xml(cls):
        return _to_xml(cls)
    
    
    @classproperty
    @classmethod
    def optional(cls):
        return dict([(attr, to_camelcase(attr))
                     for attr in cls.options])    

def single_value_tag(tag, value):
    return BaseSolrXMLElement(tag=tag, value=value)

class SingleValueTagsMixin(BaseSolrXMLElement):
    def __init__(self, camelcase=True, **kw):
        for attr, val in kw.iteritems():
            if val is None:
                continue
            if hasattr(val, 'to_xml'):
                # Ignore XML elements so they can be mixed in freely
                setattr(self, attr, val)
                continue
            
            tag = to_camelcase(attr) if camelcase else attr
            element = single_value_tag(tag, val)
            setattr(self, attr, element)
            
        super(SingleValueTagsMixin, self).__init__()
        
# OrderedSet, generally useful collection

KEY, PREV, NEXT = range(3)

class OrderedSet(MutableSet):
    def __init__(self, iterable=None):
        self.end = end = [] 
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[PREV]
            curr[NEXT] = end[PREV] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:        
            key, prev, next = self.map.pop(key)
            prev[NEXT] = next
            next[PREV] = prev

    def __iter__(self):
        end = self.end
        curr = end[NEXT]
        while curr is not end:
            yield curr[KEY]
            curr = curr[NEXT]

    def __reversed__(self):
        end = self.end
        curr = end[PREV]
        while curr is not end:
            yield curr[KEY]
            curr = curr[PREV]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = next(reversed(self)) if last else next(iter(self))
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

    def __del__(self):
        self.clear()                    # remove circular references
