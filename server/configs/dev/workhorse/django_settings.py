import djcelery
###############################
#       CAMPAIGN SETTINGS     #
##############################


###############################
#       ADMIN SETTINGS       #
##############################
ADMIN_MEDIA_PREFIX = 'http://ADMINHOST/static/media/admin/'


###############################
#       STATIC SETTINGS       #
##############################
STATIC_URL = "http://jumostatic.s3.amazonaws.com"
NO_STATIC_HASH = True

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
#       SOLR  SETTINGS       #
##############################
SOLR_CONN = "http://SOLRHOST:8983/solr"


###############################
#       EMAIL SETTINGS       #
##############################
DEFAULT_FROM_EMAIL = 'no-reply@jumo.com'
EMAIL_HOST = ''
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USER_TLS = False


###############################
#      CELERY SETTINGS       #
##############################
BROKER_HOST = "localhost"


###############################
#      DJANGO SETTINGS       #
##############################
CACHE_BACKEND = 'memcached://HOSTNAME:11211/?timeout=86400'


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

djcelery.setup_loader()
