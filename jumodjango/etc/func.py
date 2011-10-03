# -*- coding: utf8 -*-

import re
from unidecode import unidecode
import os, sys
from hashlib import md5 as hasher
import binascii
import settings


def gen_flattened_list(iterables):
    for item in iterables:
        if hasattr(item, '__iter__'):
            for i in item:
                yield i
        else:
            yield item

def crc32(val):
    return binascii.crc32(val) & 0xffffffff

# brennan added this
def wrap(text, width):
    """
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).
    """
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line)-line.rfind('\n')-1
                          + len(word.split('\n',1)[0]
                                ) >= width)],
                   word),
                  text.split(' ')
                  )

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.;:]+')

htmlCodes = (
    ('&amp;', '&'),
    ('&lt;', '<'),
    ('&gt;', '>'),
    ('&quot;', '"'),
    ('&#39;', "'"),
)

def escape_html(s):
    for bad, good in htmlCodes:
        s = s.replace(bad, good)
    return s

def slugify(text, delim='', lowercase=True):
    """ex: slugify(u'Шамиль Абетуллаев','')
    returns u'shamilabetullaev'"""
    text = escape_html(text)
    result = []
    if lowercase:
        text=text.lower()
    for word in _punct_re.split(text):
        decoded = _punct_re.split(unidecode(word))
        result.extend(decoded)
    result = unicode(delim.join(result))
    return result.lower() if lowercase else result


def salted_hash(val):
    hash = hasher(settings.CRYPTO_SECRET)
    hash.update(unicode(val, 'utf-8') if isinstance(val, str) else unicode(val))
    return hash.hexdigest()
