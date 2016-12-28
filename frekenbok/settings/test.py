from frekenbok.settings import *

ALLOWED_HOSTS = []

SECRET_KEY = '_23n6hl)*4z)s+bn*7o7wk(ce@v2e7@#l=iv%4%5=4ua!5@%+='

DEBUG = True

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'media')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '..', 'tests.sqlite3'),
    }
}
