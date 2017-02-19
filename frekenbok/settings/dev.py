import re
import pytz

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
        'accountant': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
    }
}

SMS_SECRET_KEY = 'Gx2spoTD4VrTlmCq0A/9W56jhVusc77/Fpe8QI+m3/TYyzyMNUWfUpLzZjt5Ol5b0iQlGHaE2DvP'
SMS_PARSERS = {
    'Tinkoff': {
        'regexp': re.compile(
            r'(?P<action>[\w ]+)\. (?P<account>[\w *_]+)\. '
            r'Summa (?P<amount>[\d\.]+) (?P<currency>[A-Z]{3})\. '
            r'(?P<receiver>[\w ,.]+)\. (?P<datetime>[0-9. :]{16})\. '
            r'Dostupno (?P<rest_amount>[\d.]+) (?P<rest_currency>[A-Z]{3})\.',
            re.ASCII),
        'negative_actions': {'Pokupka', 'Snytie nalichnyh', 'Platezh',
                             'Operatsia v drugih kreditnyh organizatsiyah',
                             'Vnutrenniy perevod sebe', 'Vneshniy perevod'},
        'datetime_format': '%d.%m.%Y %H:%M',
        'datetime_tz': pytz.timezone('Europe/Moscow')
    }
}
