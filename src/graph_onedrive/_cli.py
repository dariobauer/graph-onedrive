"""Command line interface to create a config file and/or interact directly with Onedrive.
"""
import os
import sys
from pathlib import Path

import graph_onedrive._main as graph_onedrive


def main(argv=sys.argv):
    """Command line interface to interact with Microsoft Onedrive.
    Options:
        instance -- create an instance in the command line to interact with Onedrive.
        auth -- generate config file containing authentication
    """

    try:
        operation = argv[1]
    except:
        print("Command not recorgnised. Input argument 'instance' or 'auth'.")
        return 1

    if operation == "instance":
        menu()
        return 0
    elif operation == "auth" or operation == "authenticate":
        authenticate()
        return 0
    else:
        print("Command not recorgnised. Input argument 'instance' or 'auth'.")
        return 1


def authenticate():
    """Authenticate with Onedrive and then save the configuration to file.
    """
    # Set basic app credentials
    tenant = input("tenant: " ).rstrip()
    client_id = input("client id: ").rstrip()
    client_secret = input("client secret value: ").rstrip()

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
        config_path = input("Path to save config (including extention): " ).rstrip()
    else:
        config_path = "/".join([os.getcwd(), "config.json"])
    config_path = Path(config_path)

    # Create the instance
    onedrive = graph_onedrive.create(client_id = client_id, client_secret = client_secret, tenant = tenant, redirect_url = redirect_url)

    # Save the config
    graph_onedrive.save_to_config_file(onedrive_instance = onedrive, config_path = config_path, config_key = config_key)
    print(f"Configuration saved to: {config_path}")


def menu():
    """Interact with Onedrive in the command line.
    """

    # Welcome message.
    print("Welcome to the Onedrive command-line interface tool.")

    # Load configuration
    if input("Load a configuration file [y/N]: ").rstrip() in ["y", "Y"]:

        # Check for config.json file
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        CWD = os.getcwd()
        root_config_path = "/".join([ROOT_DIR, "config.json"])
        cwd_config_path = "/".join([CWD, "config.json"])
        if os.path.isfile(root_config_path):
            config_path = root_config_path
        elif os.path.isfile(cwd_config_path):
            config_path = cwd_config_path
        else:
            config_path = False

        while config_path == False:
            user_config_path = input("Path to config file: ").rstrip()
            if os.path.isfile(user_config_path):
                onfig_path = user_config_path
            else:
                print("Path could not be validated, please try again.")
        
        if input("Use config dictionary key default 'onedrive' [Y/n]: ") in ["n", "N"]:
            config_key = input("Config dictionary key to use: ").rstrip()
        else:
            config_key = "onedrive"

        # Create session
        try:
            onedrive = graph_onedrive.create_from_config_file(config_path = config_path, config_key = config_key)
        except KeyError:
            print(f"The config file is not in an acceptable format or the dictionary key '{config_key}' is incorrect.")
            exit()
    
    else:
        print("Manual configuration entry:")
        client_id = input("client_id: ").rstrip()
        client_secret = input("client_secret: ").rstrip()
        tenant = input("tenant (leave blank to use 'common':" ).rstrip()
        if tenant == "":
            tenant = "common"
        refresh_token = input("refresh_token (leave blank to reauthenticate): ").rstrip()
        if refresh_token == "":
            refresh_token = None
        onedrive = graph_onedrive.create(client_id, client_secret, tenant, refresh_token)

    # Present menu to user and trigger commands
    try:
        while True:
            command = input("Please select command [usage/li/detail/mkdir/mv/cp/rename/rm/dl/ul]: ")

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
                parent_folder_id = input("Parent folder id (enter nothing for root): ").rstrip()
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
                print(f"Item was copied to folder {new_folder_id} with new item id {response}")

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
                print(f"Item was downloaded in the current working directory as {response}")

            elif command == "ul":
                file_path = input("Provide full file path: ").rstrip()
                file_path = Path(file_path)
                if input("Rename file? [y/N]: ") == "y":
                    new_file_name = input("Upload as file name (with extension): ").rstrip()
                else:
                    new_file_name = None
                parent_folder_id = input("Folder id to upload within (enter nothing for root): ").rstrip()
                if parent_folder_id == "":
                    parent_folder_id = None
                response = onedrive.upload_file(file_path, new_file_name, parent_folder_id)
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


if __name__ == "__main__":
    main()