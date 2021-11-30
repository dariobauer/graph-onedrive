__version__ = "0.1.1"

import logging

from graph_onedrive._main import *

# Set default logging handler to avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())
