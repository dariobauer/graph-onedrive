"""Graph-OneDrive main functions to create instances of the OneDrive class and save the calss configs.
Funtions: create, create_from_config_file, save_to_config_file.
"""
import json
from pathlib import Path
from typing import Optional
from typing import Union

from graph_onedrive._onedrive import OneDrive


def create(
    client_id: str,
    client_secret: str,
    tenant: str = "common",
    redirect_url: str = "http://localhost:8080",
    refresh_token: Optional[str] = None,
) -> OneDrive:
    """Create an instance of the OneDrive class from arguments.
    Positional arguments:
        client_id (str) -- Azure app client id
        client_secret (str) -- Azure app client secret
    Keyword arguments:
        tenant (str) -- Azure app org tentent id number, use default if multi-tenent (default = "common")
        redirect_url (str)  -- Authentication redirection url (default = "http://localhost:8080")
        refresh_token (str) -- optional token from previous session (default = None)
    Returns:
        onedrive_instance (OneDrive) -- OneDrive object instance
    """

    # Return the OneDrive object instance
    return OneDrive(
        client_id=client_id,
        client_secret=client_secret,
        tenant=tenant,
        redirect_url=redirect_url,
        refresh_token=refresh_token,
    )


def create_from_config_file(
    config_path: Union[str, Path], config_key: str = "onedrive"
) -> OneDrive:
    """Create an instance of the OneDrive class from a config file.
    Positional arguments:
        config_path (str|Path) -- path to configuration json file
    Keyword arguments:
        config_key (str) -- key of the json item storing the configuration (default = "onedrive")
    Returns:
        onedrive_instance (OneDrive) -- OneDrive object instance
    """

    # Read configuration from config file
    print("Reading OneDrive configs...")
    config_path = Path(config_path)
    with open(config_path) as config_file:
        config = json.load(config_file)
    if config_key not in config:
        raise Exception(f"Config Error : Config dict key '{config_key}' incorrect")
    try:
        tenant_id = config[config_key]["tenant_id"]
        client_id = config[config_key]["client_id"]
        client_secret = config[config_key]["client_secret_value"]
    except KeyError:
        raise Exception("Config Error : Config not in acceptable format")
    try:
        redirect_url = config[config_key]["redirect_url"]
    except KeyError:
        redirect_url = "http://localhost:8080"
    try:
        refresh_token = config[config_key]["refresh_token"]
    except KeyError:
        refresh_token = None

    # Create OneDrive object instance
    onedrive_instance = create(
        client_id=client_id,
        client_secret=client_secret,
        tenant=tenant_id,
        redirect_url=redirect_url,
        refresh_token=refresh_token,
    )

    # Get refresh token from instance and update config file
    print("Saving refresh token...")
    with open(config_path) as config_file:
        config = json.load(config_file)
    config[config_key]["refresh_token"] = onedrive_instance.refresh_token
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)

    # Return the OneDrive instance
    return onedrive_instance


def save_to_config_file(
    onedrive_instance: OneDrive,
    config_path: Union[str, Path],
    config_key: str = "onedrive",
) -> None:
    """Save the configuration to a json config file.
    Positional arguments:
        onedrive_instance (OneDrive) -- instance with the config to save
        config_path (str|Path) -- path to configuration json file
    Keyword arguments:
        config_key (str) -- key of the json item storing the configuration (default = "onedrive")
    """
    # Read the existing configuration from the file if one exists
    try:
        with open(config_path) as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        config = {}

    if config_key not in config:
        config[config_key] = {}

    # Set the new configuation
    config[config_key]["tenant_id"] = onedrive_instance._tenant_id
    config[config_key]["client_id"] = onedrive_instance._client_id
    config[config_key]["client_secret_value"] = onedrive_instance._client_secret
    config[config_key]["redirect_url"] = onedrive_instance._redirect
    config[config_key]["refresh_token"] = onedrive_instance.refresh_token

    # Save the configuration to config file
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)

    # Nothing returned which signals no errors
    return
