import tempfile

from frekenbok.settings import *
from frekenbok.settings.dev import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': tempfile.mkstemp(suffix='.sqlite3', prefix='frekenbok_')[1],
    }
}
