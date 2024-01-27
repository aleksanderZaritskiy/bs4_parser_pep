from pathlib import Path


OUTPUT_PRETTY = 'pretty'
OUTPUT_FILE = 'file'
MAIN_DOC_URL = 'https://docs.python.org/3/'
PYTHON_PEPS_URL = 'https://peps.python.org/'
BASE_DIR = Path(__file__).parent
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
LOG_DIR_PATH = 'logs'
DOWNLOAD_DIR_PATH = 'downloads'
FILE_OUTPUT_DIR_PATH = 'results'
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
