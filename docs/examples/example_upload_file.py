from os import path

import graph_onedrive


def main() -> None:
    """Create a OneDrive instance using a config file, and then upload
    a file to a folder in the top level of my OneDrive."""

    # Create session instance
    my_drive = graph_onedrive.create_from_config_file(
        config_path="config.json", config_key="onedrive"
    )

    # Set the location of the file to upload
    my_file = "my-photo.jpg"  # Can be a string or a pathlib Path object

    # Say we have a folder in our OneDrive root level (top level) called "My Photos"
    dest_folder_name = "My Photos"

    # Get the details of all the items in the root directory
    items = my_drive.list_directory()

    # Search through the root directory to find the file
    dest_folder_id = None
    for item in items:
        if "folder" in item and item.get("name") == dest_folder_name:
            dest_folder_id = item["id"]
            break

    # Raise an error if the folder is not found
    if dest_folder_id is None:
        raise Exception(
            f"Could not find a folder named {dest_folder_name} in the root of the OneDrive"
        )

    # Upload the file
    new_file_id = my_drive.upload_file(
        file_path=my_file, parent_folder_id=dest_folder_id, verbose=True
    )

    print(
        f"{my_file} uploaded to OneDrive folder {dest_folder_name}, and now has the id {new_file_id}."
    )

    # OPTIONAL: save back to the config file to retain the refresh token
    graph_onedrive.save_to_config_file(
        my_drive, config_path="config.json", config_key="onedrive"
    )


if __name__ == "__main__":
    main()
