# Changelog

## Unreleased


* Improved file download to asynchronously download using multiple connections
* Added HTTPX and aiofiles packages as dependencies
* Replaced Requests package with HTTPX (Issue #11)
* Added verbose keyword arguments to download and upload functions
* Improved error handling
* item_type, is_file, is_folder methods added
* Fixed a bug in the copy_item method
* Set the copy_item method to confirm the copy by default
* Documentation updates
* Updates to authors.md to include significant contributor (Shub77)

## Released

### Version 0.0.1a10

Released 2021-10-21

* Major improvements to the cli, now uses argparse, docs updated
* Removed access token validation (Issue #4)
* Allowed access token response to continue when no refresh token provided (Issue #6)
* Various dictionary value lookups improved to account for missing keys (Issue #7)

### Version 0.0.1a9

Released 2021-10-20

* Improved code typing
* Updated code formatting
* Improved validation of authorization codes and access tokens (Issues #3 & #4)

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
