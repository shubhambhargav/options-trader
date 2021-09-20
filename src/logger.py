"""Logger"""
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(process)d %(message)s')

LOG_LEVEL = os.getenv('TRADER_LOG_LEVEL', 'INFO')

LOGGER = logging.getLogger('trader')
LOGGER.setLevel(logging.getLevelName(LOG_LEVEL))
