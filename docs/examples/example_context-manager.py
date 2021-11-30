from os import path

from graph_onedrive import OneDriveManager


def main() -> None:
    """Load my OneDrive from a config file and print the drive usage."""

    # Set config path
    config_file_name = "config.json"
    directory_of_this_file = path.dirname(path.abspath(__file__))
    config_path = path.join(directory_of_this_file, config_file_name)

    # Set config dictionary key
    config_key = "onedrive"

    # Use the context manager to manage a session instance
    with OneDriveManager(config_path, config_key) as my_drive:
        # Complete tasks using the instance. For this example we will just display the usage
        my_drive.get_usage(verbose=True)


if __name__ == "__main__":
    main()
