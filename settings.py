import os

# Valid types: memory, disk
# Default: disk
CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'disk'
