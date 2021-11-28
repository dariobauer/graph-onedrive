"""Decorators to wrap Graph-OneDrive package methods and functions.
"""
import logging
from datetime import datetime
from functools import wraps
from typing import no_type_check


@no_type_check
def token_required(func):
    """INTERNAL: Graph-OneDrive decorator to check for and refresh the access token when calling methods."""

    @wraps(func)
    def wrapper_token(*args, **kwargs):
        # Set self from args to get instance expires attribute
        onedrive_instance = args[0]
        expires = onedrive_instance._access_expires
        # Get the current timestamp for comparison
        now = datetime.timestamp(datetime.now())
        # Refresh access token if expires does not exist or has expired
        if expires <= now:
            logging.info(
                "access token expired, redeeming refresh token for new access token"
            )
            onedrive_instance._get_token()
            onedrive_instance._create_headers()
        # Function that is wrapped runs here
        wrapped_func = func(*args, **kwargs)
        # After run do nothing
        # Return the wrapped function
        return wrapped_func

    return wrapper_token
