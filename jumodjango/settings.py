from celery.schedules import crontab
import djcelery
from django.conf.global_settings import EMAIL_BACKEND
import os, sys, logging
import subprocess



###############################
#            MISC            #
##############################
ROOT_PATH = os.path.dirname(__file__)


def to_absolute_path(path):
    return os.path.realpath(os.path.join(ROOT_PATH, path))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
DONATION_DEBUG = True #So we don't have to rely on django's debug.
BLOCK_FB_POSTS = True
#ROOT_PATH = os.path.dirname(__file__)

EXTRA_PATHS = [
     'lib',
]

for path in EXTRA_PATHS:
    path = to_absolute_path(path)
    if path not in sys.path:
        sys.path.append(path)

PROXY_SERVER = "PROXY_SERVER"
IGNORE_HTTPS = False



###############################
#       CAMPAIGN SETTINGS     #
##############################
MAX_PAYMENT_RETRIES = 1
PAYMENT_RETRY_SCHEDULE = [1, 3, 7]
JUMOEIN = ""


###############################
#       ADMIN SETTINGS       #
##############################

ADMINS = (
    ('Jumo Site Error', 'EMAIL@HERE'),
)
MANAGERS = ADMINS



###############################
#       STATIC SETTINGS       #
##############################

SERVE_STATIC_FILES = False
STATIC_URL = ''

NO_STATIC_HASH = False


###############################
#         DB SETTINGS        #
##############################


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jumodjango',
        'USER': 'jumo',
        'PASSWORD': 'DB_PASSWORD',
        'HOST': '',
        'PORT': '',
    },
}

#Map the db name to path of matching schema file.
DATABASE_CREATE_SCHEMAS = {
    'default':to_absolute_path('data/schema/jumodjango.schema'),
}

###############################
#       SOLR  SETTINGS       #
##############################
SOLR_CONN = 'http://SOLRSERVER:8983/solr'

###############################
#       DISQUS  SETTINGS     #
##############################
DISQUS_API_VERSION = '3.0'
DISQUS_FORUM_NAME = 'jumoprod'
DISQUS_SECRET_KEY = 'SOME_DISQUS_SECRET_KEY' #jumo_prod_app
DISQUS_PUBLIC_KEY = 'SOME_DISQUS_PUBLIC_KEY' #jumo_prod_app
DISQUS_DEV_MODE = 0 # 1 for dev, 0 for prod and stage

###############################
#       EMAIL SETTINGS       #
##############################

DEFAULT_FROM_EMAIL = 'FROM@USER'
EMAIL_HOST = ''
EMAIL_PORT = 25
EMAIL_HOST_USER = 'EMAIL@HOSTUSER'
EMAIL_HOST_PASSWORD = 'SOME_EMAIL_HOST_PASSWORD'
EMAIL_USER_TLS = False
CELERY_EMAIL_BACKEND = EMAIL_BACKEND

EMAIL_REAL_PEOPLE = False

CRYPTO_SECRET = r'CRYPTO_SECRET_HERE'


###############################
#      CELERY SETTINGS       #
##############################

# AMQP setup for Celery
BROKER_HOST = ""
BROKER_PORT = 5672
BROKER_USER = "jumo"
BROKER_PASSWORD = "SOME_BROKER_PASSWORD"
BROKER_VHOST = "/"

CELERY_DEFAULT_QUEUE = "now"
CELERY_QUEUES = {
    "now": {
        "binding_key": "task.#",
    },
    "deferred": {
        "binding_key": "deferred.#",
    },
    "billing": {
        "binding_key": "billing.#",
    },
}

CELERY_DEFAULT_EXCHANGE = "tasks"
CELERY_DEFAULT_EXCHANGE_TYPE = "topic"
CELERY_DEFAULT_ROUTING_KEY = "task.default"

CELERY_ROUTES = {"mailer.reader_tasks.send_jumo_reader_email":
                    {"queue": "deferred",
                    "routing_key": "deferred.reader"
                    },
                 "donation.tasks.process_donation":
                    {"queue": "billing",
                     "routing_key": "billing.process_donation"}
                 }

CELERY_IMPORTS = ('mailer.notification_tasks',
                  'mailer.reader_tasks',
                  'donation.tasks',
                  'mailer.messager_tasks',)

###############################
#      DJANGO SETTINGS       #
##############################

CONSOLE_MIDDLEWARE_DEBUGGER = True
APPEND_SLASH = False

#SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
CACHE_BACKEND = 'memcached://127.0.0.1:11211?timeout=86400'

AUTHENTICATION_BACKENDS = (
    'etc.backend.JumoBackend',
)

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1337
USE_I18N = True
USE_L10N = True

MEDIA_ROOT = to_absolute_path('static')
MEDIA_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/media/admin/'

HTTP_HOST = 'www.ogbon.com'

SECRET_KEY = 'SOME_SECRET_KEY_HERE'

MIDDLEWARE_CLASSES = (
    'etc.middleware.SSLMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
    'etc.middleware.DetectUserMiddleware',
    'etc.middleware.SourceTagCollectionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'etc.middleware.AddExceptionMessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    to_absolute_path('templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.auth',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'etc.context_processors.general',
)

INSTALLED_APPS = (
    'grappelli',
    'djcelery',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    #'django.contrib.sessions',
    'django.contrib.sites',
    #'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.humanize',
    'cust_admin',
    'users',
    'issue',
    'org',
    'data',
    'cust_admin',
    'etc',
    'api',
    'lib',
    'search',
    'utils',
    'mailer',
    'donation',
    'message',
    'sourcing',
    'popularity',
    'django_jenkins',
    'tastypie',
    'action',
    'entity_items',
    'commitment',
    'debug_toolbar',
    'discovery',
)


###############################
#        API SETTINGS        #
##############################
API_VERSION = 'v1'



###############################
#      TESTING SETTINGS       #
##############################
FIXTURE_DIRS = ("data/fixtures/",)
TEST_RUNNER = 'jumodjango.test.test_runner.JumoTestSuiteRunner'
JENKINS_TEST_RUNNER = 'jumodjango.test.test_runner.JumoTestSuiteRunner'
EXCLUDED_TEST_PACKAGES = ['django',]
PROJECT_APPS = (
    'users',
    'issue',
    'org',
    'mailer',
    'donation',
    'message',
    'sourcing',
    'popularity',
)


###############################
#      API KEY SETTINGS       #
##############################

MIXPANEL_TOKEN = 'SOME_MIXPANEL_TOKEN'

FACEBOOK_APP_ID = 'SOME_FACEBOOK_APP_ID'
FACEBOOK_API_KEY = 'SOME_FACEBOOK_API_KEY'
FACEBOOK_SECRET = 'SOME_FACEBOOK_SECRET'
FACEBOOK_ACCESS_TOKEN = 'SOME_FACEBOOK_ACCESS_TOKEN'

AWS_ACCESS_KEY = 'SOME_AWS_ACCESS_KEY'
AWS_SECRET_KEY = 'SOME_AWS_SECRET'
AWS_PHOTO_UPLOAD_BUCKET = "jumoimgs"

###############################################################
# DATAMINE SETTINGS - serve miner.views if IS_DATAMINE is True
###############################################################

IS_DATAMINE = False

###############################
# DATA SCIENCE TOOLKIT SETTINGS
###############################

# Use their AMI in production,
DSTK_API_BASE = "http://DSTK_HOST"

##############################
# DATAMINE SERVER
##############################

DATAMINE_BASE = "http://DATAMINE_HOST"

##############################
# LOGGER SETTINGS
##############################

LOG_DIR = '/cloud/logs/'


###############################
# DEBUG TOOLBAR SETTINGS
###############################
INTERNAL_IPS = ('127.0.0.1',)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': lambda x: False
}

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)

###############################
#      LOCAL SETTINGS       #
##############################

try:
    from local_settings import *
except ImportError:
    pass

if NO_STATIC_HASH:
    ASSET_HASH = 'abcdefg'
else:
    import git

    repo = git.Repo(to_absolute_path('.'), odbt=git.GitCmdObjectDB)
    ASSET_HASH = repo.head.commit.hexsha[0:7]
    del(repo)




if IS_DATAMINE:
    INSTALLED_APPS += ('miner',
                       'gunicorn')

    RELATED_SEARCH_MODEL_BASE_DIR = '/cloud/data'

LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
log = logging.getLogger('jumo')
