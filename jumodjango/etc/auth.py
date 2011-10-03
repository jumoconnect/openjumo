from etc.user import create_salt_cookie
from datetime import datetime, timedelta
from django.contrib.auth import authenticate
from etc.constants import ACCOUNT_COOKIE_SALT, ACCOUNT_COOKIE
from lib.facebook import GraphAPI
import logging
from users.models import User

def attempt_login(request, email_or_username, password):
    auth_user = authenticate(username=email_or_username, password=password)
    if auth_user is not None:
        user = User.objects.get(user_ptr=auth_user.id)
        login(request, user)
        return user
    return None

#Same as django's but with some fb magic and minus session work.
def login(request, user):
    user = user if user is not None else request.user
    user.last_login = datetime.now()
    user.save()

    if user.fb_access_token:
        #Update Facebook Friends
        try:
            fb = GraphAPI(user.fb_access_token)
            fb_friends = fb.request('/me/friends')
            user.update_fb_follows([item['id'] for item in fb_friends['data']])
        except Exception, err:
            logging.exception("Error importing facebook friends.")

    if hasattr(request, 'user'):
        request.user = user

#Same as django's minus session work
def logout(request):
    if hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

def set_auth_cookies(response, user):
    response.set_cookie(ACCOUNT_COOKIE, user.id, expires = datetime.now() + timedelta(days=365), path='/')
    response.set_cookie(ACCOUNT_COOKIE_SALT, create_salt_cookie(user.id), expires = datetime.now() + timedelta(days=365), path='/')
    return response

def unset_auth_cookies(response):
    response.delete_cookie(ACCOUNT_COOKIE)
    response.delete_cookie(ACCOUNT_COOKIE_SALT)
    return response
