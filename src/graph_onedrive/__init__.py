__version__ = "0.3.0dev2"

import logging

from graph_onedrive._main import *

# Set default logging handler to avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())
