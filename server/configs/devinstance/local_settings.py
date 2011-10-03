DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jumodjango',
        'USER': 'jumo',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    },
}

PROXY_SERVER = ""
BROKER_HOST = ""
BROKER_PORT = 5672
BROKER_USER = ""
BROKER_PASSWORD = ""
BROKER_VHOST = "/"

#Facebook settings
FACEBOOK_APP_ID = ''
FACEBOOK_API_KEY = ''
FACEBOOK_SECRET = ''


STATIC_URL = "http://localhost:8000"
HTTP_HOST = "localhost:8000"
ADMIN_MEDIA_PREFIX = STATIC_URL + '/static/media/admin/'
#ADMIN_MEDIA_PREFIX = 'http://static.jumo.com/static/media/admin/'

IGNORE_HTTPS = True
CELERY_ALWAYS_EAGER=True

DSTK_API_BASE = "http://DSTKSERVER"

# Make sure to fill in S3 info
AWS_ACCESS_KEY = ''
AWS_SECRET_KEY = ''
AWS_PHOTO_UPLOAD_BUCKET = ""

