[![Tests](https://github.com/dariobauer/graph-onedrive/actions/workflows/tests.yml/badge.svg)](https://github.com/dariobauer/graph-onedrive/actions/workflows/tests.yml) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/dariobauer/graph-onedrive/main.svg)](https://results.pre-commit.ci/latest/github/dariobauer/graph-onedrive/main) [![PyPI version](https://img.shields.io/pypi/v/graph-onedrive)][pypi] [![Supported Python versions](https://img.shields.io/pypi/pyversions/graph-onedrive)][pypi]

# Graph-OneDrive

Interact with Microsoft's OneDrive service using the Graph API.

The Graph-OneDrive package facilitates the creation of OneDrive class instances which are objects that you can use to interact with OneDrive sessions. Thus multiple OneDrives can be connected to in parallel.

Functions include:

* listing directories
* moving, copying, and renaming files and folders
* uploading and asynchronously downloading files
* getting file and drive metadata including usage
* getting links to files and creating sharing links

## Azure app requirement

For the package to connect to the Graph API, you need to have an app registered in the Microsoft Azure Portal. The [documentation][docs] provides basic guidance on how to register an app.

Note that some Microsoft work and school accounts will not allow apps to connect with them without admin consent.

## Installation

The package currently requires Python 3.9 or greater.
The last version to support Python 3.7 and 3.8 was release 0.4.0 which can still be installed.

Install and update using [pip](https://pip.pypa.io/en/stable/getting-started/) which will use the releases hosted on [PyPI][pypi]. Further options in the docs.

```console
pip install -U graph-onedrive
```

## Documentation

Documentation and examples are [provided on GitHub in the docs folder][docs].

### A simple example

*This is a simple example using a config file. Refer to the documentation for other instance constructors including inline options.*

Run this command in the terminal after installation which will create a config file in the current working directory.

```console
graph-onedrive --configure --authenticate -f "config.json" -k "onedrive"
```

Save the following in a .py file in the same folder.

```python
from graph_onedrive import OneDriveManager

# Use a context manager to manage the session
with OneDriveManager(config_path="config.json", config_key="onedrive") as my_drive:
    # Print the OneDrive usage
    my_drive.get_usage(verbose=True)

    # Upload a file to the root directory
    new_file_id = my_drive.upload_file("my-photo.jpg", verbose=True)
```

## License and Terms of Use

This project itself is subject to BSD 3-Clause License detailed in [LICENSE][license].

The Graph API is provided by Microsoft Corporation and subject to their [terms of use](https://docs.microsoft.com/en-us/legal/microsoft-apis/terms-of-use).

## Links

* [Documentation][docs]
* [License][license]
* [Change Log](https://github.com/dariobauer/graph-onedrive/blob/main/CHANGES.md)
* [PyPI][pypi]
* [PyPI Release History][releases]
* [Source Code](https://github.com/dariobauer/graph-onedrive/)
* [Contributing](https://github.com/dariobauer/graph-onedrive/blob/main/CONTRIBUTING.md)
* [Issue Tracker](https://github.com/dariobauer/graph-onedrive/issues)

[docs]: <https://github.com/dariobauer/graph-onedrive/blob/main/docs/> "Graph-OneDrive Documentation"
[license]: <https://github.com/dariobauer/graph-onedrive/blob/main/LICENSE> "Graph-OneDrive License"
[releases]: <https://pypi.org/project/graph-onedrive/#history> "History of Graph-OneDrive releases on PyPI"
[pypi]:  <https://pypi.org/project/graph-onedrive/> "Graph-OneDrive on PyPI"
