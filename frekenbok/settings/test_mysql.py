from frekenbok.settings import *
from frekenbok.settings.dev import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'USER': 'frekenbok',
        'PASSWORD': 'frekenbok',
        'NAME': 'frekenbok',
        'OPTIONS': {'init_command': 'SET names "utf8"'}
    }
}
