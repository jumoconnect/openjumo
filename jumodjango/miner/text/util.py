import nltk
import os
import string

# Fastest way to strip control characters in bulk

translations = {
    unicode: dict((ord(char), u' ') for char in u'\n\r\t'),
    str: string.maketrans('\n\t\r', '   ')
}

def strip_control_characters(s, translate_to=' '):
    return s.translate(translations[type(s)])
    
porter = nltk.PorterStemmer()

stopwords_path = os.path.realpath(os.path.dirname(__file__))

# Stopwords get filtered out before we do any analysis
stopwords = set([unicode(line.strip()).lower() for line in open(os.path.join(stopwords_path, 'stopwords.txt'))]) | set([unicode(word) for word in [
    # These are all technically tokens, filter them out too
    '.',',',';','"',"'",'?','(',')',':','-','_','`','...'
    ]])

# Regex pattern for splitting tokens
tokenizer = r'''(?x)
      ([A-Z]\.)+
    | \w+(-\w+)*
    | \$?\d+(\.\d+)?%?
    | \.\.\.
    | [][.,;"'?():-_`]
'''

def search_features(doc):
    words = [word.lower() for word in nltk.regexp_tokenize(doc, tokenizer) if word.lower() not in stopwords]
    unigrams = set([porter.stem(word) for word in words])
    bigrams = set(nltk.bigrams(words))
    return unigrams | bigrams
