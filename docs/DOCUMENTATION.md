# Documentation

## General

### Azure app creation

Before the package can interact with the Graph API, it must first create an authenticated session with the Microsoft identity platform.

The Graph API operates securely through each request having an accompanying bearer token containing an "access token". These tokens are used to verify a session has been authenticated.
The package generates these access tokens on your behalf, acting as a native OAuth client.

Note that some Microsoft work and school accounts will not allow apps to connect with them without admin consent.

#### Step 1: Create an Azure app

To interact with the Graph API, an app needs to be registered through the [Azure portal](https://portal.azure.com/). Detailed documentation on how to do this is [available directly from Microsoft](https://docs.microsoft.com/en-us/graph/auth-register-app-v2?context=graph%2Fapi%2F1.0&view=graph-rest-1.0).

| Setup Option            | Description                                                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Supported account types | This is related to the tenant described in the next section. Essentially the more restrictive, the easier it is to get the app registered. |
| Redirect URI            | It is recommended this is left as `Web` to `http://localhost`.                                                                             |

#### Step 2: Obtain authentication details

You need to obtain your registered app's authentication details from the [Azure portal](https://portal.azure.com/) to use in the package for authentication.

| Parameter               | Location within Azure Portal                                 | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ----------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Directory (tenant) ID   | App registrations > *your app name* > Overview               | The tenant is used to restrict an app to certain accounts. `common` allows both personal Microsoft accounts as well as work/school accounts to use the app. `organizations`, and `consumers` each only allow these account types. All of these types are known as multi-tenant and require more security processes be passed to ensure that you are a legitimate developer. On the contrary, single-tenant apps restrict the app to only one work/school account (i.e. typically one company) and therefore have far fewer security requirements. Single tenants are either a GUID or domain. Refer to the [Azure docs](https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-v2-protocols#endpoints) for details. |
| Application (client) ID | App registrations > *your app name* > Overview               | The application ID that's assigned to your app. You can find this information in the portal where you registered your app. Note that this is not the client secret id but the id of the app itself.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Client secret value     | App registrations > *your app name* > Certificates & secrets | The client secret that you generated for your app in the app registration portal. Note that this allows you to set an expiry and should be checked if your app stops working. The client secret is hidden after the initial generation so it is important to copy it and keep it secure.                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

WARNING: The client secret presents a security risk if exposed. It is recommended to revoke the client secret immediately if it becomes exposed.

### Configuration

Graph-OneDrive requires the Azure app credentials and a few other items of configuration to operate. While these parameters can be input during instance creation, it is instead recommended to use a configuration file.

The configuration details required are below displayed in the typical configuration file format (json).

```json
{
    "onedrive": {
        "tenant_id": "",
        "client_id": "",
        "client_secret_value": "",
        "redirect_url": "http://localhost:8080",
        "refresh_token": null
    }
}
```

Equivalent YAML and TOML formats can also be used when the corresponding optional dependency is installed.

Note that the `onedrive` dictionary key can be any string and could facilitate multiple instances running from the same configuration file with different keys.

The `redirect_url` and `refresh_token` values are default so these lines can be removed if you are using the defaults. To learn about the refresh token, refer to the corresponding section in the docs below.

### Installation

#### Requirements

The package currently requires Python 3.9 or greater.

Release 0.4.0 can be used with Python 3.7 and 3.8.

#### Install

Install and update using [pip](https://pip.pypa.io/en/stable/getting-started/) which will use the releases hosted on [PyPI](https://pypi.org/project/graph-onedrive/#history).
Depending on your installation you may need to use `pip3` instead.

```console
pip install -U graph-onedrive
```

You can also install the in-development version:

```console
pip install -U https://github.com/dariobauer/graph-onedrive/archive/main.zip
```

#### Dependencies

##### Required Dependencies

These dependencies provide critical functions for the package to run and will typically be installed automatically if using pip as described above.

* [HTTPX](https://pypi.org/project/httpx/) - used for http requests
* [aiofiles](https://pypi.org/project/aiofiles/) - used when downloading files

##### Optional Dependencies

Optional dependencies provide secondary features that are not part of the core package functionality. These can be installed manually (e.g. `pip install pyyaml`).

* [PyYAML](https://pypi.org/project/PyYAML/) - enables .yaml config files
* [TOML](https://pypi.org/project/TOML/) or [TOML Kit](https://pypi.org/project/tomlkit/) - fully enables .toml config files (tomli, tomli-w, and tomllib can also be used but multiple need to be installed for both read and write file support)

## Command-line interface

A command-line interface tool is provided with the typical installation.

You can run the cli using ```graph-onedrive``` or ```python3 -m graph-onedrive```.

```console
graph-onedrive [-h] [-c] [-a] [-i] [-V] [-f PATH] [-k KEY]
```

### Main actions

One of the main actions must be given as an input.

| Action argument    | Description                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------ |
| -c, --configure    | Create a new configuration file, or add to an existing one with a different dictionary key |
| -a, --authenticate | Authenticate a configuration file                                                          |
| -i, --instance     | Interact with OneDrive to test your config and perform simple tasks                        |

You can combine these to run multiple tasks in succession, with a common one being `graph-onedrive -cai` which will create a config file, authenticate it, and then run an instance.

### Options to input configuration file path and key

You can use flags to specify the config file path and/or dictionary key.

| Optional argument | Description                         |
| ----------------- | ----------------------------------- |
| -f, --file PATH   | Optional path to config file        |
| -k, --key KEY     | Optional config file dictionary key |

Use these flags by using the flag followed by the input, for example:

```console
graph-onedrive -cai -f "config.json" -k "onedrive"
```

### Other commands

| Other arguments | Description                                     |
| --------------- | ----------------------------------------------- |
| -V, --version   | Returns the version of Graph-Onedrive installed |
| -h, --help      | Displays help, including a list of attributes   |

## Limitations

### Personal drives only

The Graph API provides hooks to interact with a number of drives connected to an account, including SharePoint.

However the Graph-OneDrive package currently only connects to a user's personal OneDrive, including a user's work personal, or school personal OneDrive.

### Work and school accounts may limit apps

Some Microsoft work and school accounts will not allow apps to connect with them without admin consent.

### Saving refresh tokens for multiple users

The package currently has the option to save refresh tokens for a user. While it is possible to create multiple instances with a different user for each instance, it is not possible to use a single config file for multiple users.

It is however possible to use one config file to host multiple configurations within itself by using the dictionary key described in the config file section.

### Throttling limits

TLDR; for file transfer methods keep max_connections ≤ 16

Depending on your internet connection and the sizes of the files that you and transferring may see increased transfer speeds with more connections than the default. Graph-OneDrive currently will create a new connection for every 1MiB if not limited by the max_connections. If you have a really fast connection having many connections may slow the overall performance.

A word of caution on too many connections - the Graph API may throttle requests. This can be a hard throttle where all existing connections are cut and a cool-down period is enforced.
Throttling can be applied at the user level or the whole organization. [Details on throttling](https://docs.microsoft.com/en-us/graph/throttling) are available, however the [exact limits are not provided](https://docs.microsoft.com/en-us/graph/throttling).

We recommended to not exceed 16 connections for performance and to avoid throttling.

## Package use

### Package import

```python
import graph_onedrive
```

### Creating an OneDrive instance

Graph-OneDrive is an object-orientated package that uses an OneDrive class allowing you to create multiple instances of that class.

To create an instance, you need to provide the configuration.

#### a) Using a config file and the context manager (recommended)

The context manager is recommend as it will save the configuration back to file including the tokens.
Refer above section on configuration to learn about config files.

```python
from graph_onedrive import OneDriveManager

config_path = "config.json"  # path to config file
config_key = "onedrive"  # config file dictionary key (default = "onedrive")
with OneDriveManager(config_path, config_key) as onedrive:
    pass  # do stuff
```

#### b) Using a config file

Useful if wanting to use a config file but don't want to save the tokens back to file.
Refer above section on configuration to learn about config files.

```python
from graph_onedrive import OneDrive

config_path = "config.json"  # path to config file
config_key = "onedrive"  # config file dictionary key (default = "onedrive")
my_instance = OneDrive.from_file(config_path, config_key)
# do stuff
my_instance.to_file(config_path, config_key)  # optionally dump the config
```

#### c) Using in-line configuration parameters

This solution is slightly easier but could be a security issue, especially if sharing code.

```python
from graph_onedrive import OneDrive

client_id = ""
client_secret_value = ""
tenant = ""
redirect_url = "http://localhost:8080"
my_instance = OneDrive(client_id, client_secret_value, tenant, redirect_url)
# do stuff
my_instance.to_file(config_path, config_key)  # optionally dump the config
```

### Authenticating the instance

The instance must be authenticated by a user giving their delegated permission for your project to interact with the Graph API.

#### a) Authenticate at the time of instance initialization

The easiest option is to just create an instance as per above methods. A prompt will appear in the command line for you to copy a url to a web browser, authenticate, and then copy the redirected url back into the terminal.

#### b) Authenticate the config file in the command-line

You can use a config file to authenticate in the command line ahead of instance creation which is useful if your production code will not be run in a terminal. This will save a refresh token (described in the next section) to your config file.

```console
graph-onedrive -a
```

WARNING: This configuration assumes that your use of the configuration file serves one user only. If using the same code to serve multiple users then the refresh token must be stored independently of the configuration file.

### Using refresh tokens

Access tokens used to authenticate each request directly by the Graph API, without having to re-authenticate each time with the authentication server which speeds up requests. However due to security, these tokens typically expire after one hour.
To avoid having to have the user re-authorize the app with their account, refresh tokens are used instead. This process of refreshing access tokens in managed automatically by the package, however if the script ends, then the instance information is lost.

To use the refresh token to create a new instance (e.g. after running the script again), you can save the refresh token and provide it at the time of instance initiation.

WARNING: Saving the refresh token presents a security risk as it could be used by anyone with it exchange it for an access token. If a refresh token is exposed, it is recommended that the app client secret it revoked.

#### Obtaining the refresh token

##### a) Saving to a config file

If using a configuration file then it is suggested that you use the `OneDriveManager` context manager which will save the refresh token to your configuration.
Alternatively you can manually save to a file (suggested after your last API request to ensure the latest tokens are used).

```python
my_instance.to_file(config_path="config.json", config_key="onedrive")
```

Then when creating the instance again using your config file, the refresh token will be used.

WARNING: This configuration assumes that your use of the configuration file serves one user only. If using the same code to serve multiple users then the refresh token must be stored independently of the configuration file.

##### b) Saving the token manually

You can get the refresh token from your instance:

```python
refresh_token = my_instance.refresh_token
```

Then when creating an instance later, provide the refresh token to :

```python
my_instance = graph_onedrive.OneDrive(..., refresh_token=refresh_token)
```

### Context manager

#### OneDriveManager

Create an instance of the OneDrive class using a context manager (generator).
Uses from_file() on entry and to_file() on exit.

```python
with graph_onedrive.OneDriveManager(
    config_path="config.json", config_key="onedrive"
) as onedrive:
    pass
```

Keyword arguments:

* config_path (str|Path) -- path to configuration file (default = "config.json")
* config_key (str) -- key of the item storing the configuration (default = "onedrive")

Yields:

* onedrive_instance (OneDrive) -- OneDrive object instance

### Class methods

Module class constructors and deconstructors/exporters.

#### OneDrive()

Create an instance of the OneDrive class for arguments, and assist in creating and saving OneDrive class objects.

```python
onedrive_instance = graph_onedrive.OneDrive(
    client_id,
    client_secret,
    tenant="common",
    redirect_url="http://localhost:8080",
    refresh_token=None,
)
```

Positional arguments:

* client_id (str) -- Azure app client id
* client_secret (str) -- Azure app client secret

Keyword arguments:

* tenant (str) -- Azure app org tenant id number, use default if multi-tenant (default = "common")
* redirect_url (str)  -- Authentication redirection url (default = "http://localhost:8080")
* refresh_token (str) -- optional token from previous session (default = None)

Returns:

* onedrive_instance (OneDrive) -- OneDrive object instance

#### from_file

Create an instance of the OneDrive class from a configuration file.

To use yaml and toml config files the corresponding [optional dependencies](#dependencies) are required.

```python
onedrive_instance = graph_onedrive.OneDrive.from_file(
    config_path="config.json", config_key="onedrive", save_refresh_token=False
)
```

Keyword arguments:

* config_path (str|Path) -- path to configuration file (default = "config.json")
* config_key (str) -- key of the item storing the configuration (default = "onedrive")
* save_refresh_token (bool) -- save the refresh token back to the config file during instance initiation (default = False)

Returns:

* onedrive_instance (OneDrive) -- OneDrive object instance

#### to_file

Save the configuration to a configuration file.

To use yaml or toml config files the corresponding [optional dependencies](#dependencies) are required.

```python
onedrive_instance.to_file(config_path="config.json", config_key="onedrive")
```

Keyword arguments:

* config_path (str|Path) -- path to configuration file (default = "config.json")
* config_key (str) -- key of the item storing the configuration (default = "onedrive")

Returns:

* None

### Instance methods

The requests to the Graph API are made using the instance of the OneDrive class that you have created.

#### get_usage

Get the current usage and capacity of the connected OneDrive.

```python
used, capacity, units = my_instance.get_usage(unit="gb", refresh=False, verbose=False)
```

Keyword arguments:

* unit (str) -- unit to return value, either "b", "kb", "mb", "gb" (default = "gb")
* refresh (bool) -- refresh the usage data (default = False)
* verbose (bool) -- print the usage (default = False)

Returns:

* used (float) -- storage used in unit requested
* capacity (float) -- storage capacity in unit requested
* units (str) -- unit of usage

#### list_directory

List the files and folders within the input folder/root of the connected OneDrive.

```python
items = my_instance.list_directory(folder_id=None, verbose=False)
```

Keyword arguments:

* folder_id (str) -- the item id of the folder to look into, None being the root directory (default = None)
* verbose (bool) -- print the items along with their ids (default = False)

Returns:

* items (dict) -- details of all the items within the requested directory

#### search

List files and folders matching a search query.

```python
items = my_instance.search(query, top=-1, verbose=False)
```

Positional arguments:

* query (str) -- search query string

Keyword arguments:

* top (int) -- limits the results list length, use -1 to not limit (default = -1)
* verbose (bool) -- print the items along with their ids (default = False)

Returns:

* items (dict) -- details of items matching the search query

#### detail_item

Retrieves the metadata for an item by id.

```python
item_details = my_instance.detail_item(item_id, verbose=False)
```

Positional arguments:

* item_id (str) -- item id of the folder or file

Keyword arguments:

* verbose (bool) -- print the main parts of the item metadata (default = False)

Returns:

* items (dict) -- metadata of the requested item

#### detail_item_path

Retrieves the metadata for an item by path.

```python
item_details = my_instance.detail_item_path(item_path, verbose=False)
```

Positional arguments:

* item_path (str) -- drive root path to the folder or file (e.g. "/pictures/Holiday 01.jpg")

Keyword arguments:

* verbose (bool) -- print the main parts of the item metadata (default = False)

Returns:

* items (dict) -- metadata of the requested item

#### item_type

Returns the item type in str format.

```python
item_type = my_instance.item_type(item_id)
```

Positional arguments:

* item_id (str) -- item id of the folder or file

Returns:

* type (str) -- "folder" or "file"

#### is_folder

Checks if an item is a folder.

```python
item_type = my_instance.is_folder(item_id)
```

Positional arguments:

* item_id (str) -- item id of the folder or file

Returns:

* folder (bool) -- True if folder, else false.

#### is_file

Checks if an item is a file.

```python
item_type = my_instance.is_file(item_id)
```

Positional arguments:

* item_id (str) -- item id of the folder or file

Returns:

* file (bool) -- True if file, else false.

#### create_share_link

Creates a basic sharing link for an item.

```python
link = my_instance.create_share_link(
    item_id, link_type="view", password=None, expiration=None, scope="anonymous"
)
```

Positional arguments:

* item_id (str) -- item id of the folder or file

Keyword arguments:

* link_type (str) -- type of sharing link to create, either "view", "edit", or ("embed" for OneDrive personal only) (default = "view")
* password (str) -- password for the sharing link (OneDrive personal only) (default = None)
* expiration (datetime) -- expiration of the sharing link, computer local timezone assumed for 'native' datetime objects (default = None)
* scope (str) -- "anonymous" for anyone with the link, or ("organization" to limit to the tenant for OneDrive Business) Note businesses may choose to disable anonymous links which will result in an error (default = "anonymous")

Returns:

* link (str) -- typically a web link, html iframe if link_type="embed"

#### make_folder

Creates a new folder within the input folder/root of the connected OneDrive.

```python
folder_id = my_instance.make_folder(
    folder_name, parent_folder_id=None, check_existing=True, if_exists="rename"
)
```

Positional arguments:

* folder_name (str) -- the name of the new folder

Keyword arguments:

* parent_folder_id (str) -- the item id of the parent folder, None being the root directory (default = None)
* check_existing (bool) -- checks parent and returns folder_id if a matching folder already exists (default = True)
* if_exists (str) -- if check_existing is set to False; action to take if the new folder already exists, either "fail", "replace", "rename" (default = "rename")

Returns:

* folder_id (str) -- newly created folder item id

#### move_item

Moves an item (folder/file) within the connected OneDrive. Optionally rename an item at the same time.

```python
item_id, folder_id = my_instance.move_item(item_id, new_folder_id, new_name=None)
```

Positional arguments:

* item_id (str) -- item id of the folder or file to move
* new_folder_id (str) -- item id of the folder to shift the item to

Keyword arguments:

* new_name (str) -- optional new item name with extension (default = None)

Returns:

* item_id (str) -- item id of the folder or file that was moved, should match input item id
* folder_id (str) -- item id of the new parent folder, should match input folder id

#### copy_item

Copies an item (folder/file) within the connected OneDrive server-side.

```python
item_id = my_instance.copy_item(
    item_id, new_folder_id, new_name=None, confirm_complete=True, verbose=False
)
```

Positional arguments:

* item_id (str) -- item id of the folder or file to copy
* new_folder_id (str) -- item id of the folder to copy the item to

Keyword arguments:

* new_name (str) -- optional new item name with extension (default = None)
* confirm_complete (bool) -- waits for the copy operation to finish before returning (default = True)
* verbose (bool) -- prints status message during the download process (default = False)

Returns:

* item_id (str | None) -- item id of the new item (None returned if confirm_complete set to False)

#### rename_item

Renames an item (folder/file) without moving it within the connected OneDrive.

```python
item_name = my_instance.rename_item(item_id, new_name)
```

Positional arguments:

* item_id (str) -- item id of the folder or file to rename
* new_name (str) -- new item name with extension

Returns:

* item_name (str) -- new name of the folder or file that was renamed

#### delete_item

Deletes an item (folder/file) within the connected OneDrive. Potentially recoverable in the OneDrive web browser client.

```python
confirmation = my_instance.delete_item(item_id, pre_confirm=False)
```

Positional arguments:

* item_id (str) -- item id of the folder or file to be deleted

Keyword arguments:

* pre_confirm (bool) -- confirm that you want to delete the file and not show the warning (default = False)

Returns:

* confirmation (bool) -- True if item was deleted successfully

#### download_file

Downloads a file to the current working directory asynchronously with multiple concurrent http requests for files larger than 1mb.
Note folders cannot be downloaded, you need to implement a loop instead.

```python
file_path = my_instance.download_file(
    item_id, max_connections=8, dest_dir=None, verbose=False
)
```

Positional arguments:

* item_id (str) -- item id of the file to be deleted

Keyword arguments:

* max_connections (int) -- max concurrent open http requests, refer [throttling limits](#throttling-limits)
* dest_dir (str | Path) -- destination directory for the downloaded file, default is current working directory (default = None)
* verbose (bool) -- prints the download progress (default = False)

Returns:

* file_path (Path) -- returns the path to the downloaded file including extension

#### upload_file

Uploads a file to a particular folder with a provided file name.

```python
item_id = my_instance.upload_file(
    file_path,
    new_file_name=None,
    parent_folder_id=None,
    if_exists="rename",
    verbose=False,
)
```

Positional arguments:

* file_path (str|Path) -- path of the local source file to upload (path to the file on your computer which you are wanting to upload)

Keyword arguments:

* new_file_name (str) -- new name of the file as it should appear on OneDrive, without extension (default = None)
* parent_folder_id (str) -- item id of the folder to put the file within, if None then root (default = None)
* if_exists (str) -- action to take if the new folder already exists, either "fail", "replace", "rename" (default = "rename")
* verbose (bool) -- prints the upload progress (default = False)

Returns:

* item_id (str) -- item id of the newly uploaded file

## Examples

Examples are provided to aid in development: <https://github.com/dariobauer/graph-onedrive/blob/main/docs/examples/>

## Support and issues

* Support info, feature requests: <https://github.com/dariobauer/graph-onedrive/blob/main/CONTRIBUTING.md>
* Issue Tracker: <https://github.com/dariobauer/graph-onedrive/issues>
