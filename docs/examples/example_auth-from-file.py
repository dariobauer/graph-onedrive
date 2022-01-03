from os import path

from graph_onedrive import OneDrive


def main() -> None:
    """Load my OneDrive from a config file and print the drive usage."""

    # Set config path
    config_file_name = "config.json"
    directory_of_this_file = path.dirname(path.abspath(__file__))
    config_path = path.join(directory_of_this_file, config_file_name)

    # Set config dictionary key
    config_key = "onedrive"

    # Create session instance
    my_drive = OneDrive.from_file(config_path, config_key)

    # Complete tasks using the instance. For this example we will just display the usage
    my_drive.get_usage(verbose=True)

    # OPTIONAL: save back to the config file to retain the refresh token which can be used to bypass authentication.
    # If you are doing this then it is reccommended that you use the context manager instead.
    my_drive.to_file(config_path, config_key)


if __name__ == "__main__":
    main()
