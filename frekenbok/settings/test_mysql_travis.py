from frekenbok.settings.test_mysql import *

DATABASES['default']['USER'] = 'root'
DATABASES['default']['PASSWORD'] = ''
DATABASES['default']['OPTIONS'] = {'init_command': 'SET names "utf8";'}
