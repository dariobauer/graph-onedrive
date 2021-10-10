from os import path

import graph_onedrive


def main():
    """ Interact with Microsoft Onedrive. Setup using config.json file in the same directory.
    """

    # Set config path
    ROOT_DIR = path.dirname(path.abspath(__file__))
    config_path = "/".join([ROOT_DIR, "config.json"])
    
    # Create session instance
    onedrive = graph_onedrive.create_from_config_file(config_path)

    # Complete tasks using the instance. For this example we will just display the usage
    onedrive.get_usage(verbose=True)

    # OPTIONAL: save back to the config file to retain the refresh token which can be used to bypass authentication.
    graph_onedrive.save_to_config_file(onedrive, config_path)


if __name__ == "__main__":
    main()