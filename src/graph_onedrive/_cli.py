"""Command line interface tools for the Python package Graph-OneDrive.
"""
import json
import os
import sys
from pathlib import Path
from typing import List
from typing import Optional
from typing import Tuple

import graph_onedrive._main as graph_onedrive


def main(argv: List[str] = sys.argv) -> int:
    """Command line interface tools for the Python package Graph OneDrive.
    Options:
        instance -- create an instance in the command line to interact with OneDrive.
        config -- generate a config file.
        auth -- authenticate an existing config file.
    """

    try:
        operation: Optional[str] = argv[1]
    except:
        operation = None

    if operation == "instance":
        menu()
        return 0
    elif operation == "config":
        config()
        if input(
            "Would you like to authenticate and create a refresh token? [Y/n]: "
        ) not in ["n", "N"]:
            authenticate()
        return 0
    elif operation == "auth":
        authenticate()
        return 0
    else:
        print(
            "Command not recorgnised. Input argument 'instance', 'config', or 'auth'."
        )
        return 1


def config() -> None:
    """Create a configuration file."""

    # Set the export directory
    if input("Save config.json in current working directory [Y/n]: ") not in ["n", "N"]:
        config_path_str = os.path.join(os.getcwd(), "config.json")
    else:
        config_path_str = input("Path to save config (including file name): ").rstrip()
        if not config_path_str.endswith(".json"):
            config_path_str = config_path_str + ".json"
    config_path = Path(config_path_str)

    # Set config dictionary key
    if input("Use config dictionary key default 'onedrive' [Y/n]: ") not in ["n", "N"]:
        config_key = "onedrive"
    else:
        config_key = input("Config dictionary key to use: ").rstrip()

    # Load the current file if it exists, otherwsie create dictionary
    if os.path.isfile(config_path):
        with open(config_path) as config_file:
            config = json.load(config_file)
        # For safety do not overwrite existing configs
        if config_key in config:
            raise SystemExit(
                f"Error: '{config_key}' already exists in file, overwrite not permitted."
            )
        config[config_key] = {}
    else:
        config = {config_key: {}}

    # Set basic app credentials
    tenant_id = input("tenant: ").rstrip()
    client_id = input("client id: ").rstrip()
    client_secret_value = input("client secret value: ").rstrip()

    # Set redirect url
    if input("Use redirect url default 'http://localhost:8080' [Y/n]: ") not in [
        "n",
        "N",
    ]:
        redirect_url = "http://localhost:8080"
    else:
        redirect_url = input("Redirect url to use: ").rstrip()

    # Format the config into the dictionary
    config[config_key]["tenant_id"] = tenant_id
    config[config_key]["client_id"] = client_id
    config[config_key]["client_secret_value"] = client_secret_value
    config[config_key]["redirect_url"] = redirect_url
    config[config_key]["refresh_token"] = None

    # Save the configuration to config file
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)
    print(f"Configuration saved to: {config_path}")


def authenticate() -> None:
    """Authenticate with OneDrive and then save the configuration to file."""
    # Get the config file path
    config_path, config_key = get_config_file()

    # Create the instance
    try:
        onedrive = graph_onedrive.create_from_config_file(
            config_path=config_path, config_key=config_key
        )
    except KeyError:
        raise SystemExit(
            f"Error: Config not in acceptable format or dict key '{config_key}' incorrect."
        )

    # Save the config
    graph_onedrive.save_to_config_file(
        onedrive_instance=onedrive, config_path=config_path, config_key=config_key
    )
    print(f"Refresh token saved to configuration: {config_path}")


def get_config_file() -> Tuple[str, str]:
    """Sets a config path and key by searching the cwd with assistance from from user."""

    # Look for json files in the current working directory and confirm with user
    config_path = None
    count = 0
    cwd_path = os.getcwd()

    for root, dirs, files in os.walk(cwd_path):
        for file_name in files:
            if file_name.endswith(".json"):
                print(f"Found: {file_name}")
                if input("Is this a config file to use? [Y/n]: ").rstrip() not in [
                    "n",
                    "N",
                ]:
                    config_path = os.path.join(root, file_name)
                    break
                # Limit number of suggested files to top 5
                count += 1
                if count >= 5:
                    break
        else:
            continue
        break

    # Get the file path from the user
    if not config_path:
        while True:
            config_path = input("Path to config file: ").rstrip()
            if not config_path.endswith(".json"):
                config_path = config_path + ".json"
            if os.path.isfile(config_path):
                break
            print("Path could not be validated, please try again.")

    # Open the config file
    with open(config_path) as config_file:
        config = json.load(config_file)

    # Check the config key
    config_key = "onedrive"
    if config_key in config:
        if input(
            "Config dictionary key 'onedrive' found. Use this key? [Y/n]: "
        ).rstrip() in ["n", "N"]:
            config_key = input("Config dictionary key to use: ").rstrip()
    while config_key not in config:
        print(f"Config dictionary key '{config_key}' not found.")
        config_key = input("Config dictionary key to use: ").rstrip()

    return config_path, config_key


def menu() -> int:
    """Interact directly with OneDrive in the command line to perform simple tasks and test the configuration."""

    # Load configuration
    if input("Load an existing config file [Y/n]: ").rstrip() not in ["n", "N"]:

        # Get the config details
        config_path, config_key = get_config_file()

        # Create session
        try:
            onedrive = graph_onedrive.create_from_config_file(
                config_path=config_path, config_key=config_key
            )
        except KeyError:
            raise SystemExit(
                f"Error: Config not in acceptable format or dict key '{config_key}' incorrect."
            )

    else:
        print("Manual configuration entry:")
        client_id = input("client_id: ").rstrip()
        client_secret = input("client_secret: ").rstrip()
        tenant = input("tenant (leave blank to use 'common': ").rstrip()
        if tenant == "":
            tenant = "common"
        refresh_token = input(
            "refresh_token (leave blank to reauthenticate): "
        ).rstrip()
        onedrive = graph_onedrive.create(
            client_id, client_secret, tenant, refresh_token
        )

    # Present menu to user and trigger commands
    try:
        while True:
            command = input(
                "Please select command [usage/li/detail/mkdir/mv/cp/rename/rm/dl/ul]: "
            )

            if command == "usage":
                onedrive.get_usage(verbose=True)

            elif command == "li":
                folder_id: Optional[str] = input(
                    "Folder id to look into (enter nothing for root): "
                )
                if folder_id == "":
                    folder_id = None
                onedrive.list_directory(folder_id, verbose=True)

            elif command == "detail":
                item_id = input("Item id to detail: ").rstrip()
                onedrive.detail_item(item_id, verbose=True)

            elif command == "mkdir":
                parent_folder_id: Optional[str] = input(
                    "Parent folder id (enter nothing for root): "
                ).rstrip()
                if parent_folder_id == "":
                    parent_folder_id = None
                folder_name = input("Name of the new folder: ").rstrip()
                response = onedrive.make_folder(folder_name, parent_folder_id)
                print(response)

            elif command == "mv":
                item_id = input("Item id of the file/folder to move: ").rstrip()
                new_folder_id = input("New parent folder id: ").rstrip()
                if input("Specify a new file name? [y/N]: ") == "y":
                    new_file_name: Optional[str] = input(
                        "New file name (with extension): "
                    ).rstrip()
                else:
                    new_file_name = None
                response = onedrive.move_item(item_id, new_folder_id, new_file_name)
                print(f"Item {item_id} was moved to {new_folder_id}")

            elif command == "cp":
                item_id = input("Item id of the file/folder to copy: ").rstrip()
                new_folder_id = input("New parent folder id: ").rstrip()
                if input("Specify a new name? [y/N]: ") == "y":
                    new_file_name = input("New file name (with extension): ").rstrip()
                else:
                    new_file_name = None
                response = onedrive.copy_item(item_id, new_folder_id, new_file_name)
                print(
                    f"Item was copied to folder {new_folder_id} with new item id {response}"
                )

            elif command == "rename":
                item_id = input("Item id of the file/folder to rename: ").rstrip()
                new_file_name = input("New file name (with extension): ").rstrip()
                response = onedrive.rename_item(item_id, new_file_name)
                print("Item was renamed.")

            elif command == "rm":
                item_id = input("Item id of the file/folder to remove: ").rstrip()
                response = onedrive.delete_item(item_id)
                if response == True:
                    print(f"Item {item_id} was successfully removed.")

            elif command == "dl":
                item_id = input("Item id to download: ").rstrip()
                print("Downloading...")
                response = onedrive.download_file(item_id)
                print(
                    f"Item was downloaded in the current working directory as {response}"
                )

            elif command == "ul":
                file_path_input = input("Provide full file path: ").rstrip()
                file_path = Path(file_path_input)
                if input("Rename file? [y/N]: ") == "y":
                    new_file_name = input(
                        "Upload as file name (with extension): "
                    ).rstrip()
                else:
                    new_file_name = None
                parent_folder_id = input(
                    "Folder id to upload within (enter nothing for root): "
                ).rstrip()
                if parent_folder_id == "":
                    parent_folder_id = None
                response = onedrive.upload_file(
                    file_path, new_file_name, parent_folder_id
                )
                print(response)

            elif command == "_access":
                token = onedrive._access_token
                print(token)

            elif command == "_refresh":
                token = onedrive.refresh_token
                print(token)
            elif command == "exit" or command == "exit()":
                graph_onedrive.save_to_config_file(onedrive, config_path)
                return 0
            else:
                print("Command not recognised. Input 'exit' or press ^c to exit.")

    except KeyboardInterrupt:
        graph_onedrive.save_to_config_file(onedrive, config_path)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
