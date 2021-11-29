"""OneDrive instance constructor classes.
"""
from __future__ import annotations

import warnings
from pathlib import Path

from graph_onedrive._manager import OneDriveManager
from graph_onedrive._onedrive import OneDrive

# The following functions are depreciated and will be removed completely in a future release.


def create(
    client_id: str,
    client_secret: str,
    tenant: str = "common",
    redirect_url: str = "http://localhost:8080",
    refresh_token: str | None = None,
) -> OneDrive:
    """DEPRECIATED: use OneDrive() instead.
    Create an instance of the OneDrive class from arguments.
    Positional arguments:
        client_id (str) -- Azure app client id
        client_secret (str) -- Azure app client secret
    Keyword arguments:
        tenant (str) -- Azure app org tentent id number, use default if multi-tenant (default = "common")
        redirect_url (str)  -- Authentication redirection url (default = "http://localhost:8080")
        refresh_token (str) -- optional token from previous session (default = None)
    Returns:
        onedrive_instance (OneDrive) -- OneDrive object instance
    """
    # Warn to use class directly
    warnings.warn(
        "create() depreciated, use OneDrive()",
        category=DeprecationWarning,
        stacklevel=2,
    )
    # Return the OneDrive object instance
    return OneDrive(
        client_id=client_id,
        client_secret=client_secret,
        tenant=tenant,
        redirect_url=redirect_url,
        refresh_token=refresh_token,
    )


def create_from_config_file(
    config_path: str | Path, config_key: str = "onedrive"
) -> OneDrive:
    """DEPRECIATED: use OneDrive.from_json() instead.
    Create an instance of the OneDrive class from a config file.
    Positional arguments:
        config_path (str|Path) -- path to configuration json file
    Keyword arguments:
        config_key (str) -- key of the json item storing the configuration (default = "onedrive")
    Returns:
        onedrive_instance (OneDrive) -- OneDrive object instance
    """
    # Warn to use class directly
    warnings.warn(
        "create_from_config_file() depreciated, use OneDrive.from_json()",
        category=DeprecationWarning,
        stacklevel=2,
    )
    # Return the OneDrive instance
    return OneDrive.from_json(config_path, config_key)


def save_to_config_file(
    onedrive_instance: OneDrive,
    config_path: str | Path,
    config_key: str = "onedrive",
) -> None:
    """DEPRECIATED: use OneDrive.to_json() instead.
    Save the configuration to a json config file.
    Positional arguments:
        onedrive_instance (OneDrive) -- instance with the config to save
        config_path (str|Path) -- path to configuration json file
    Keyword arguments:
        config_key (str) -- key of the json item storing the configuration (default = "onedrive")
    """
    # Check types
    if not isinstance(onedrive_instance, OneDrive):
        raise TypeError(
            f"onedrive_instance expected 'OneDrive', got {type(onedrive_instance).__name__!r}"
        )
    # Warn to use class directly
    warnings.warn(
        "save_to_config_file() depreciated, use OneDrive.to_json()",
        category=DeprecationWarning,
        stacklevel=2,
    )
    # Save to json
    onedrive_instance.to_json(config_path, config_key)
