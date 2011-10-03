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
#       EMAIL SETTINGS       #
##############################
DEFAULT_FROM_EMAIL = 'no-reply@jumo.com'
EMAIL_HOST = ''
EMAIL_PORT = 25
EMAIL_HOST_USER = 'jumodev@jumo.com'
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

##############################
#      DSTK SETTINGS
##############################

DSTK_API_BASE = "http://DSTKHOST"

##############################
#      DATAMINE SETTINGS
##############################

IS_DATAMINE = True

###############################
#      DJANGO SETTINGS       #
##############################
CACHE_BACKEND = 'memcached://HOST:11211/?timeout=86400'
HTTP_HOST = "www.ogbon.com"


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

MIXPANEL_TOKEN = ''

djcelery.setup_loader()
