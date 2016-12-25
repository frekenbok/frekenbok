from frekenbok.settings import *

ALLOWED_HOSTS = []

SECRET_KEY = '_23n6hl)*4z)s+bn*7o7wk(ce@v2e7@#l=iv%4%5=4ua!5@%+='

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'frekenbok',
        'USER': 'frekenbok',
        'PASSWORD': 'frekenbok'
    }
}
