import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'frekenbok.settings'
django.setup()

from django.contrib.auth.models import User
from django.core import management

# This tiny script prepares dev environment for start it
# 1. removes old DB
try:
    os.unlink('db.sqlite3')
    print('Dev database removed')
except FileNotFoundError:
    print('Dev database not found')
except Exception as e:
    print('Can\'t delete dev database: {}'.format(e))
    exit(1)
# 2. makes migrations
management.call_command('migrate')
# 3. compiles PO files
management.call_command('compilemessages')
# 4. creates superuser
User.objects.create_superuser(username='valera', password='vena89portae', email='valera@creator.su')
# ...
# PROFIT!!!1
