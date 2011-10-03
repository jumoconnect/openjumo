import urllib

def get_twitter_share_url(url, text):
    twitter_params = urllib.urlencode({"url":url,"text":text})
    return "http://twitter.com/share?%s" % twitter_params

def get_facebook_share_url(url, text):
    facebook_params = urllib.urlencode({"u":url, "t":text})
    return "http://facebook.com/sharer.php?%s" % facebook_params
