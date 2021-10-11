"""Command line interface tools for the Python package Graph OneDrive.
"""
import json
import os
import sys
from pathlib import Path

import graph_onedrive._main as graph_onedrive


def main(argv=sys.argv):
    """Command line interface tools for the Python package Graph OneDrive.
    Options:
        instance -- create an instance in the command line to interact with OneDrive.
        config -- generate a config file.
        auth -- authenticate an existing config file.
    """

    try:
        operation = argv[1]
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


def config():
    """Create a configuration file."""
    # Set basic app credentials
    tenant_id = input("tenant: ").rstrip()
    client_id = input("client id: ").rstrip()
    client_secret_value = input("client secret value: ").rstrip()

    # Set config dictionary key
    if input("Use redirect url default 'http://localhost:8080' [Y/n]: ") in ["n", "N"]:
        redirect_url = input("Redirect url to use: ").rstrip()
    else:
        redirect_url = "http://localhost:8080"

    # Set config dictionary key
    if input("Use config dictionary key default 'onedrive' [Y/n]: ") in ["n", "N"]:
        config_key = input("Config dictionary key to use: ").rstrip()
    else:
        config_key = "onedrive"

    # Set the export directory
    if input("Save config.json in current working directory [Y/n]: ") in ["n", "N"]:
        config_path = input("Path to save config (including extention): ").rstrip()
    else:
        config_path = "/".join([os.getcwd(), "config.json"])
    config_path = Path(config_path)

    # Create the config
    config = {config_key: {}}
    config[config_key]["tenant_id"] = tenant_id
    config[config_key]["client_id"] = client_id
    config[config_key]["client_secret_value"] = client_secret_value
    config[config_key]["redirect_url"] = redirect_url
    config[config_key]["refresh_token"] = None

    # Save the configuration to config file
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)
    print(f"Configuration saved to: {config_path}")


def authenticate():
    """Authenticate with Onedrive and then save the configuration to file."""
    # Get the config file path
    config_path = get_config_file_path()

    # Set config dictionary key
    if input("Use config dictionary key default 'onedrive' [Y/n]: ") in ["n", "N"]:
        config_key = input("Config dictionary key to use: ").rstrip()
    else:
        config_key = "onedrive"

    # Create the instance
    try:
        onedrive = graph_onedrive.create_from_config_file(
            config_path=config_path, config_key=config_key
        )
    except KeyError:
        print(
            f"The config file is not in an acceptable format or the dictionary key '{config_key}' is incorrect."
        )
        exit()

    # Save the config
    graph_onedrive.save_to_config_file(
        onedrive_instance=onedrive, config_path=config_path, config_key=config_key
    )
    print(f"Refresh token saved to configuration: {config_path}")


def menu():
    """Interact directly with OneDrive in the command line to perform simple tasks and test the configuration."""

    # Load configuration
    if input("Load a configuration file [y/N]: ").rstrip() in ["y", "Y"]:

        # Get the config file path
        config_path = get_config_file_path()

        # Set the config dict key
        if input("Use config dictionary key default 'onedrive' [Y/n]: ") in ["n", "N"]:
            config_key = input("Config dictionary key to use: ").rstrip()
        else:
            config_key = "onedrive"

        # Create session
        try:
            onedrive = graph_onedrive.create_from_config_file(
                config_path=config_path, config_key=config_key
            )
        except KeyError:
            print(
                f"The config file is not in an acceptable format or the dictionary key '{config_key}' is incorrect."
            )
            exit()

    else:
        print("Manual configuration entry:")
        client_id = input("client_id: ").rstrip()
        client_secret = input("client_secret: ").rstrip()
        tenant = input("tenant (leave blank to use 'common':").rstrip()
        if tenant == "":
            tenant = "common"
        refresh_token = input(
            "refresh_token (leave blank to reauthenticate): "
        ).rstrip()
        if refresh_token == "":
            refresh_token = None
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
                folder_id = input("Folder id to look into (enter nothing for root): ")
                if folder_id == "":
                    folder_id = None
                onedrive.list_directory(folder_id, verbose=True)

            elif command == "detail":
                item_id = input("Item id to detail: ").rstrip()
                onedrive.detail_item(item_id, verbose=True)

            elif command == "mkdir":
                parent_folder_id = input(
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
                    new_file_name = input("New file name (with extension): ").rstrip()
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
                file_path = input("Provide full file path: ").rstrip()
                file_path = Path(file_path)
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

            else:
                print("Command not recognised. Press ^c to exit.")

    except KeyboardInterrupt:
        graph_onedrive.save_to_config_file(onedrive, config_path)
        pass


def get_config_file_path(try_filename="config.json"):
    """Sets a config path by trying a filename in the current working directory, else requests from user.
    Keyword arguments:
        try_filename (str) -- file name to try (default = "config.json")
    """
    cwd_config_path = "/".join([os.getcwd(), try_filename])
    if os.path.isfile(cwd_config_path):
        print("config.json found in current working directory.")
        if input("Use this config file? [Y/n]: ") not in ["n", "N"]:
            config_path = cwd_config_path
        else:
            # Get the file path from the user
            while True:
                config_path = input(
                    "Path to config file (including extension: "
                ).rstrip()
                if os.path.isfile(config_path):
                    break
                print("Path could not be validated, please try again.")
    return config_path


if __name__ == "__main__":
    main()
