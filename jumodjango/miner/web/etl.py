import urllib2
import settings
import json
from miner.text.util import strip_control_characters

def html_to_story(doc, strip_control_chars=True):
    try:
        # Send the HTML over to Data Science Toolkit
        story = urllib2.urlopen( '/'.join([settings.DSTK_API_BASE, 'html2story']), data=doc).read()
        
        story = json.loads(story).get('story', '')
        
        if strip_control_chars:
            story = strip_control_characters(story)
        return story
    except urllib2.URLError, e:
        return ''