from frekenbok.settings import *

ALLOWED_HOSTS = []

SECRET_KEY = '_23n6hl)*4z)s+bn*7o7wk(ce@v2e7@#l=iv%4%5=4ua!5@%+='

DEBUG = True

MEDIA_URL = '/media/'
MEDIA_ROOT = '/tmp/media'

STATIC_URL = '/static/'
STATIC_ROOT = '/tmp/static'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '..', 'development.sqlite3'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(funcName)s [pid %(process)d] [th %(thread)d] %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'accountant.models': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
        'accountant.tests': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}

SMS_SECRET_KEY = 'Gx2spoTD4VrTlmCq0A/9W56jhVusc77/Fpe8QI+m3/TYyzyMNUWfUpLzZjt5Ol5b0iQlGHaE2DvP'