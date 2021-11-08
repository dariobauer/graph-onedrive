[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/dariobauer/graph-onedrive/main.svg)](https://results.pre-commit.ci/latest/github/dariobauer/graph-onedrive/main) [![PyPI version](https://badge.fury.io/py/graph-onedrive.svg)](https://pypi.org/project/graph-onedrive/)

# Graph-OneDrive

Interact with Microsoft's OneDrive service using the Graph API.

The Graph-OneDrive package facilitates the creation of OneDrive class instances which are objects that you can use to interact with OneDrive sessions. Thus multiple OneDrives can be connected to in parallel.

Functions include:

* listing directories
* moving, copying, and renaming files and folders
* uploading and asynchronously downloading files
* getting file and drive metadata including usage

## Azure app requirement

For the package to connect to the Graph API, you need to have an app registered in the Microsoft Azure Portal. The [documentation][docs] provides basic guidance on how to register an app.

Note that some Microsoft work and school accounts will not allow apps to connect with them without admin consent.

## Installation

The package currently requires Python 3.7 or greater.

Install and update using [pip](https://pip.pypa.io/en/stable/getting-started/) which will use the releases hosted on [PyPI][releases]. Further options in the docs.

```console
pip install graph-onedrive
```

## Documentation

Documentation and examples are [provided on GitHub in the docs folder][docs].

### A simple example

Run this command in the terminal after installation which will create a config file in the current working directory.

```console
graph-onedrive --configure --authenticate -f "config.json" -k "onedrive"
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

This project itself is subject to BSD 3-Clause License detailed in [LICENSE][license].

The Graph API is provided by Microsoft Corporation and subject to their [terms of use](https://docs.microsoft.com/en-us/legal/microsoft-apis/terms-of-use).

## Links

* [Documentation][docs]
* [License][license]
* [Change Log](https://github.com/dariobauer/graph-onedrive/blob/main/CHANGES.md)
* [PyPI Releases][releases]
* [Source Code](https://github.com/dariobauer/graph-onedrive/)
* [Contributing](https://github.com/dariobauer/graph-onedrive/blob/main/CONTRIBUTING.md)
* [Issue Tracker](https://github.com/dariobauer/graph-onedrive/issues)

[docs]: <https://github.com/dariobauer/graph-onedrive/blob/main/docs/> "Graph-OneDrive Documentation"
[license]: <https://github.com/dariobauer/graph-onedrive/blob/main/LICENSE> "Graph-OneDrive License"
[releases]: <https://pypi.org/project/graph-onedrive/#history> "History of Graph-OneDrive releases on PyPI"
