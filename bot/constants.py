from os import environ

ghost_unicode = "\N{GHOST}"
HACKTOBERBOT_TOKEN = environ.get('HACKTOBERBOT_TOKEN')
HACKTOBERBOT_PREFIX = environ.get('HACKTOBERBOT_PREFIX', ['.', f'{ghost_unicode} ', ghost_unicode])
