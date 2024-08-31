import os
import logging
from dotenv import load_dotenv
from uvicorn.logging import AccessFormatter, DefaultFormatter
from typing import Dict, Any

load_dotenv()


BOUNDARY_API_VERSION = os.environ.get("BOUNDARY_API_VERSION")
MATCH_DB_FILE = "./match.json"
BOUNDARY_DB_FILE = "./boundary.json"

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



class DefaultBoundaryCoordinates:
    @staticmethod
    def get_default_coordinates(boundary_type: str, capacity: int) -> Dict[str, Dict[str, int]]:
        capacity_coordinates = {
            1: {
                "OUTER": {
                    "UL": {"x": 40, "y": 40}, "UR": {"x": 600, "y": 40},
                    "LR": {"x": 600, "y": 440}, "LL": {"x": 40, "y": 440}
                },
                "TABLE": {
                    "UL": {"x": 80, "y": 80}, "UR": {"x": 560, "y": 80},
                    "LR": {"x": 560, "y": 400}, "LL": {"x": 80, "y": 400}
                },
                "1": {
                    "UL": {"x": 120, "y": 120}, "UR": {"x": 520, "y": 120},
                    "LR": {"x": 520, "y": 360}, "LL": {"x": 120, "y": 360}
                },
            },
            2: {
                "OUTER": {
                    "UL": {"x": 30, "y": 30}, "UR": {"x": 610, "y": 30},
                    "LR": {"x": 610, "y": 450}, "LL": {"x": 30, "y": 450}
                },
                "TABLE": {
                    "UL": {"x": 70, "y": 70}, "UR": {"x": 570, "y": 70},
                    "LR": {"x": 570, "y": 410}, "LL": {"x": 70, "y": 410}
                },
                "1": {
                    "UL": {"x": 110, "y": 110}, "UR": {"x": 320, "y": 110},
                    "LR": {"x": 320, "y": 370}, "LL": {"x": 110, "y": 370}
                },
                "2": {
                    "UL": {"x": 320, "y": 110}, "UR": {"x": 530, "y": 110},
                    "LR": {"x": 530, "y": 370}, "LL": {"x": 320, "y": 370}
                },
            },
            3: {
                "OUTER": {
                    "UL": {"x": 20, "y": 20}, "UR": {"x": 620, "y": 20},
                    "LR": {"x": 620, "y": 460}, "LL": {"x": 20, "y": 460}
                },
                "TABLE": {
                    "UL": {"x": 60, "y": 60}, "UR": {"x": 580, "y": 60},
                    "LR": {"x": 580, "y": 420}, "LL": {"x": 60, "y": 420}
                },
                "1": {
                    "UL": {"x": 100, "y": 100}, "UR": {"x": 280, "y": 100},
                    "LR": {"x": 280, "y": 380}, "LL": {"x": 100, "y": 380}
                },
                "2": {
                    "UL": {"x": 280, "y": 100}, "UR": {"x": 460, "y": 100},
                    "LR": {"x": 460, "y": 380}, "LL": {"x": 280, "y": 380}
                },
                "3": {
                    "UL": {"x": 460, "y": 100}, "UR": {"x": 540, "y": 100},
                    "LR": {"x": 540, "y": 380}, "LL": {"x": 460, "y": 380}
                },
            },
            4: {
                "OUTER": {
                    "UL": {"x": 10, "y": 10}, "UR": {"x": 630, "y": 10},
                    "LR": {"x": 630, "y": 470}, "LL": {"x": 10, "y": 470}
                },
                "TABLE": {
                    "UL": {"x": 50, "y": 50}, "UR": {"x": 590, "y": 50},
                    "LR": {"x": 590, "y": 430}, "LL": {"x": 50, "y": 430}
                },
                "1": {
                    "UL": {"x": 90, "y": 90}, "UR": {"x": 250, "y": 90},
                    "LR": {"x": 250, "y": 230}, "LL": {"x": 90, "y": 230}
                },
                "2": {
                    "UL": {"x": 250, "y": 90}, "UR": {"x": 410, "y": 90},
                    "LR": {"x": 410, "y": 230}, "LL": {"x": 250, "y": 230}
                },
                "3": {
                    "UL": {"x": 90, "y": 230}, "UR": {"x": 250, "y": 230},
                    "LR": {"x": 250, "y": 390}, "LL": {"x": 90, "y": 390}
                },
                "4": {
                    "UL": {"x": 250, "y": 230}, "UR": {"x": 410, "y": 230},
                    "LR": {"x": 410, "y": 390}, "LL": {"x": 250, "y": 390}
                },
            },
            5: {
                "OUTER": {
                    "UL": {"x": 5, "y": 5}, "UR": {"x": 635, "y": 5},
                    "LR": {"x": 635, "y": 475}, "LL": {"x": 5, "y": 475}
                },
                "TABLE": {
                    "UL": {"x": 45, "y": 45}, "UR": {"x": 595, "y": 45},
                    "LR": {"x": 595, "y": 435}, "LL": {"x": 45, "y": 435}
                },
                "1": {
                    "UL": {"x": 85, "y": 85}, "UR": {"x": 225, "y": 85},
                    "LR": {"x": 225, "y": 205}, "LL": {"x": 85, "y": 205}
                },
                "2": {
                    "UL": {"x": 225, "y": 85}, "UR": {"x": 365, "y": 85},
                    "LR": {"x": 365, "y": 205}, "LL": {"x": 225, "y": 205}
                },
                "3": {
                    "UL": {"x": 365, "y": 85}, "UR": {"x": 505, "y": 85},
                    "LR": {"x": 505, "y": 205}, "LL": {"x": 365, "y": 205}
                },
                "4": {
                    "UL": {"x": 85, "y": 205}, "UR": {"x": 295, "y": 205},
                    "LR": {"x": 295, "y": 395}, "LL": {"x": 85, "y": 395}
                },
                "5": {
                    "UL": {"x": 295, "y": 205}, "UR": {"x": 505, "y": 205},
                    "LR": {"x": 505, "y": 395}, "LL": {"x": 295, "y": 395}
                },
            },
            6: {
                "OUTER": {
                    "UL": {"x": 0, "y": 0}, "UR": {"x": 640, "y": 0},
                    "LR": {"x": 640, "y": 480}, "LL": {"x": 0, "y": 480}
                },
                "TABLE": {
                    "UL": {"x": 40, "y": 40}, "UR": {"x": 600, "y": 40},
                    "LR": {"x": 600, "y": 440}, "LL": {"x": 40, "y": 440}
                },
                "1": {
                    "UL": {"x": 80, "y": 80}, "UR": {"x": 200, "y": 80},
                    "LR": {"x": 200, "y": 180}, "LL": {"x": 80, "y": 180}
                },
                "2": {
                    "UL": {"x": 200, "y": 80}, "UR": {"x": 320, "y": 80},
                    "LR": {"x": 320, "y": 180}, "LL": {"x": 200, "y": 180}
                },
                "3": {
                    "UL": {"x": 320, "y": 80}, "UR": {"x": 440, "y": 80},
                    "LR": {"x": 440, "y": 180}, "LL": {"x": 320, "y": 180}
                },
                "4": {
                    "UL": {"x": 80, "y": 180}, "UR": {"x": 200, "y": 180},
                    "LR": {"x": 200, "y": 400}, "LL": {"x": 80, "y": 400}
                },
                "5": {
                    "UL": {"x": 200, "y": 180}, "UR": {"x": 320, "y": 180},
                    "LR": {"x": 320, "y": 400}, "LL": {"x": 200, "y": 400}
                },
                "6": {
                    "UL": {"x": 320, "y": 180}, "UR": {"x": 440, "y": 180},
                    "LR": {"x": 440, "y": 400}, "LL": {"x": 320, "y": 400}
                },
            }
        }
        
        if capacity in capacity_coordinates and boundary_type in capacity_coordinates[capacity]:
            return capacity_coordinates[capacity][boundary_type]
        
        # Fallback to (0, 0) coordinates if no match is found
        return {
            "UL": {"x": 0, "y": 0}, "UR": {"x": 0, "y": 0},
            "LR": {"x": 0, "y": 0}, "LL": {"x": 0, "y": 0}
        }