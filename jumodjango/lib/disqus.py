from django.conf import settings

import base64
import hashlib
import hmac
import time
import json
import logging

'''
  Commenting out DisqusAPI for current integration, 
  but for future features, like 'top comments', will need to install discus-python
  ref: https://github.com/disqus/disqus-python/blob/master/README.rst
'''
# from disqusapi import DisqusAPI

'''
    returns a user params json object base-64 encoded then hmac'd with our private API key (settings.DISQUS_SECRET_KEY)
    the disqus plugin requires this to exist on the integrating page as a JS var named 'remote_auth_s3'
    ref: http://docs.disqus.com/developers/sso/
    data obj 
    {
        id - any unique user ID number associated with that account within your user database. This will be used to generate a unique username to reference in the Disqus system.
        username - The displayed name for that account
        email - The registered email address for that account
        avatar (optional) - A link to that user's avatar
        url (optional) - A link to the user's website
    }
'''
def get_sso_auth(user):
    # avoid conflicts with production users
    devprefix = ''
    if settings.DISQUS_DEV_MODE == 1:
        devprefix = 'dev_'
        
    if user and user.is_authenticated():
        data = json.dumps({
            'id': '%s%s' % (devprefix, user.id),
            'username': user.get_name,
            'email': user.email,
            'avatar': user.get_image_small,
            # need FQDN with protocol for 'url' here b/c disqus has 
            # stupid parsing logic when displaying the link- they
            # simply cut off the first 7 characters of the the value always assuming that's 
            # the protocol and display the rest. wow. so, if you have a secure link https://,
            # which is 8 characters, they display the last forward slash, "/rest_of_url".. is it
            # that hard to parse for protocols in urls?  apparently.
            'url': "http://%s%s" % (settings.HTTP_HOST, user.get_url)
        })
    else:
        # sending empty json object logs out
        data = json.dumps({});
    
    # encode the data to base64
    message = base64.b64encode(data)
    # generate a timestamp for signing the message
    timestamp = int(time.time())
    # generate our hmac signature
    sig = hmac.HMAC(settings.DISQUS_SECRET_KEY, '%s %s' % (message, timestamp), hashlib.sha1).hexdigest()
    return "%(message)s %(sig)s %(timestamp)s" % dict(
        message=message,
        timestamp=timestamp,
        sig=sig,
    )