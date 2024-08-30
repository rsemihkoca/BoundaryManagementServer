import os
import logging
from dotenv import load_dotenv
from uvicorn.logging import AccessFormatter, DefaultFormatter

load_dotenv()


BOUNDARY_API_VERSION = os.environ.get("BOUNDARY_API_VERSION")

# Camera settings
BOUNDARY_DB_FILE = "./boundary.json"
MATCH_DB_FILE = "./boundary.json"

# Logging settings
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'access': {
            '()': AccessFormatter,
            'fmt': '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
        'default': {
            '()': DefaultFormatter,
            'fmt': '%(levelprefix)s %(message)s',
            'use_colors': None,
        },
    },
    'handlers': {
        'access': {
            'class': 'logging.StreamHandler',
            'formatter': 'access',
            'stream': 'ext://sys.stdout',
        },
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stderr',
        },
    },
    'loggers': {
        'uvicorn': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False,
        },
        'uvicorn.access': {
            'handlers': ['access'],
            'level': 'INFO',
            'propagate': False,
        },
        'uvicorn.error': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False,
        },
        'app': {
        'handlers': ['default'],
        'level': 'INFO',
        'propagate': False,
        },
    },
}


def setup_logging():
    logging.config.dictConfig(logging_config)