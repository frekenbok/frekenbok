from frekenbok.settings import *
from frekenbok.settings.dev import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'USER': 'frekenbok',
        'PASSWORD': 'frekenbok',
        'NAME': 'frekenbok',
    }
}
