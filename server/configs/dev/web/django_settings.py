##### DEV ######

import djcelery
###############################
#       CAMPAIGN SETTINGS     #
##############################


###############################
#       ADMIN SETTINGS       #
##############################
ADMIN_MEDIA_PREFIX = 'http://jumostatic.s3.amazonaws.com/static/media/admin/'


###############################
#       STATIC SETTINGS       #
##############################
STATIC_URL = "http://jumostatic.s3.amazonaws.com"


###############################
#         DB SETTINGS        #
##############################
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jumodjango',
        'USER': 'jumo',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }

}

###############################
#       DISQUS  SETTINGS     #
##############################
DISQUS_API_VERSION = '3.0'
DISQUS_FORUM_NAME = ''
DISQUS_SECRET_KEY = '' # jumo_test_app
DISQUS_PUBLIC_KEY = '' # jumo_test_app
DISQUS_DEV_MODE = 1 # 1 for dev, 0 for prod and stage


###############################
#       EMAIL SETTINGS       #
##############################
DEFAULT_FROM_EMAIL = 'no-reply@jumo.com'
EMAIL_HOST = ''
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USER_TLS = False
EMAIL_BACKEND = 'mailer.backend.JumoEmailBackend'


###############################
#      CELERY SETTINGS       #
##############################

# AMQP setup for Celery
BROKER_HOST = ""
BROKER_PORT = 5672
BROKER_USER = "jumo"
BROKER_PASSWORD = ""
BROKER_VHOST = "/"


###############################
#      DJANGO SETTINGS       #
##############################
CACHE_BACKEND = 'memcached://HOSTNAME:11211/?timeout=86400'
HTTP_HOST = "www.ogbon.com"

###############################
#      DATAMINE SETTINGS
###############################

DATAMINE_BASE = "http://DATAMINEBASE"

###############################
#      API KEY SETTINGS       #
##############################
#DEV FACEBOOK INFO
FACEBOOK_APP_ID = ''
FACEBOOK_API_KEY = ''
FACEBOOK_SECRET = ''

#DEV AWS INFO
AWS_ACCESS_KEY = ''
AWS_SECRET_KEY = ''
AWS_PHOTO_UPLOAD_BUCKET = ""

# DATA SCIENCE TOOLKIT
DSTK_API_BASE = "http://DSTK_HOST"

MIXPANEL_TOKEN = ''

djcelery.setup_loader()
