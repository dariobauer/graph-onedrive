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

General installation is using pip from PyPI, but depending on your installation you may need to use `pip3` instead.

    pip install graph-onedrive

You can also install the in-development version:

    pip install https://github.com/dariobauer/graph-onedrive/archive/master.zip

Futher information is available in the [documentation](https://github.com/dariobauer/graph-onedrive/blob/main/docs/).

## Documentation

Documentation and examples are provided on GitHub: <https://github.com/dariobauer/graph-onedrive/blob/main/docs/>

## License

This project itself is subject to BSD 3-Clause License detailed in [LICENSE](https://github.com/dariobauer/graph-onedrive/blob/main/LICENSE).

The Graph API is provided by Microsoft Corporation and subject to their [terms of use](https://docs.microsoft.com/en-us/legal/microsoft-apis/terms-of-use).

## Links

* License: <https://github.com/dariobauer/graph-onedrive/blob/main/LICENSE>
* Change Log: <https://github.com/dariobauer/graph-onedrive/blob/main/CHANGES.md>
* PyPI Releases: <https://pypi.org/project/graph-onedrive>
* Source Code: <https://github.com/dariobauer/graph-onedrive/>
* Support info, feature requests: <https://github.com/dariobauer/graph-onedrive/blob/main/CONTRIBUTING.md>
* Issue Tracker: <https://github.com/dariobauer/graph-onedrive/issues>