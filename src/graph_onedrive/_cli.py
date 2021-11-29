"""Command line interface tools for the Python package Graph-OneDrive.
Run terminal command 'graph-onedrive --help' or 'python -m graph-onedrive --help' for details.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime
from typing import Sequence

from graph_onedrive.__init__ import __version__
from graph_onedrive._main import OneDrive


CONFIG_EXT = ".json"
CONFIG_DEF_FILE = "config" + CONFIG_EXT
CONFIG_DEF_KEY = "onedrive"


def main(argv: Sequence[str] | None = None) -> int:
    """Command line interface tools for the Python package Graph OneDrive.
    Use command --help for details.
    """
    # Create the argument parser
    cli_description = "Graph-OneDrive helper functions to create and authenticate configs and interact with OneDrive to test your configuration."
    cli_epilog = "Note: use of the Graph API is subject to the Microsoft terms of use available at https://docs.microsoft.com/en-us/legal/microsoft-apis/terms-of-use"
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
    parser.add_argument(
        "-l",
        "--log",
        action="count",
        default=0,
        help="displays logs (level=INFO), use -ll for level=DEBUG",
    )
    # Parse arguments, using function input args when given for tests
    args = parser.parse_args(argv)

    # Validate arguments
    if not (args.configure or args.authenticate or args.instance):
        parser.error("No action provided, use --help for details")

    if args.file and not args.file.endswith(CONFIG_EXT):
        parser.error(f"--file path must have {CONFIG_EXT} extension")

    if args.key and args.key == "":
        parser.error("--key provided can not be blank")

    # Configure logger
    if args.log == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.log == 2:
        logging.basicConfig(level=logging.DEBUG)

    # Call action functions
    if args.configure:
        config(args.file, args.key)
    if args.authenticate:
        authenticate(args.file, args.key)
    if args.instance:
        instance(args.file, args.key)

    # Returning 0 to the terminal to indicate success
    return 0


def config(config_path: str | None = None, config_key: str | None = None) -> None:
    """Create a configuration file."""

    # Set the export directory
    if not config_path:
        if (
            input(f"Save {CONFIG_DEF_FILE} in current working directory [Y/n]: ")
            .strip()
            .lower()
            == "n"
        ):
            config_path = input("Path to save config (including file name): ").strip()
        else:
            config_path = os.path.join(os.getcwd(), CONFIG_DEF_FILE)

    if not config_path.endswith(CONFIG_EXT):
        config_path += CONFIG_EXT

    # Set config dictionary key
    if not config_key:
        if (
            input(f"Use config dictionary key default '{CONFIG_DEF_KEY}' [Y/n]: ")
            .strip()
            .lower()
            == "n"
        ):
            config_key = input("Config dictionary key to use: ").strip()
        else:
            config_key = CONFIG_DEF_KEY

    # Load the current file if it exists, otherwise create dictionary
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


def authenticate(config_path: str | None = None, config_key: str | None = None) -> None:
    """Authenticate with OneDrive and then save the configuration to file."""
    # Get the config file path
    config_path, config_key = get_config_file(config_path, config_key)

    # Create the instance
    onedrive = OneDrive.from_json(config_path, config_key)

    # Save the config
    onedrive.to_json(config_path, config_key)
    print(f"Refresh token saved to configuration: {config_path}")


def get_config_file(
    config_path: str | None = None, config_key: str | None = None
) -> tuple[str, str]:
    """Sets a config path and key by searching the cwd with assistance from from user."""

    if not config_path:
        # Look for json files in the current working directory and confirm with user
        cwd_path = os.getcwd()
        count = 0
        for root, dirs, files in os.walk(cwd_path):
            for file_name in files:
                if file_name.endswith(CONFIG_EXT):
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
                if not config_path.endswith(CONFIG_EXT):
                    config_path = config_path + CONFIG_EXT
                if os.path.isfile(config_path):
                    break
                print("Path could not be validated, please try again.")

    # Open the config file
    with open(config_path) as config_file:
        config = json.load(config_file)

    # Check the config key
    if not config_key:
        config_key = CONFIG_DEF_KEY
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


def instance(config_path: str | None = None, config_key: str | None = None) -> None:
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
        onedrive = OneDrive.from_json(config_path_verified, config_key_verified, True)
    else:
        print("Manual configuration entry:")
        client_id = input("client_id: ").strip()
        client_secret = input("client_secret: ").strip()
        tenant = input("tenant (leave blank to use 'common': ").strip()
        if tenant == "":
            tenant = "common"
        refresh_token = input("refresh_token (leave blank to reauthenticate): ").strip()
        onedrive = OneDrive(client_id, client_secret, tenant, refresh_token)

    # Command menu for the user
    help_info = """
    Graph-OneDrive cli instance actions:
    u / usage      :  prints the OneDrive usage
    od / onedrive  :  print the OneDrive details
    li / list      :  list the contents of a folder
    de / detail    :  print metadata of an item
    sl / link      :  create a sharing link for an item
    md / mkdir     :  make a new folder
    mv / move      :  move an item
    cp / copy      :  copy an item
    rn / rename    :  rename an item
    rm / remove    :  remove an item
    dl / download  :  download a file
    ul / upload    :  upload a file
    exit / quit    :  exit the menu\n"""
    print(help_info)

    # Ask for input and trigger commands
    try:
        while True:
            command = input("Please enter command: ").strip().lower()

            if command == "help":
                print(help_info)

            elif command in ["u", "usage"]:
                onedrive.get_usage(verbose=True)

            elif command in ["li", "list"]:
                folder_id: str | None = input(
                    "Folder id to look into (enter nothing for root): "
                ).strip()
                if folder_id == "":
                    folder_id = None
                elif not onedrive.is_folder(str(folder_id)):
                    print("The item id is not a folder.")
                    continue
                onedrive.list_directory(folder_id, verbose=True)

            elif command in ["de", "detail"]:
                item_id = input("Item id or root path starting with /: ").strip()
                if item_id[0] == "/":
                    onedrive.detail_item_path(item_id, verbose=True)
                else:
                    onedrive.detail_item(item_id, verbose=True)

            elif command in ["sl", "link"]:
                item_id = input("Item id to create a link for: ").strip()
                link_type = ""
                while link_type not in ("view", "edit", "embed"):
                    link_type = input("Type of link (view/edit/embed): ").strip()
                password = None
                if (
                    onedrive._drive_type == "personal"
                    and input("Set password [y/N]: ").strip().lower() == "y"
                ):
                    password = input("Password: ").strip()
                expiration = None
                if input("Set expiry [y/N]: ").strip().lower() == "y":
                    while True:
                        date = input("Set expiry date in format YYYY-MM-DD: ").strip()
                        try:
                            expiration = datetime.strptime(date, "%Y-%m-%d")
                        except ValueError:
                            print("Not in correct format, try again or use ^c to exit.")
                            continue
                        if (
                            input(
                                f"{expiration.strftime('%e %B %Y')} - is this correct? [Y/n]: "
                            )
                            .strip()
                            .lower()
                            != "n"
                        ):
                            break
                scope = "anonymous"
                if onedrive._drive_type == "business":
                    if (
                        input("Limit to your organization [Y/n]: ").strip().lower()
                        != "n"
                    ):
                        scope = "organization"
                response = onedrive.create_share_link(
                    item_id, link_type, password, expiration, scope
                )
                print(response)

            elif command in ["md", "mkdir"]:
                parent_folder_id: str | None = input(
                    "Parent folder id (enter nothing for root): "
                ).strip()
                if parent_folder_id == "":
                    parent_folder_id = None
                elif not onedrive.is_folder(str(parent_folder_id)):
                    print("The item id is not a folder.")
                    continue
                folder_name = input("Name of the new folder: ").strip()
                response = onedrive.make_folder(folder_name, parent_folder_id)
                print(response)

            elif command in ["mv", "move"]:
                item_id = input("Item id of the file/folder to move: ").strip()
                new_folder_id = input("New parent folder id: ").strip()
                if input("Specify a new file name? [y/N]: ").strip().lower() == "y":
                    new_file_name: str | None = input(
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
                response = onedrive.copy_item(
                    item_id,
                    new_folder_id,
                    new_file_name,
                    confirm_complete=True,
                    verbose=True,
                )
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
                item_id = input("File item id to download: ").strip()
                if onedrive.is_folder(item_id):
                    print("Item id is a folder. Folders cannot be downloaded.")
                    continue
                print("Downloading")
                response = onedrive.download_file(item_id, verbose=True)
                print(
                    f"Item was downloaded in the current working directory as {response}"
                )

            elif command in ["ul", "upload"]:
                file_path = input("Provide full file path: ").strip()
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
                elif not onedrive.is_folder(str(parent_folder_id)):
                    print("The item id is not a folder.")
                    continue
                item_id = onedrive.upload_file(
                    file_path, new_file_name, parent_folder_id, verbose=True
                )
                print(f"New file item id: {item_id}")

            elif command in ["od", CONFIG_DEF_KEY, "drive"]:
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
                break

            else:
                print("Command not recognized. Use 'help' for info or 'exit' to quit.")

    finally:
        if use_config_file:
            onedrive.to_json(
                config_path_verified,
                config_key_verified,
            )


if __name__ == "__main__":
    raise SystemExit(main())
