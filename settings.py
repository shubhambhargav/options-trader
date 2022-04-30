import os

# Constants
ENVIRONMENT_LOCAL = 'local'
ENVIRONMENT_PRODUCTION = 'prod'

# Valid types: memory, disk
# Default: disk
CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'disk'
ENVIRONMENT = os.environ.get('ENVIRONMENT') or ENVIRONMENT_LOCAL
