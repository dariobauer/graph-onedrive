# Changelog

## Unreleased



## Released

### Version 0.1.1

Released 2021-11-30

* Added py.typed for mypy typing support
* Added ability to create sharing links (Issue [#16](https://github.com/dariobauer/graph-onedrive/issues/16))
* Improved upload to attempt to retain file creation and modified metadata (Issue [#13](https://github.com/dariobauer/graph-onedrive/issues/13))
* Improved developer experience by adding tests, testing automation (tox, GitHub Actions), requirements files, pre-commit improvements
* Input type checks added and error messaging improved
* Fixed bug in sharing links part of the CLI
* Listing a directory now gets all items, even if there are over 200
* New method detail_item_path details an item by providing a drive path instead of id
* New `OneDriveManager` context manager added
* `create` depreciated, use the OneDrive class directly
* `create_from_config_file`, use `OneDrive.from_json` or the `OneDriveManager` context manager
* `save_to_config_file`, use `OneDrive.to_json` or the `OneDriveManager` context manager
* Added basic logging
* Docs, examples, and tests updated to reflect above changes

### Version 0.1.0

Released 2021-10-29

* Improved file download to asynchronously download using multiple connections
* Added HTTPX and aiofiles packages as dependencies
* Replaced Requests package with HTTPX (Issue [#11](https://github.com/dariobauer/graph-onedrive/issues/11))
* Added verbose keyword arguments to download and upload functions
* Improved error handling
* item_type, is_file, is_folder methods added
* Fixed a bug in the copy_item method
* Set the copy_item method to confirm the copy by default
* Documentation updates
* Updates to authors.md to include significant contributor (Shub77)

### Version 0.0.1a10

Released 2021-10-21

* Major improvements to the cli, now uses argparse, docs updated
* Removed access token validation (Issue [#4](https://github.com/dariobauer/graph-onedrive/issues/4))
* Allowed access token response to continue when no refresh token provided (Issue [#6](https://github.com/dariobauer/graph-onedrive/issues/6))
* Various dictionary value lookups improved to account for missing keys (Issue [#7](https://github.com/dariobauer/graph-onedrive/issues/7))

### Version 0.0.1a9

Released 2021-10-20

* Improved code typing
* Updated code formatting
* Improved validation of authorization codes and access tokens (Issues [#3](https://github.com/dariobauer/graph-onedrive/issues/3) & [#4](https://github.com/dariobauer/graph-onedrive/issues/4))

### Version 0.0.1a8

Released 2021-10-17

* Updated exits from cli
* Moved OneDrive class from _main.py to _onedrive.py
* Moved testing and debugging decorators to /tests
* Updated some formatting using pre-commit hooks
* Docs improved including syntax highlighting
* Improved auth function to not require a session state (Pull Request #1)

### Version 0.0.1a7

Released 2021-10-13

* Minor doc fix

### Version 0.0.1a6

Released 2021-10-13

* Minor doc fix

### Version 0.0.1a5

Released 2021-10-13

* Added safeties in cli to not overwrite existing configs
* Minor doc updates and fixes

### Version 0.0.1a4

Released 2021-10-11

* json import bug fixed within cli

### Version 0.0.1a3

Released 2021-10-11

* Minor bug fix to cli

### Version 0.0.1a2

Released 2021-10-11

* Split cli auth to config and auth
* Corrected spelling 'Onedrive' to 'OneDrive'
* Moved documentation from README to /docs
* Updated documentation
* Added pre-commit file for Black
* Reformatted all code using Black
* Updated CONTRIBUTING patch section
* Updated README

### Version 0.0.1a1

Released 2021-10-10

* Initial alpha commit
