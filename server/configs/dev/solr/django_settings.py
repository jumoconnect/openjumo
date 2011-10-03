CACHE_BACKEND = 'memcached://HOSTNAME:11211/?timeout=86400'

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

SOLR_CONN = "http://localhost:8983/solr"

#DEV FACEBOOK INFO
FACEBOOK_APP_ID = ''
FACEBOOK_API_KEY = ''
FACEBOOK_SECRET = ''

#DEV AWS INFO
AWS_ACCESS_KEY = ''
AWS_SECRET_KEY = ''
AWS_PHOTO_UPLOAD_BUCKET = ""
