#!/usr/bin/python
import logging
import gdata.youtube.service
import json
import re
import time
import urllib
from urlparse import urlsplit, urlunsplit, parse_qs

YQL_URL = "http://query.yahooapis.com/v1/public/yql?"
YQL_PARAMS = {"q":"",
              "format":"json",
              "env":"store://datatables.org/alltableswithkeys",
             }


#All regex is evil magic cast with the devils own spells.
def do_voodoo_regex(subject, regex_spells):
  result = None
  for regex_match in regex_spells:
    res = regex_match.search(subject)
    if res and res.groups() and len(res.groups()) > 0:
      result = res.groups()[0]
      break
  return result


def do_yql_query_thang(query):
  return_value = None
  try:
    YQL_PARAMS["q"] = query
    params = urllib.urlencode(YQL_PARAMS)
    string_result = urllib.urlopen(YQL_URL+params).read()
    result = json.loads(string_result)
    if result.has_key('query') and result["query"].has_key('results') and result["query"]["results"]:
      return_value = result["query"]["results"]
  except Exception, err:
    logging.exception(query)
    raise err
  finally:
    #time.sleep(2.5) #enforce sleep
    pass

  return return_value

def facebook_id_magic(subject):
  graph_url = 'http://graph.facebook.com/%s'

  regex_spells = [re.compile('(?:www|).facebook.com/(?:pages|people)/.*/([0-9]+)'),
                  re.compile('(?:www|).facebook.com/profile.php\?id=([0-9]+)'),
                  re.compile('(?:www|).facebook.com/(?!pages|group|search|people)([a-zA-Z0-9]+)')]

  identifier = None
  #Did they give us a url?
  if subject.find("facebook.com") >= 0:
    identifier = do_voodoo_regex(subject, regex_spells)

  if not identifier:
    #Maybe they gave us something good.
    identifier = subject.replace(' ','')

  #No need to try catch as we WANT the exception if it fails.
  url = graph_url % identifier
  string_result = urllib.urlopen(url).read()
  result = json.loads(string_result)

  #time.sleep(1)
  if result and result.has_key('id'):
    return int(result['id']) #Evil wins again.
  #Fail
  return None


def twitter_id_magic(subject):
  screen_name_query = "SELECT * FROM twitter.users WHERE screen_name='%s'"
  id_query = "SELECT * FROM twitter.users WHERE id='%s'"

  regex_spells = [re.compile('twitter.com/#?!?/?([a-zA-Z0-9]+)(\/|\||$)')]

  identifier = None
  if subject.find("twitter.com") >= 0:
    identifier = do_voodoo_regex(subject, regex_spells)

  if not identifier:
    identifier = subject.replace(' ','')

  query = screen_name_query
  if identifier.isdigit():
    query = id_query

  result = do_yql_query_thang(query % identifier)
  if result:
    return result["user"]["screen_name"]
  return ""


def youtube_id_magic(subject):
  id_query = "SELECT * FROM youtube.user WHERE id='%s'"
  regex_spells = [re.compile('youtube.com/(?:user\/|)(?!watch|user)([a-zA-Z0-9]+)')]

  identifier = None
  if subject.find("youtube.com") >= 0:
    identifier = do_voodoo_regex(subject, regex_spells)

  if not identifier:
    identifier = subject.replace(' ', '')

  result = do_yql_query_thang(id_query % identifier)
  if result and result["user"]["id"]:
    return result["user"]["id"]
  return ""


def youtube_url_magic(url):
    try:
        return_data = {"title":"", "description":"", "url":url, "image":"", "image_choices":[], "source_id":""}
        main_url_split= urlsplit(url)
        if 'youtube.com' in main_url_split.netloc or 'youtube' in main_url_split.netloc:
            qparams = parse_qs(main_url_split.query)
            id = None
            re_query = "(?<=v=)[a-zA-Z0-9-]+(?=&)|(?<=[0-9]/)[^&\n]+|(?<=v=)[^&\n]+"
            re_result = re.findall(re_query, url)
            if len(re_result) > 0:
                id = re_result[0]

            if id is not None:
                yt_service = gdata.youtube.service.YouTubeService()
                yt_service.ssl = False
                entry = yt_service.GetYouTubeVideoEntry(video_id=id)
                vid = entry.media
                return_data = dict(title = vid.title.text,
                                   description = vid.description.text,
                                   url = vid.content[0].url,
                                   image_choices=[img.url for img in vid.thumbnail],
                                   source_id = id
                                   )
        return return_data
    except Exception as e:
        import logging
        logging.exception(e)
    return None



def flickr_id_magic(subject):
  url_query = "SELECT * FROM flickr.urls.lookupuser WHERE url='%s'"
  id_query = "SELECT * FROM flickr.people.getInfo WHERE user_id='%s'"
  username_query = "SELECT * FROM flickr.getidfromusername where username='%s'"
  username_query2 = "SELECT * FROM flickr.people.findbyusername WHERE username='%s'"  #Yes...there are two calls that behave differently.

  if subject.find("flickr.com") >= 0:
    result = do_yql_query_thang(url_query % subject)
  elif subject.find("@") >= 0: #flickr's got weird user ids
    result = do_yql_query_thang(id_query % subject)
  else:
    result = do_yql_query_thang(username_query % subject)
    if not result:
      print "Doing backup username query...so lame."
      result = do_yql_query_thang(username_query2 % subject)

  #Flickr's crazy...some of their usernames are sentences so we're taking id instead.
  if result:
    if result.has_key("user"):
      return result["user"]["id"]
    elif result.has_key("person"):
      return result["person"]["id"]
    elif result.has_key("user_id"):
      return result["user_id"]
  return ""


def vimeo_id_magic(subject):
  id_query = "SELECT * FROM vimeo.user.info WHERE username='%s'"
  regex_spells = [re.compile('vimeo.com/([a-zA-Z0-9]+)(/[a-zA-Z0-9]+)?')]

  identifier = None
  if subject.find("vimeo.com") >= 0:
    identifier = do_voodoo_regex(subject, regex_spells)

  if not identifier:
    identifier = subject.replace(' ','')

  result = do_yql_query_thang(id_query % identifier)
  #Vimeo doesn't actually include a username in their result so just use what we have
  if result and result.has_key("users") and result["users"].has_key("user"):
    return identifier
  return ""
