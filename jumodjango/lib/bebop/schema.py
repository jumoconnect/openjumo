'''
Created on Jan 15, 2011

@author: al
'''

import os
from util import *
from collections import deque

class SolrFieldType(BaseSolrXMLElement):
    tag = "fieldType"
    required = {'solr_class': 'class',
                 'type_name': 'name'}
    options = ['indexed', 'stored',
               'sort_missing_first', 'sort_missing_last',
               'omit_norms', 'term_vectors',
               'compressed', 'multi_valued',
               'position_increment_gap'
               ]

class String(SolrFieldType): 
    solr_class='solr.StrField'
    type_name='string'
    omit_norms = True
    sort_missing_last = True

class UniqueId(SolrFieldType):
    solr_class='solr.UUIDField'
    type_name='uuid'    

class Boolean(SolrFieldType):
    solr_class = 'solr.BoolField'
    type_name = 'boolean'
    omit_norms = True
    sort_missing_last = True

class Date(SolrFieldType):
    solr_class = 'solr.DateField'
    type_name = 'date'
    
class Random(SolrFieldType):
    solr_class = 'solr.RandomSortField'
    type_name = 'random'

""" 
Numeric types 
"""

class Integer(SolrFieldType):
    solr_class = 'solr.IntField'
    type_name = 'int'
    omit_norms = True
    
class Long(SolrFieldType):
    solr_class = 'solr.LongField'
    type_name = 'long'
    omit_norms = True
    
class Float(SolrFieldType):
    solr_class = 'solr.FloatField'
    type_name = 'float'
    omit_norms = True
    
class Double(SolrFieldType):
    solr_class = 'solr.DoubleField'
    type_name = 'double'
    omit_norms = True
    
class SortableInteger(SolrFieldType):
    solr_class = 'solr.SortableIntField'
    type_name = 'sint'
    omit_norms = True
    sort_missing_last = True

class SortableLong(SolrFieldType):
    solr_class = 'solr.SortableLongField'
    type_name = 'slong'
    omit_norms = True
    sort_missing_last = True
    
class SortableDouble(SolrFieldType):
    solr_class = 'solr.SortableDoubleField'
    type_name = 'sdouble'
    omit_norms = True
    sort_missing_last = True

class SortableFloat(SolrFieldType):
    solr_class = 'solr.SortableFloatField'
    type_name = 'sfloat'
    omit_norms = True
    sort_missing_last = True

"""
Tokenizers
"""
    
class Tokenizer(BaseSolrXMLElement):
    solr_class = None
    tag = "tokenizer"
    required = {'solr_class': 'class'}
    
class WhitespaceTokenizer(Tokenizer):
    solr_class = 'solr.WhitespaceTokenizerFactory'
       
class StandardTokenizer(Tokenizer):
    solr_class = 'solr.StandardTokenizerFactory'
    
class KeywordTokenizer(Tokenizer):
    solr_class = 'solr.KeywordTokenizerFactory'
    
class LetterTokenizer(Tokenizer):
    solr_class = 'solr.LetterTokenizerFactory'
    
class HTMLStripWhitespaceTokenizer(Tokenizer):
    solr_class = 'solr.HTMLStripWhitespaceTokenizerFactory'
    
class HTMLStripStandardTokenizer(Tokenizer):
    solr_class = 'solr.HTMLStripStandardTokenizerFactory'
    
class PatternTokenizer(Tokenizer):
    """ To be subclassed further as needed, for instance:
    
    class GroupingPatternTokenizer(PatternTokenizer):
        pattern= "\'([^\']+)\'"
        group = 1
        
    """
    solr_class = 'solr.PatternTokenizerFactory'
    options = ['pattern', 'group']
        
"""
Filter classes
"""
        
class Filter(BaseSolrXMLElement):
    solr_class = None
    tag = "filter"
    options = []
    required = {'solr_class': 'class'}
    
class LowerCaseFilter(Filter):
    solr_class = "solr.LowerCaseFilterFactory"
    
class StandardFilter(Filter):
    solr_class = 'solr.StandardFilterFactory'
    
class TrimFilter(Filter):
    solr_class = 'solr.TrimFilterFactory'
    options = ['update_offsets']
    
class LengthFilter(Filter):
    solr_class = 'solr.LengthFilterFactory'
    options = ['min', 'max']
    
class RemoveDuplicatesFilter(Filter):
    """ Add this as your last analysis step"""
    solr_class = 'solr.RemoveDuplicatesTokenFilterFactory'
    
class ISOLatin1AccentFilter(Filter):
    """ Normalize accented characters """
    solr_class = 'solr.ISOLatin1AccentFilterFactory'
    
class CapitalizationFilter(Filter):
    solr_class = 'solr.CapitalizationFilterFactory'

class PatternReplaceFilter(Filter):
    """ To be subclassed further as needed"""
    solr_class = 'solr.PatternReplaceFilterFactory'
    options = ['pattern', 'replacement', 'replace']    
    
""" 
CharFilterFactories are available only for Solr 1.4 and higher
"""

class MappingCharFilter(Filter):
    solr_class = 'solr.MappingCharFilterFactory'
    
class PatternReplaceCharFilter(Filter):
    """ To be subclassed further as needed"""
    solr_class = 'solr.PatternReplaceCharFilterFactory'
    options = ['pattern', 'replacement', 'replace']
    
class HTMLStripCharFilter(Filter):
    """ Strips out HTML embedded in text. Good for blog posts, etc.
    that are not HTML documents themselves but may contain HTML """
    solr_class = 'solr.HTMLStripCharFilterFactory'
    
"""
WordDelimiter - highly customizable, don't just use mine
"""
    
class WordDelimiterFilter(Filter):
    solr_class = 'solr.WordDelimiterFilterFactory'
    options = ['generate_word_parts',
                'generate_number_parts', 'catenate_words',
                'catenate_numbers', 'catenate_all', 
                'split_on_case_change', 'split_on_numerics',
                'stem_english_possessive', 'preserve_original']
        
class EnglishPorterFilter(Filter):
    solr_class = 'solr.EnglishPorterFilterFactory'
    options = ['protected']
    
class SnowballPorterFilter(Filter):
    solr_class = 'solr.SnowballPorterFilterFactory'
    options = ['language']
    
class SynonymFilter(Filter):
    solr_class = 'solr.SynonymFilterFactory'
    options = ['synonyms', 'ignore_case', 'expand']
    
class StopFilter(Filter):
    solr_class = 'solr.StopFilterFactory'
    options = ['words', 'ignore_case']
    
"""
Phonetic filters for sounds-like analysis
"""
    
class DoubleMetaphoneFilter(Filter):
    solr_class = 'solr.DoubleMetaphoneFilterFactory'
    options = ['inject', 'max_code_length']

class PhoneticFilter(Filter):
    solr_class = 'solr.PhoneticFilterFactory'
    options = ['encoder', 'inject']    
    
class MetaphoneFilter(PhoneticFilter):
    encoder = 'Metaphone'

class SoundexFilter(PhoneticFilter):
    encoder = 'Soundex'
    
class RefinedSoundexFilter(PhoneticFilter):
    encoder = 'RefinedSoundex'

"""
NGramFilter does substring matches based on a gram size that you specify.
Use with caution...
"""

class NGramFilter(Filter):
    solr_class = 'solr.NGramFilterFactory'
    options = ['min_gram_size', 'max_gram_size']
    min_gram_size = 2
    max_gram_size = 15
   
class EdgeNGramFilter(NGramFilter):
    solr_class = 'solr.EdgeNGramFilterFactory'
    options = NGramFilter.options + ['side']
    
""" 
Analyzer
"""
    
class Analyzer(BaseSolrXMLElement):
    INDEX = 'index'
    QUERY = 'query'
    
    tag = 'analyzer'
    options = ['type']
    
    tokenizer = WhitespaceTokenizer
    filters = ()


"""
All text-based field_types
"""

class BaseText(SolrFieldType):
    solr_class = 'solr.TextField'
    position_increment_gap = 100
    
class SimpleTokenizedText(BaseText):
    type_name = 'text_ws'
    anaylzer = Analyzer(tokenizer=WhitespaceTokenizer)

class Text(BaseText):
    type_name = 'text'
    
    index_analyzer = Analyzer(type=Analyzer.INDEX,
                              tokenizer = WhitespaceTokenizer,
                              filters = (StopFilter(ignore_case=True, words='stopwords.txt', enable_position_increments=True),
                                         WordDelimiterFilter(generate_word_parts=1, generate_number_parts=1, catenate_words=1, 
                                                             catenate_numbers=1, catenate_all=0, split_on_case_change=1),
                                         LowerCaseFilter,
                                         ISOLatin1AccentFilter,
                                         EnglishPorterFilter(protected='protwords.txt'),
                                         RemoveDuplicatesFilter
                                         )
                        )
    query_analyzer = Analyzer(type=Analyzer.QUERY,
                              tokenizer = WhitespaceTokenizer,
                              filters = (SynonymFilter(synonyms='synonyms.txt', ignore_case=True, expand=True),
                                         StopFilter(ignore_case=True, words='stopwords.txt'),
                                         WordDelimiterFilter(generate_word_parts=1, generate_number_parts=1, catenate_words=1, 
                                                             catenate_numbers=0, catenate_all=0, split_on_case_change=1),
                                         LowerCaseFilter,
                                         ISOLatin1AccentFilter,
                                         EnglishPorterFilter(protected='protwords.txt'),
                                         RemoveDuplicatesFilter
                                         )
                              
                              )
class TextTight(BaseText):
    type_name = 'textTight'
    
    analyzer = Analyzer(tokenizer = WhitespaceTokenizer,
                        filters = (SynonymFilter(synonyms='synonyms.txt', ignore_case=True, expand=False),
                                   StopFilter(ignore_case=True, words='stopwords.txt'),
                                   WordDelimiterFilter(generate_word_parts=0, generate_number_parts=0, catenate_words=1, catenate_numbers=1, catenate_all=0),
                                   LowerCaseFilter,
                                   EnglishPorterFilter(protected='protwords.txt'),
                                   RemoveDuplicatesFilter
                                   )
                        )

class Title(BaseText):
    type_name = 'title'
    
    analyzer = Analyzer(tokenizer = WhitespaceTokenizer,
                        filters = (StopFilter(ignore_case=True, words='stopwords.txt'),
                                   WordDelimiterFilter(generate_word_parts=0, generate_number_parts=0, catenate_words=1, catenate_numbers=1, catenate_all=0),
                                   LowerCaseFilter,
                                   ISOLatin1AccentFilter,
                                   RemoveDuplicatesFilter
                                   )
                        )

class TextSpell(BaseText):
    type_name = 'textSpell'
    stored = False
    multi_valued = True
    
    index_analyzer = Analyzer(type=Analyzer.INDEX,
                              tokenizer = StandardTokenizer,
                              filters = (LowerCaseFilter,
                                         SynonymFilter(synonyms='synonyms.txt', ignore_case=True, expand=True),
                                         StopFilter(ignore_case=True, words='stopwords.txt'),
                                         StandardFilter,
                                         RemoveDuplicatesFilter
                                         )
                              )
    query_analyzer = Analyzer(type=Analyzer.QUERY,
                              tokenizer=StandardTokenizer,
                              filters=(LowerCaseFilter,
                                       StopFilter(ignore_case=True, words='stopwords.txt'),
                                       StandardFilter,
                                       RemoveDuplicatesFilter
                                       )
                              )

class TextSpellPhrase(BaseText):
    type_name = 'textSpellPhrase'

    analyzer = Analyzer(tokenizer=KeywordTokenizer,
                        filters = (LowerCaseFilter,
                                   )
                        )

class AlphaOnlySort(BaseText):
    type_name = 'alphaOnlySort'
    omit_norms = True
    sort_missing_last = True
    
    analyzer = Analyzer(tokenizer = KeywordTokenizer,
                        filters = (LowerCaseFilter,
                                   TrimFilter,
                                   PatternReplaceFilter(pattern='([^a-z])', replacement='', replace='all')
                                   )
                        )


class Ignored(SolrFieldType):
    type_name = 'ignored'
    solr_class = 'solr.StrField'
    indexed = False
    stored = False

class SolrFieldTypes(BaseSolrXMLElement):
    tag = 'types'

    types = (String, Boolean, UniqueId,
             Integer, Long, Float, Double,
             SortableInteger, SortableLong,
             SortableFloat, SortableDouble,
             Date, Random, SimpleTokenizedText, 
             Text, TextTight, Title, TextSpell,
             TextSpellPhrase, AlphaOnlySort, Ignored)    
    
    def __init__(self, *args):
        self.types = tuple(args)

class SolrSchemaField(BaseSolrXMLElement):
    tag = 'field'
    required = dict([(attr, attr)
                    for attr in ['name', 'type']])
    options = ['indexed', 'stored', 'multi_valued', 'sort_missing_last',
               'sort_missing_first', 'compressed', 'term_vectors', 'omit_norms',
               'position_increment_gap']

    def __init__(self, name, type):
        super(SolrSchemaField, self).__init__(name=name, type=type.type_name)


class SolrSchemaFields(BaseSolrXMLElement):  
    tag = 'fields'
    fields = ()
    dependency = SolrFieldTypes
    
    def __init__(self, *args):
        super(SolrSchemaFields, self).__init__(fields=args)

class UniqueKey(BaseSolrXMLElement):
    tag = 'uniqueKey'
    dependency = SolrSchemaFields
    value = None

    def __init__(self, name=None):
        self.value = name

class SolrSchema(BaseSolrXMLElement):
    tag = 'schema'
    required = dict([(attr, attr)
                    for attr in ['name', 'version']])

    def __init__(self, name, version='1.1',
                    field_types=SolrFieldTypes(),
                    fields=SolrSchemaFields(), **kw):
        self.name = name
        self.version = version
        self.field_types = field_types
        self.names_to_fields = dict([(field_type.type_name, field_type)
                                     for field_type in field_types.types])
        self.fields = fields
        super(SolrSchema, self).__init__(**kw)

def generate_schema(schema, path = 'solr/conf/schema.xml'):
    ensure_dir(os.path.dirname(path))
    
    tree = etree.ElementTree(schema.to_xml())
    tree.write(path, encoding='utf-8', xml_declaration=True, pretty_print=True)                    