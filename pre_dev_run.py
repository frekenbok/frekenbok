#!/usr/bin/env python3

import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'frekenbok.settings.dev'
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.core import management

from accountant.tests.test_data import add_test_data


class DevData:
    def __new__(cls):
        add_test_data(cls)


# This tiny script prepares dev environment for start. It...
# 1. ...removes old DB...
try:
    os.unlink(settings.DATABASES['default']['NAME'])
    print('Dev database ({}) removed'.format(settings.DATABASES['default']['NAME']))
except FileNotFoundError:
    print('Dev database not found')
except Exception as e:
    print('Can\'t delete dev database: {}'.format(e))
    exit(1)
# 2. ...migrates...
management.call_command('migrate')
# 3. ...compiles PO files...
management.call_command('compilemessages')
# 4. ...creates superuser
User.objects.create_superuser(
    username='valera',
    password='vena89portae',
    email='valera@creator.su')
# 5. Import test data
DevData()
# ...
# PROFIT!!!1
