import os
import logging
import subprocess
import yaml

with open('config.yaml', 'r') as config:
    cfg = yaml.load(config)

from disco.util.logging import LOG_FORMAT
from raven import Client
from raven.transport.gevent import GeventedHTTPTransport

ENV = os.getenv('ENV', 'prod')
DSN = cfg['DSN']
REV = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()

VERSION = '2.0.0'

raven_client = Client(
    DSN,
    ignore_exceptions=[
        'KeyboardInterrupt',
    ],
    release=REV,
    environment=ENV,
    transport=GeventedHTTPTransport,
)

# Log things to file
file_handler = logging.FileHandler('rowboat.log')
log = logging.getLogger()
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
log.addHandler(file_handler)

