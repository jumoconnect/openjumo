from django.conf import settings
from lib.facebook import GraphAPI
import logging

DEFAULT_FB_IMAGE = '%s/static/img/logo-jumo_small.png' % settings.STATIC_URL

#FOR LOCAL DEV'ING
if settings.STATIC_URL == "":
    DEFAULT_FB_IMAGE = "http://jumostatic.s3.amazonaws.com/static/img/logo-jumo_small.png"

def post_donation_to_wall(user, entity):
    fb_name = "%s just donated to %s on Jumo" % (user.first_name, entity.get_name)
    fb_link = 'http://%s%s?utm_source=donate&utm_medium=facebook&utm_campaign=jumo' % (settings.HTTP_HOST, entity.get_url)
    _post_to_fb_wall(user.fb_access_token, '', {'name':fb_name,'link':fb_link,'picture':DEFAULT_FB_IMAGE})

def post_joined_to_wall(user):
    fb_name = '%s just joined Jumo.' % user.first_name
    fb_link = 'http://%s/%s?utm_source=newsignup&utm_medium=facebook&utm_campaign=jumo' % (settings.HTTP_HOST, user.username.encode('utf-8'))
    fb_desc = "Jumo connects individuals and organizations working to change the world."
    _post_to_fb_wall(user.fb_access_token, '', {'name':fb_name, 'link':fb_link, 'description':fb_desc, 'picture':DEFAULT_FB_IMAGE})


def _post_to_fb_wall(access_token, message='', attachments={}, profile_id=''):
    try:
        if not settings.BLOCK_FB_POSTS:
            GraphAPI(access_token).put_wall_post(message, attachments, profile_id)
        else:
            logging.info("This log is a simulated FB Wall Post. Params:\nmessage: %s\nattachments: %s\nprofile_id: %s" % (message, attachments, profile_id))
    except:
        logging.exception("FB WALL POST Exception")
