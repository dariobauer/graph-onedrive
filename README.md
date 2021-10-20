# Graph-OneDrive

Interact with Microsoft's OneDrive service using the Graph API.

The Graph-OneDrive package facilitates the creation of OneDrive class instances which are objects that you can use to interact with OneDrive sessions. Thus multiple OneDrives can be connected to in parallel.

Functions include:

* listing directories;
* moving, copying, and renaming files and folders;
* uploading and downloading files;
* getting drive metadata including usage.

## Azure app requirement

For the package to connect to the Graph API, you need to have an app registered in the Microsoft Azure Portal. The [documentation](https://github.com/dariobauer/graph-onedrive/blob/main/docs/) provides basic guidance on how to register an app.

Note that some Microsoft work and school accounts will not allow apps to connect with them without admin consent.

## Installation

The package currently requires Python 3.7 or greater.

Install and update using [pip](https://pip.pypa.io/en/stable/getting-started/) which will use the releases hosted on [PyPI](https://pypi.org/project/graph-onedrive/#history). Further options in the docs.

```console
pip install graph-onedrive
```

## Documentation

Documentation and examples are provided on GitHub: <https://github.com/dariobauer/graph-onedrive/blob/main/docs/>

### A simple example

Run this command in the terminal after installation which will create a config file in the current folder.

```console
graph-onedrive config
```

Save the following in a .py file in the same folder.

```python
import graph_onedrive

# Set config file details
config_path = "config.json"
config_key = "onedrive"

# Create session instance
my_drive = graph_onedrive.create_from_config_file(config_path, config_key)

# Complete tasks using the instance. For example print the drive usage
my_drive.get_usage(verbose=True)

# Save the config to retain the refresh token
graph_onedrive.save_to_config_file(my_drive, config_path, config_key)
```

## License

This project itself is subject to BSD 3-Clause License detailed in [LICENSE](https://github.com/dariobauer/graph-onedrive/blob/main/LICENSE).

The Graph API is provided by Microsoft Corporation and subject to their [terms of use](https://docs.microsoft.com/en-us/legal/microsoft-apis/terms-of-use).

## Links

* Documentation: <https://github.com/dariobauer/graph-onedrive/blob/main/docs/>
* License: <https://github.com/dariobauer/graph-onedrive/blob/main/LICENSE>
* Change Log: <https://github.com/dariobauer/graph-onedrive/blob/main/CHANGES.md>
* PyPI Releases: <https://pypi.org/project/graph-onedrive>
* Source Code: <https://github.com/dariobauer/graph-onedrive/>
* Contributing: <https://github.com/dariobauer/graph-onedrive/blob/main/CONTRIBUTING.md>
* Issue Tracker: <https://github.com/dariobauer/graph-onedrive/issues>
