"""Command line interface tools for the Python package Graph-OneDrive.
Run terminal command 'graph-onedrive --help' or 'python -m graph-onedrive --help' for details.
"""
import argparse
import json
import os
from typing import Optional
from typing import Sequence
from typing import Tuple

import graph_onedrive._main as graph_onedrive
from graph_onedrive.__init__ import __version__


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Command line interface tools for the Python package Graph OneDrive.
    Use command --help for details.
    """
    # Create the argument parser
    cli_description = "Graph-OneDrive helper functions to create and authenticate configs and interact with OneDrive to test your configuration."
    cli_epilog = "Note: use of the Graph API is subject to the Microsoft terms of use avaliable at https://docs.microsoft.com/en-us/legal/microsoft-apis/terms-of-use"
    parser = argparse.ArgumentParser(description=cli_description, epilog=cli_epilog)
    # Add arguments
    parser_actions = parser.add_argument_group("actions")
    parser_actions.add_argument(
        "-c", "--configure", action="store_true", help="create a new configuration file"
    )
    parser_actions.add_argument(
        "-a",
        "--authenticate",
        action="store_true",
        help="authenticate a configuration file",
    )
    parser_actions.add_argument(
        "-i",
        "--instance",
        action="store_true",
        help="interact with OneDrive to test your config and perform simple tasks",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=__version__,
        help="Graph-OneDrive version number",
    )
    parser.add_argument(
        "-f",
        "--file",
        action="store",
        type=str,
        metavar="PATH",
        help="optional path to config json file",
    )
    parser.add_argument(
        "-k",
        "--key",
        action="store",
        type=str,
        help="optional config file dictionary key",
    )
    # Parse arguments, using function input args when given for tests
    args = parser.parse_args(argv)

    # Validate arguments
    if not (args.configure or args.authenticate or args.instance):
        parser.error("No action provided, use --help for details")

    if args.file and not args.file.endswith(".json"):
        parser.error("--file path must end in a json file")

    if args.key and args.key == "":
        parser.error("--key provided can not be blank")

    # Call action functions
    if args.configure:
        config(args.file, args.key)
    if args.authenticate:
        authenticate(args.file, args.key)
    if args.instance:
        instance(args.file, args.key)

    # Returning 0 to the terminal to indicate success
    return 0


def config(config_path: Optional[str] = None, config_key: Optional[str] = None) -> None:
    """Create a configuration file."""

    # Set the export directory
    if not config_path:
        if (
            input("Save config.json in current working directory [Y/n]: ")
            .strip()
            .lower()
            == "n"
        ):
            config_path = input("Path to save config (including file name): ").strip()
            if not config_path.endswith(".json"):
                config_path = config_path + ".json"
        else:
            config_path = os.path.join(os.getcwd(), "config.json")

    # Set config dictionary key
    if not config_key:
        if (
            input("Use config dictionary key default 'onedrive' [Y/n]: ")
            .strip()
            .lower()
            == "n"
        ):
            config_key = input("Config dictionary key to use: ").strip()
        else:
            config_key = "onedrive"

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
    tenant_id = input("tenant: ").strip()
    client_id = input("client id: ").strip()
    client_secret_value = input("client secret value: ").strip()

    # Set redirect url
    if (
        input("Use redirect url default 'http://localhost:8080' [Y/n]: ")
        .strip()
        .lower()
        == "n"
    ):
        redirect_url = input("Redirect url to use: ").strip()
    else:
        redirect_url = "http://localhost:8080"

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


def authenticate(
    config_path: Optional[str] = None, config_key: Optional[str] = None
) -> None:
    """Authenticate with OneDrive and then save the configuration to file."""
    # Get the config file path
    config_path, config_key = get_config_file(config_path, config_key)

    # Create the instance
    onedrive = graph_onedrive.create_from_config_file(
        config_path=config_path, config_key=config_key
    )

    # Save the config
    graph_onedrive.save_to_config_file(
        onedrive_instance=onedrive, config_path=config_path, config_key=config_key
    )
    print(f"Refresh token saved to configuration: {config_path}")


def get_config_file(
    config_path: Optional[str] = None, config_key: Optional[str] = None
) -> Tuple[str, str]:
    """Sets a config path and key by searching the cwd with assistance from from user."""

    if not config_path:
        # Look for json files in the current working directory and confirm with user
        cwd_path = os.getcwd()
        count = 0
        for root, dirs, files in os.walk(cwd_path):
            for file_name in files:
                if file_name.endswith(".json"):
                    if (
                        input(f"Found: {file_name} Use this? [Y/n]: ").strip().lower()
                        != "n"
                    ):
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
                config_path = input("Path to config file: ").strip()
                if not config_path.endswith(".json"):
                    config_path = config_path + ".json"
                if os.path.isfile(config_path):
                    break
                print("Path could not be validated, please try again.")

    # Open the config file
    with open(config_path) as config_file:
        config = json.load(config_file)

    # Check the config key
    if not config_key:
        config_key = "onedrive"
        if config_key in config:
            if (
                input("Config dictionary key 'onedrive' found. Use this key? [Y/n]: ")
                .strip()
                .lower()
                == "n"
            ):
                config_key = input("Config dictionary key to use: ").strip()
    while config_key not in config:
        print(f"Config dictionary key '{config_key}' not found.")
        config_key = input("Config dictionary key to use: ").strip()

    return config_path, config_key


def instance(
    config_path: Optional[str] = None, config_key: Optional[str] = None
) -> None:
    """Interact directly with OneDrive in the command line to perform simple tasks and test the configuration."""

    # Check with user if using config file
    if config_path or config_key:
        use_config_file = True
    elif input("Load an existing config file [Y/n]: ").strip().lower() != "n":
        use_config_file = True
    else:
        use_config_file = False

    # Create the instance
    if use_config_file:
        # Get the config details
        config_path_verified, config_key_verified = get_config_file(
            config_path, config_key
        )

        # Create session
        onedrive = graph_onedrive.create_from_config_file(
            config_path=config_path_verified, config_key=config_key_verified
        )
    else:
        print("Manual configuration entry:")
        client_id = input("client_id: ").strip()
        client_secret = input("client_secret: ").strip()
        tenant = input("tenant (leave blank to use 'common': ").strip()
        if tenant == "":
            tenant = "common"
        refresh_token = input("refresh_token (leave blank to reauthenticate): ").strip()
        onedrive = graph_onedrive.create(
            client_id, client_secret, tenant, refresh_token
        )

    # Present menu to user and trigger commands
    try:
        help_info = """
    Graph-OneDrive cli instance actions:
    u / usage      :  prints the OneDrive usage
    od / onedrive  :  print the OneDrive details
    li / list      :  list the contents of a folder
    de / detail    :  print metadata of an item
    md / mkdir     :  make a new folder
    mv / move      :  move an item
    cp / copy      :  copy an item
    rn / rename    :  rename an item
    rm / remove    :  remove an item
    dl / download  :  download a file
    ul / upload    :  upload a file
    exit / quit    :  exit the menu\n"""
        print(help_info)
        while True:
            command = input("Please enter command: ").strip().lower()

            if command == "help":
                print(help_info)

            elif command in ["u", "usage"]:
                onedrive.get_usage(verbose=True)

            elif command in ["li", "list"]:
                folder_id: Optional[str] = input(
                    "Folder id to look into (enter nothing for root): "
                ).strip()
                if folder_id == "":
                    folder_id = None
                onedrive.list_directory(folder_id, verbose=True)

            elif command in ["d", "detail"]:
                item_id = input("Item id to detail: ").strip()
                onedrive.detail_item(item_id, verbose=True)

            elif command in ["md", "mkdir"]:
                parent_folder_id: Optional[str] = input(
                    "Parent folder id (enter nothing for root): "
                ).strip()
                if parent_folder_id == "":
                    parent_folder_id = None
                folder_name = input("Name of the new folder: ").strip()
                response = onedrive.make_folder(folder_name, parent_folder_id)
                print(response)

            elif command in ["mv", "move"]:
                item_id = input("Item id of the file/folder to move: ").strip()
                new_folder_id = input("New parent folder id: ").strip()
                if input("Specify a new file name? [y/N]: ").strip().lower() == "y":
                    new_file_name: Optional[str] = input(
                        "New file name (with extension): "
                    ).strip()
                else:
                    new_file_name = None
                response = onedrive.move_item(item_id, new_folder_id, new_file_name)
                print(f"Item {item_id} was moved to {new_folder_id}")

            elif command in ["cp", "copy"]:
                item_id = input("Item id of the file/folder to copy: ").strip()
                new_folder_id = input("New parent folder id: ").strip()
                if input("Specify a new name? [y/N]: ").strip().lower() == "y":
                    new_file_name = input("New file name (with extension): ").strip()
                else:
                    new_file_name = None
                response = onedrive.copy_item(item_id, new_folder_id, new_file_name)
                print(
                    f"Item was copied to folder {new_folder_id} with new item id {response}"
                )

            elif command in ["rn", "rename"]:
                item_id = input("Item id of the file/folder to rename: ").strip()
                new_file_name = input("New file name (with extension): ").strip()
                response = onedrive.rename_item(item_id, new_file_name)
                print("Item was renamed.")

            elif command in ["rm", "remove", "delete"]:
                item_id = input("Item id of the file/folder to remove: ").strip()
                response = onedrive.delete_item(item_id)
                if response == True:
                    print(f"Item {item_id} was successfully removed.")

            elif command in ["dl", "download"]:
                item_id = input("Item id to download: ").strip()
                print("Downloading...")
                response = onedrive.download_file(item_id)
                print(
                    f"Item was downloaded in the current working directory as {response}"
                )

            elif command in ["ul", "upload"]:
                file_path_input = input("Provide full file path: ").strip()
                file_path = file_path_input
                if input("Rename file? [y/N]: ").strip().lower() == "y":
                    new_file_name = input(
                        "Upload as file name (with extension): "
                    ).strip()
                else:
                    new_file_name = None
                parent_folder_id = input(
                    "Folder id to upload within (enter nothing for root): "
                ).strip()
                if parent_folder_id == "":
                    parent_folder_id = None
                response = onedrive.upload_file(
                    file_path, new_file_name, parent_folder_id
                )
                print(response)

            elif command in ["od", "onedrive", "drive"]:
                print("Drive id:    ", onedrive._drive_id)
                print("Drive name:  ", onedrive._drive_name)
                print("Drive type:  ", onedrive._drive_type)
                print("Owner id:    ", onedrive._owner_id)
                print("Owner email: ", onedrive._owner_email)
                print("Owner name:  ", onedrive._owner_name)
                print(
                    "Quota used:  ",
                    round(onedrive._quota_used / (1024 * 1024), 2),
                    "mb",
                )
                print(
                    "Quota remain:",
                    round(onedrive._quota_remaining / (1024 * 1024), 2),
                    "mb",
                )
                print(
                    "Quota total: ",
                    round(onedrive._quota_total / (1024 * 1024), 2),
                    "mb",
                )

            elif command == "_access":
                print(onedrive._access_token)

            elif command == "_refresh":
                print(onedrive.refresh_token)

            elif command in ["exit", "exit()", "quit", "q", "end"]:
                if use_config_file:
                    graph_onedrive.save_to_config_file(
                        onedrive,
                        config_path=config_path_verified,
                        config_key=config_key_verified,
                    )
                break

            else:
                print("Command not recognised. Use 'help' for info or 'exit' to quit.")

    except KeyboardInterrupt:
        if use_config_file:
            graph_onedrive.save_to_config_file(
                onedrive,
                config_path=config_path_verified,
                config_key=config_key_verified,
            )


if __name__ == "__main__":
    raise SystemExit(main())
