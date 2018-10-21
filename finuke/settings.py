"""
Django settings for finuke project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

import dj_email_url
from django.contrib import messages

_YES_VALUES = ['true', 'yes']
_NO_VALUES = ['false', 'no']

def _boolean_env_var(name, default=False):
    value = os.environ.get(name, '').lower().strip()

    if any(s.startswith(value) for s in _YES_VALUES):
        return True
    if any(s.startswith(value) for s in _NO_VALUES):
        return False

    return default


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET', 'h4otg99cb_n4y3^gc6xab)zojyt5_l%==(nig4uoc#$igm*b5e')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
BASE_URL = os.environ.get('BASE_URL', None)
DOMAIN_NAME = os.environ.get('DOMAIN_NAME', 'localhost')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'phonenumber_field',
    'webpack_loader',
    'crispy_forms',
    'custom_messages',
    'phones',
    'votes',
    'bureaux',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'finuke.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'finuke.context_processors.votation_name',
            ],
        },
    },
]

WSGI_APPLICATION = 'finuke.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'finuke',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/' + (BASE_URL or '') + 'static/'
STATIC_ROOT = os.environ.get('STATIC_ROOT')

# Email

# by default configured for mailhog sending
email_config = dj_email_url.parse(os.environ.get('SMTP_URL', 'smtp://localhost:1025/'))

EMAIL_FILE_PATH = email_config['EMAIL_FILE_PATH']
EMAIL_HOST_USER = email_config['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = email_config['EMAIL_HOST_PASSWORD']
EMAIL_HOST = email_config['EMAIL_HOST']
EMAIL_PORT = email_config['EMAIL_PORT']
EMAIL_BACKEND = email_config['EMAIL_BACKEND']
EMAIL_USE_TLS = email_config['EMAIL_USE_TLS']
EMAIL_USE_SSL = email_config['EMAIL_USE_SSL']

# Loggers

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'finuke': {
            'handlers': ['console'],
        },
    },
}

if not DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'journald': {
                'level': 'DEBUG',
                'class': 'systemd.journal.JournaldLogHandler',
            }
        },
        'loggers': {
            'finuke': {
                'handlers': ['journald'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.template': {
                'handlers': ['journald'],
                'level': 'INFO',
                'propagate': False,
            },
            'django': {
                'handlers': ['journald'],
                'level': 'DEBUG',
                'propagate': True
        },
    }
}

# Django webpack loader config
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'assets'),
)
WEBPACK_LOADER = {
    'DEFAULT': {
        'STATS_FILE': os.path.join(BASE_DIR, 'assets', 'webpack_bundles', 'webpack-stats.json'),
    }
}

# Cripsy settings

CRISPY_TEMPLATE_PACK = 'bootstrap3'
CRISPY_FAIL_SILENTLY = not DEBUG

# Debug toolbar settings
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        #'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]

# OVH Settings
OVH_SMS_DISABLE = _boolean_env_var('OVH_SMS_DISABLE', True)
OVH_SMS_SERVICE = os.environ.get('OVH_SMS_SERVICE')
OVH_APPLICATION_KEY = os.environ.get('OVH_APPLICATION_KEY')
OVH_APPLICATION_SECRET = os.environ.get('OVH_APPLICATION_SECRET')
OVH_CONSUMER_KEY = os.environ.get('OVH_CONSUMER_KEY')
SMS_BUCKET_MAX = 3
SMS_BUCKET_INTERVAL = 600
SMS_IP_BUCKET_MAX = 30
SMS_IP_BUCKET_INTERVAL = 3600


# redis settings
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/?db=0')
REDIS_MAX_CONNECTIONS = 3


PHONENUMBER_DEFAULT_REGION = 'FR'

MESSAGE_STORAGE = 'custom_messages.storage.CustomStorage'
MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}
MESSAGE_LEVEL = messages.DEBUG if DEBUG else messages.INFO


PROMETHEUS_USER = os.environ.get('PROMETHEUS_USER', 'prometheus')
PROMETHEUS_PASSWORD = os.environ.get('PROMETHEUS_PASSWORD', 'password')


CONTACT_EMAIL = os.environ.get('EMAIL_ADDRESS')
CONTACT_EMAIL_SERVER = 'mail.gandi.net'
CONTACT_EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')

FROM_EMAIL = os.environ.get('FROM_EMAIL', 'votation@lafranceinsoumise.fr')
EMAIL_NOT_CLOSED = 'https://mosaico.lafranceinsoumise.fr/emails/6cbbc59c-19bf-423f-880f-a7ee88db7fa4.html'
EMAIL_NO_RESULTS = 'https://mosaico.lafranceinsoumise.fr/emails/65f1fe4c-b83a-4808-82fa-049159d22bb7.html'
EMAIL_OPERATOR = 'https://mosaico.jlm2017.fr/emails/efeecd4d-1cbb-4bb6-9552-7d09a6251bcd.html'

ENABLE_ELECTRONIC_VOTE = _boolean_env_var('ELECTRONIC_VOTE', True)
ELECTRONIC_VOTE_REQUIRE_LIST = _boolean_env_var('ELECTRONIC_VOTE_REQUIRE_LIST', False)
ELECTRONIC_VOTE_REQUIRE_SMS = _boolean_env_var('ELECTRONIC_VOTE_REQUIRE_SMS', True)
ELECTRONIC_VOTE_REQUIRE_BIRTHDATE = _boolean_env_var('ELECTRONIC_VOTE_REQUIRE_BIRTHDATE', False)
ENABLE_PHYSICAL_VOTE = _boolean_env_var('PHYSICAL_VOTE', True)
VOTATION_NAME = os.environ.get('VOTATION_NAME', 'citoyenne')
VOTE_QUESTION = os.environ.get('VOTE_QUESTION', "Pensez-vous qu'être méchant c'est pas gentil ?")
VOTE_TEXT = os.environ.get('VOTE_TEXT', None)

ENABLE_VOTING = _boolean_env_var('ENABLE_VOTING', True)
ENABLE_CONTACT_INFORMATION = _boolean_env_var('ENABLE_CONTACT_INFORMATION', False)
ENABLE_PARTICIPATION = _boolean_env_var('ENABLE_PARTICIPATION', False)
ENABLE_HIDING_VOTERS = _boolean_env_var('ENABLE_HIDING_VOTERS', True)
MAIN_PAGE = os.environ.get('MAIN_PAGE', 'assistant_login')


THANK_YOU_URL = os.environ.get('THANK_YOU_URL', '/')


ELASTICSEARCH_HOST = 'localhost'
ELASTICSEARCH_ENABLED = _boolean_env_var("ELASTICSEARCH_ENABLED")
