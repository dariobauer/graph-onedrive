"""Contains the OneDrive object class to interact through the Graph API using the Python package Graph-OneDrive.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import secrets
import shutil
import tempfile
import urllib.parse
import warnings
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from json.decoder import JSONDecodeError
from pathlib import Path
from time import sleep
from typing import Any

import aiofiles
import httpx

from graph_onedrive.__init__ import __version__
from graph_onedrive._decorators import token_required


class GraphAPIError(Exception):
    """Exception raised when Graph API returns an error status."""

    pass


class OneDrive:
    """Creates an instance to interact with Microsoft's OneDrive platform through their Graph API.
    Positional arguments:
        client_id (str)     -- Azure app client id
        client_secret (str) -- Azure app client secret
    Keyword arguments:
        tenant (str)        -- Azure app org tenant id number, use default if multi-tenant (default = "common")
        redirect_url (str)  -- Authentication redirection url (default = "http://localhost:8080")
        refresh_token (str) -- optional token from previous session (default = None)
    Attributes:
        refresh_token (str) -- single-use token to supply when recreating the instance to skip authorization
    Constructor methods:
        from_dict           -- create an instance from a dictionary
        from_json           -- create an instance from a json file
        to_json             -- export an instance configuration to a json file
    Methods:
        get_usage           -- account current usage and total capacity
        list_directory      -- lists all of the items and their attributes within a directory
        detail_item         -- get item details by item id
        detail_item_path    -- get item details by drive path
        item_type           -- get item type, folder or file
        is_folder           -- check if an item is a folder
        is_file             -- check if an item is a file
        create_share_link   -- create a sharing link for a file or folder
        make_folder         -- creates a folder
        move_item           -- moves an item
        copy_item           -- copies an item
        rename_item         -- renames an item
        delete_item         -- deletes an item
        download_file       -- downloads a file to the working directory
        upload_file         -- uploads a file
    """

    # Set class constants for the Graph API
    _API_VERSION = "v1.0"
    _API_URL = "https://graph.microsoft.com/" + _API_VERSION + "/"
    _AUTH_BASE_URL = "https://login.microsoftonline.com/"
    _AUTH_ENDPOINT = "/oauth2/v2.0/"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant: str = "common",
        redirect_url: str = "http://localhost:8080",
        refresh_token: str | None = None,
    ) -> None:
        # Set private attributes after checking types
        if not isinstance(client_id, str):
            raise TypeError(
                f"client_id expected 'str', got {type(client_id).__name__!r}"
            )
        self._client_id = client_id
        if not isinstance(client_secret, str):
            raise TypeError(
                f"client_secret expected 'str', got {type(client_secret).__name__!r}"
            )
        self._client_secret = client_secret
        if not isinstance(tenant, str):
            raise TypeError(f"tenant expected 'str', got {type(tenant).__name__!r}")
        self._tenant_id = tenant
        self._auth_url = self._AUTH_BASE_URL + self._tenant_id + self._AUTH_ENDPOINT
        self._scope = "offline_access files.readwrite"
        if not isinstance(redirect_url, str):
            raise TypeError(
                f"redirect_url expected 'str', got {type(redirect_url).__name__!r}"
            )
        self._redirect = redirect_url
        self._drive_path = "me/drive/"
        self._api_drive_url = self._API_URL + self._drive_path
        self._access_token = ""
        self._access_expires = 0.0
        # Set public attributes
        if refresh_token:
            if not isinstance(refresh_token, str):
                raise TypeError(
                    f"refresh_token expected 'str', got {type(refresh_token).__name__!r}"
                )
            self.refresh_token: str = refresh_token
        else:
            self.refresh_token = ""
        # Initiate generation of authorization tokens
        self._get_token()
        self._create_headers()
        # Set additional attributes from the server
        self._get_drive_details()
        logging.debug(
            f"Graph-OneDrive version={__version__}, client_id={client_id}, tenant={tenant}"
        )

    def __repr__(self) -> str:
        return f"<OneDrive {self._drive_type} {self._drive_name} {self._owner_name}>"

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> OneDrive:
        """Create an instance of the OneDrive class from a dictionary.
        Keyword arguments:
            config (dict) -- dictionary containing at minimum tenant_id, client_id, client_secret_value
        Returns:
            onedrive_instance (OneDrive) -- OneDrive object instance
        """
        # Check config contents
        try:
            tenant_id = config["tenant_id"]
        except KeyError:
            raise KeyError("expected tenant_id in first level of dictionary")
        try:
            client_id = config["client_id"]
        except KeyError:
            raise KeyError("expected client_id in first level of dictionary")
        try:
            client_secret = config["client_secret_value"]
        except KeyError:
            raise KeyError("expected client_secret_value in first level of dictionary")
        try:
            redirect_url = config["redirect_url"]
        except KeyError:
            redirect_url = "http://localhost:8080"
        try:
            refresh_token = config["refresh_token"]
        except KeyError:
            refresh_token = None
        # Create OneDrive object instance
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            tenant=tenant_id,
            redirect_url=redirect_url,
            refresh_token=refresh_token,
        )

    @classmethod
    def from_json(
        cls,
        file_path: str | Path = "config.json",
        config_key: str = "onedrive",
        save_refresh_token: bool = False,
    ) -> OneDrive:
        """Create an instance of the OneDrive class from a config json file.
        Keyword arguments:
            file_path (str|Path) -- path to configuration json file (default = "config.json")
            config_key (str) -- key of the json item storing the configuration (default = "onedrive")
            save_refresh_token (bool) -- save the refresh token back to the config file during instance initiation (default = False)
        Returns:
            onedrive_instance (OneDrive) -- OneDrive object instance
        """
        # Check types
        if not isinstance(file_path, str) and not isinstance(file_path, Path):
            raise TypeError(
                f"config_path expected 'str' or 'Path', got {type(file_path).__name__!r}"
            )
        if not isinstance(config_key, str):
            raise TypeError(
                f"config_key expected 'str', got {type(config_key).__name__!r}"
            )
        # Read configuration from config file
        logging.info("reading OneDrive configuration")
        config_path = Path(file_path)
        with open(config_path) as config_file:
            config = json.load(config_file)
        if config_key not in config:
            raise KeyError(
                f"config_key '{config_key}' not found in '{config_path.name}'"
            )
        # Create the instance
        onedrive_instance = cls.from_dict(config[config_key])
        # Get refresh token from instance and update config file
        if save_refresh_token:
            logging.info("saving refresh token")
            with open(config_path) as config_file:
                config = json.load(config_file)
            config[config_key]["refresh_token"] = onedrive_instance.refresh_token
            with open(config_path, "w") as config_file:
                json.dump(config, config_file, indent=4)
        # Return the OneDrive instance
        return onedrive_instance

    def to_json(
        self, file_path: str | Path = "config.json", config_key: str = "onedrive"
    ) -> None:
        """Save the configuration to a json config file.
        Keyword arguments:
            file_path (str|Path) -- path to configuration json file (default = "config.json")
            config_key (str) -- key of the json item storing the configuration (default = "onedrive")
        """
        # Check types
        if not isinstance(file_path, str) and not isinstance(file_path, Path):
            raise TypeError(
                f"file_path expected 'str' or 'Path', got {type(file_path).__name__!r}"
            )
        if not isinstance(config_key, str):
            raise TypeError(
                f"config_key expected 'str', got {type(config_key).__name__!r}"
            )
        # Read the existing configuration from the file if one exists
        try:
            with open(file_path) as config_file:
                logging.debug(f"attempting to load exiting config '{file_path}'")
                config = json.load(config_file)
        except FileNotFoundError:
            config = {}
        # Create the config key
        if config_key not in config:
            config[config_key] = {}
        # Set the new configuation
        config[config_key]["tenant_id"] = self._tenant_id
        config[config_key]["client_id"] = self._client_id
        config[config_key]["client_secret_value"] = self._client_secret
        config[config_key]["redirect_url"] = self._redirect
        config[config_key]["refresh_token"] = self.refresh_token
        # Save the configuration to config file
        with open(file_path, "w") as config_file:
            json.dump(config, config_file, indent=4)
        # Nothing returned which signals no errors
        logging.info(f"saved config to '{file_path}' with key '{config_key}'")

    def _raise_unexpected_response(
        self,
        response: httpx.Response,
        expected: int | list[int] = 200,
        message: str = "could not complete request",
        has_json: bool = False,
    ) -> None:
        """INTERNAL: Checks a API HTTPX Response object status and raises an exception if not as expected.
        Positional arguments:
            response (Response) -- HTTPX response object
        Keyword arguments:
            expected (int|[int]) -- valid status checks expected (default = 200)
            message (str) -- exception message to display (default = "could not complete request")
            has_json (bool) -- check the response has json (default = False)
        """
        # Ensure expected is a list
        expected = expected if isinstance(expected, list) else [expected]
        # Check the status code
        if response.status_code not in expected:
            # Try get the api error message and raise an exception
            graph_error = "no error message returned"
            if response.headers.get("content-type") == "application/json":
                api_error = response.json().get("error", {}).get("message")
                auth_error = response.json().get("error_description")
                if api_error:
                    graph_error = api_error
                elif auth_error:
                    graph_error = auth_error
                logging.debug(f"response_json={response.json()}")
            logging.debug(
                f"expected_codes={expected}, response_code={response.status_code}, package_error={message}"
            )
            raise GraphAPIError(f"{message} ({graph_error})")
        # Check response has json
        if has_json:
            try:
                response.json()
            except JSONDecodeError:
                graph_error = "response did not contain json"
                raise GraphAPIError(f"{message} ({graph_error})")

    def _get_token(self) -> None:
        """INTERNAL: Get access and refresh tokens from the Graph API.
        Calls get_authorization function if an existing refresh token (from a previous session) is not provided.
        """
        request_url = self._auth_url + "token"
        # Generate request body as an url encoded query
        query = {
            "client_id": self._client_id,
            "scope": self._scope,
            "redirect_uri": self._redirect,
            "client_secret": self._client_secret,
        }

        # Set grant type
        # If no refresh token provided, get new authorization code
        if self.refresh_token != "":
            query["grant_type"] = "refresh_token"
            query["refresh_token"] = self.refresh_token
        else:
            query["grant_type"] = "authorization_code"
            query["code"] = self._get_authorization()

        # Set the header and encode the query
        headers = {"content-type": "application/x-www-form-urlencoded"}
        query_encoded = urllib.parse.urlencode(query, encoding="utf-8")
        logging.debug(f"token request query={query_encoded}")

        # Make the request
        logging.info(f"requesting access and refresh tokens from {request_url}")
        response = httpx.post(request_url, headers=headers, content=query_encoded)

        # Check and parse the response
        self._raise_unexpected_response(
            response, 200, "could not get access token", has_json=True
        )
        response_data = response.json()

        # Set the access and refresh tokens to the instance attributes
        if not response_data.get("access_token"):
            logging.error("response did not return an access token")
            raise GraphAPIError("response did not return an access token")
        self._access_token = response_data["access_token"]

        if response_data.get("refresh_token"):
            self.refresh_token = response_data["refresh_token"]
        else:
            logging.warning(
                "token request did not return a refresh token, existing config not updated"
            )

        # Set an expiry time, removing 60 seconds assumed for processing
        expires = response_data.get("expires_in", 660) - 60
        expires = datetime.now() + timedelta(seconds=expires)
        logging.info(f"access token expires: {expires}")
        self._access_expires = datetime.timestamp(expires)

    def _get_authorization(self) -> str:
        """INTERNAL: Get authorization code by generating a url for the user to authenticate and authorize the app with.
        The user then return the response manually for the function to then extract the authorization code from.
        The authorization code has a short life and should only be used to generate access and refresh tokens.
            Returns:
                authorization_code (str) -- Graph API authorization code valid once for about 10 mins
        """
        # Create state used for check
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"  # = string.ascii_letters + string.digits
        state = "".join(secrets.choice(alphabet) for _ in range(10))
        # Generate request url
        request_url = self._auth_url + "authorize"
        request_url += "?client_id=" + self._client_id
        request_url += "&response_type=code"
        request_url += "&redirect_uri=" + urllib.parse.quote(self._redirect, safe="")
        request_url += "&response_mode=query"
        request_url += "&scope=" + urllib.parse.quote(self._scope)
        request_url += "&state=" + state
        # Make request (manually)
        print("Manual app authorization required.")
        print("Step 1: Copy the below URL and paste into a web browser.")
        print("AUTHORIZATION URL --------------")
        print(request_url)
        print("--------------------------------")
        print("Step 2: Authorize the app using your account.")
        print("You will be redirected (potentially to an error page - this is normal).")
        print("Step 3: Copy the entire response URL address.")
        response = input("Step 4: paste the response here: ").strip()
        # Verify the state which ensures the response is for this request
        return_state = re.search("[?|&]state=([^&]+)", response)
        if return_state:
            if return_state.group(1) != state:
                error_message = "response 'state' not for this request, occurs when reusing an old authorization url"
                logging.error(error_message)
                raise GraphAPIError(error_message)
        else:
            logging.warning(
                "response 'state' was not in returned url, response not confirmed"
            )
        # Extract the code from the response
        authorization_code_re = re.search("[?|&]code=([^&]+)", response)
        if authorization_code_re is None:
            error_message = "response did not contain an authorization code"
            logging.error(error_message)
            raise GraphAPIError(error_message)
        authorization_code = authorization_code_re.group(1)
        # Return the authorization code to be used to get tokens
        return authorization_code

    def _create_headers(self) -> None:
        """INTERNAL: Create headers for the http request to the Graph API."""
        if self._access_token == "":
            raise ValueError("expected self._access_token to be set, got empty string")
        self._headers = {
            "Accept": "*/*",
            "Authorization": "Bearer " + self._access_token,
        }

    @token_required
    def _get_drive_details(self) -> None:
        """INTERNAL: Gets the drive details"""
        # Generate request url
        request_url = self._api_drive_url
        response = httpx.get(request_url, headers=self._headers)
        self._raise_unexpected_response(
            response, 200, "could not get drive details", has_json=True
        )
        response_data = response.json()
        # Set drive details
        self._drive_id = response_data.get("id")
        self._drive_name = response_data.get("name")
        self._drive_type = response_data.get("driveType")
        response_data_user = response_data.get("owner", {}).get("user", {})
        self._owner_id = response_data_user.get("id")
        self._owner_email = response_data_user.get("email")
        self._owner_name = response_data_user.get("displayName")
        response_data_quota = response_data.get("quota", {})
        self._quota_used = response_data_quota.get("used")
        self._quota_remaining = response_data_quota.get("remaining")
        self._quota_total = response_data_quota.get("total")

    @token_required
    def get_usage(
        self, unit: str = "gb", refresh: bool = False, verbose: bool = False
    ) -> tuple[float, float, str]:
        """Get the current usage and capacity of the connected OneDrive.
        Keyword arguments:
            unit (str) -- unit to return value ["b", "kb", "mb", "gb"] (default = "gb")
            refresh (bool) -- refresh the usage data (default = False)
            verbose (bool) -- print the usage (default = False)
        Returns:
            used (float) -- storage used in unit requested
            capacity (float) -- storage capacity in unit requested
            units (str) -- unit of usage
        """
        # Validate unit
        if not isinstance(unit, str):
            raise TypeError(f"unit expected 'str', got {type(unit).__name__!r}")
        unit = unit.lower()
        if unit not in ("b", "kb", "mb", "gb"):
            raise ValueError(f"{unit!r} is not a supported unit")
        # Refresh drive details
        if refresh:
            self._get_drive_details()
        # Read usage values
        used = self._quota_used
        capacity = self._quota_total
        # Convert to requested unit unit
        if unit == "gb":
            used = round(used / (1024 * 1024 * 1024), 1)
            capacity = round(capacity / (1024 * 1024 * 1024), 1)
        elif unit == "mb":
            used = round(used / (1024 * 1024), 1)
            capacity = round(capacity / (1024 * 1024), 1)
        elif unit == "kb":
            used = round(used / (1024), 1)
            capacity = round(capacity / (1024), 1)
        else:
            unit = "b"
        # Print usage
        if verbose:
            print(
                f"Using {used} {unit} ({used*100/capacity:.2f}%) of total {capacity} {unit}."
            )
        # Return usage and capacity in requested units
        return used, capacity, unit

    @token_required
    def list_directory(
        self, folder_id: str | None = None, verbose: bool = False
    ) -> list[dict[Any, Any]]:
        """List the files and folders within the input folder/root of the connected OneDrive.
        Keyword arguments:
            folder_id (str) -- the item id of the folder to look into, None being the root directory (default = None)
            verbose (bool) -- print the items along with their ids (default = False)
        Returns:
            items (dict) -- details of all the items within the requested directory
        """
        # Check if folder id was provided and create the request url
        if folder_id:
            if not isinstance(folder_id, str):
                raise TypeError(
                    f"folder_id expected 'str', got {type(folder_id).__name__!r}"
                )
            request_url = self._api_drive_url + "items/" + folder_id + "/children"
        else:
            request_url = self._api_drive_url + "root/children"
        # Make the Graph API request
        items_list = []
        while True:
            response = httpx.get(request_url, headers=self._headers)
            # Validate request response and parse
            self._raise_unexpected_response(
                response, 200, "directory could not be listed", has_json=True
            )
            response_data = response.json()
            # Add the items to the item list
            items_list += response_data.get("value", {})
            # Break if these is no next link, else set the request link
            if response_data.get("@odata.nextLink") is None:
                break
            else:
                request_url = response_data["@odata.nextLink"]
        # Print the items in the directory along with their item ids
        if verbose:
            for item in items_list:
                print(item["id"], item["name"])
        # Return the items dictionary
        return items_list

    @token_required
    def detail_item(self, item_id: str, verbose: bool = False) -> dict[str, Any]:
        """Retrieves the metadata for an item.
        Positional arguments:
            item_id (str) -- item id of the folder or file
        Keyword arguments:
            verbose (bool) -- print the main parts of the item metadata (default = False)
        Returns:
            item_details (dict) -- metadata of the requested item
        """
        # Validate item id
        if not isinstance(item_id, str):
            raise TypeError(f"item_id expected 'str', got {type(item_id).__name__!r}")
        # Create request url based on input item id
        request_url = self._api_drive_url + "items/" + item_id
        # Make the Graph API request
        response = httpx.get(request_url, headers=self._headers)
        # Validate request response and parse
        self._raise_unexpected_response(
            response, 200, "item could not be detailed", has_json=True
        )
        response_data = response.json()
        # Print the item details
        if verbose:
            self._print_item_details(response_data)
        # Return the item details
        return response_data

    @token_required
    def detail_item_path(self, item_path: str, verbose: bool = False) -> dict[str, Any]:
        """Retrieves the metadata for an item from a web path.
        Positional arguments:
            item_path (str) -- web path of the drive folder or file
        Keyword arguments:
            verbose (bool) -- print the main parts of the item metadata (default = False)
        Returns:
            item_details (dict) -- metadata of the requested item
        """
        # Validate item id
        if not isinstance(item_path, str):
            raise TypeError(
                f"item_path expected 'str', got {type(item_path).__name__!r}"
            )
        # Create request url based on input item id
        if item_path[0] != "/":
            item_path = "/" + item_path
        request_url = self._api_drive_url + "root:" + item_path
        # Make the Graph API request
        response = httpx.get(request_url, headers=self._headers)
        # Validate request response and parse
        self._raise_unexpected_response(
            response, 200, "item could not be detailed", has_json=True
        )
        response_data = response.json()
        # Print the item details
        if verbose:
            self._print_item_details(response_data)
        # Return the item details
        return response_data

    def _print_item_details(self, item_details: dict[str, Any]) -> None:
        """INTERNAL: Prints the details of an item.
        Positional arguments:
            item_details (dict) -- item details in a dictionary format, typically from detail_item method
        """
        print("item id:", item_details.get("id"))
        print("name:", item_details.get("name"))
        if "folder" in item_details:
            print("type:", "folder")
        elif "file" in item_details:
            print("type:", "file")
        print(
            "created:",
            item_details.get("createdDateTime"),
            "by:",
            item_details.get("createdBy", {}).get("user", {}).get("displayName"),
        )
        print(
            "last modified:",
            item_details.get("lastModifiedDateTime"),
            "by:",
            item_details.get("lastModifiedBy", {}).get("user", {}).get("displayName"),
        )
        print("size:", item_details.get("size"))
        print("web url:", item_details.get("webUrl"))
        file_system_info = item_details.get("fileSystemInfo", {})
        print("file system created:", file_system_info.get("createdDateTime"))
        print(
            "file system last modified:",
            file_system_info.get("lastModifiedDateTime"),
        )
        if "file" in item_details.keys():
            hashes = item_details["file"].get("hashes")
            if isinstance(hashes, dict):
                for key, value in hashes.items():
                    print(f"file {key.replace('Hash', '')} hash:", value)
        if "folder" in item_details.keys():
            print("child count:", item_details["folder"].get("childCount"))

    def item_type(self, item_id: str) -> str:
        """Returns the item type in str format.
        Positional arguments:
            item_id (str) -- item id of the folder or file
        Returns:
            type (str) -- "folder" or "file"
        """
        item_details = self.detail_item(item_id)
        if "folder" in item_details:
            return "folder"
        else:
            return "file"

    def is_folder(self, item_id: str) -> bool:
        """Checks if an item is a folder.
        Positional arguments:
            item_id (str) -- item id of the folder or file
        Returns:
            folder (bool) -- True if folder, else false.
        """
        item_type = self.item_type(item_id)
        if item_type == "folder":
            return True
        else:
            return False

    def is_file(self, item_id: str) -> bool:
        """Checks if an item is a file.
        Positional arguments:
            item_id (str) -- item id of the folder or file
        Returns:
            file (bool) -- True if file, else false.
        """
        item_type = self.item_type(item_id)
        if item_type == "file":
            return True
        else:
            return False

    @token_required
    def create_share_link(
        self,
        item_id: str,
        link_type: str = "view",
        password: str | None = None,
        expiration: datetime | None = None,
        scope: str = "anonymous",
    ) -> str:
        """Creates a basic sharing link for an item.
        Positional arguments:
            item_id (str) -- item id of the folder or file
        Keyword arguments:
            link_type (str) -- type of sharing link to create, either "view", "edit", or ("embed" for OneDrive personal only) (default = "view")
            password (str) -- password for the sharing link (OneDrive personal only) (default = None)
            expiration (datetime) -- expiration of the sharing link, computer local timezone assumed for 'native' datetime objects (default = None)
            scope (str) -- "anonymous" for anyone with the link, or ("organization" to limit to the tenant for OneDrive Business) (default = "anonymous")
        Returns:
            link (str) -- typically a web link, html iframe if link_type="embed"
        """
        # Verify type
        if not isinstance(link_type, str):
            raise TypeError(
                f"link_type expected 'str', got {type(link_type).__name__!r}"
            )
        elif link_type not in ("view", "edit", "embed"):
            raise ValueError(
                f"link_type expected 'view', 'edit', or 'embed', got '{link_type}'"
            )
        elif link_type == "embed" and self._drive_type != "personal":
            raise ValueError(
                f"link_type='embed' is not available for {self._drive_type} OneDrive accounts"
            )
        # Verify password
        if password is not None and not isinstance(password, str):
            raise TypeError(
                f"password expected type 'str', got {type(password)}.__name__!r"
            )
        elif password is not None and self._drive_type != "personal":
            raise ValueError(
                f"password is not available for {self._drive_type} OneDrive accounts"
            )
        # Verify expiration
        if expiration is not None and not isinstance(expiration, datetime):
            raise TypeError(
                f"expiration expected type 'datetime.datetime', got {type(expiration).__name__!r}"
            )
        elif expiration is not None and datetime.now(
            timezone.utc
        ) > expiration.astimezone(timezone.utc):
            raise ValueError("expiration can not be in the past")
        # Verify scope
        if not isinstance(scope, str):
            raise TypeError(f"scope expected type 'str', got {type(scope).__name__!r}")
        elif scope not in ("anonymous", "organization"):
            raise ValueError(
                f"scope expected 'anonymous' or 'organization', got {scope}"
            )
        elif scope == "organization" and self._drive_type not in (
            "business",
            "sharepoint",
        ):
            raise ValueError(
                f"scope='organization' is not available for {self._drive_type} OneDrive accounts"
            )
        # Create the request url
        request_url = self._api_drive_url + "items/" + item_id + "/createLink"
        # Create the body
        body = {"type": link_type, "scope": scope}
        # Add link password to body if it exists
        if password is not None and password != "":
            body["password"] = password
        # Add link expiration to body if it exists
        if expiration is not None:
            expiration_iso = (
                expiration.astimezone(timezone.utc)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z")
            )
            body["expirationDateTime"] = expiration_iso
        # Make the request
        response = httpx.post(request_url, headers=self._headers, json=body)
        # Verify and parse the response
        self._raise_unexpected_response(
            response, [200, 201], "share link could not be created", has_json=True
        )
        response_data = response.json()
        # Extract the html iframe or link and return it
        if link_type == "embed":
            html_iframe = response_data.get("link", {}).get("webHtml")
            return html_iframe
        else:
            share_link = response_data.get("link", {}).get("webUrl")
            return share_link

    @token_required
    def make_folder(
        self,
        folder_name: str,
        parent_folder_id: str | None = None,
        check_existing: bool = True,
        if_exists: str = "rename",
    ) -> str:
        """Creates a new folder within the input folder/root of the connected OneDrive.
        Positional arguments:
            folder_name (str) -- the name of the new folder
        Keyword arguments:
            parent_folder_id (str) -- the item id of the parent folder, None being the root directory (default = None)
            check_existing (bool) -- checks parent and returns folder_id if a matching folder already exists (default = True)
            if_exists (str) -- if check_existing is set to False; action to take if the new folder already exists [fail, replace, rename] (default = "rename")
        Returns:
            folder_id (str) -- newly created folder item id
        """
        # Validate folder_name
        if not isinstance(folder_name, str):
            raise TypeError(
                f"folder_name expected 'str', got {type(folder_name).__name__!r}"
            )
        # Validate parent_folder_id
        if parent_folder_id and not isinstance(parent_folder_id, str):
            raise TypeError(
                f"parent_folder_id expected 'str', got {type(parent_folder_id).__name__!r}"
            )
        # Set conflict behavior
        conflict_behavior = if_exists
        if conflict_behavior not in ("fail", "replace", "rename"):
            raise ValueError(
                f"if_exists expected 'fail', 'replace', or 'rename', got {if_exists!r}"
            )
        # Create request url based on input parent folder
        if parent_folder_id:
            request_url = (
                self._api_drive_url + "items/" + parent_folder_id + "/children"
            )
        else:
            request_url = self._api_drive_url + "root/children"
        # Check if folder already exists
        if check_existing:
            items = self.list_directory(parent_folder_id)
            for item in items:
                if item.get("name") == folder_name and "folder" in item:
                    return item["id"]
        # Create the request body
        body = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": conflict_behavior,
        }
        # Make the Graph API request
        response = httpx.post(request_url, headers=self._headers, json=body)
        # Validate request response and parse
        self._raise_unexpected_response(
            response, 201, "folder not created", has_json=True
        )
        response_data = response.json()
        folder_id = response_data["id"]
        # Return the folder item id
        return folder_id

    @token_required
    def move_item(
        self, item_id: str, new_folder_id: str, new_name: str | None = None
    ) -> tuple[str, str]:
        """Moves an item (folder/file) within the connected OneDrive. Optionally rename an item at the same time.
        Positional arguments:
            item_id (str) -- item id of the folder or file to move
            new_folder_id (str) -- item id of the folder to shift the item to
        Keyword arguments:
            new_name (str) -- optional new item name with extension (default = None)
        Returns:
            item_id (str) -- item id of the folder or file that was moved, should match input item id
            folder_id (str) -- item id of the new parent folder, should match input folder id
        """
        # Validate item_id
        if not isinstance(item_id, str):
            raise TypeError(f"item_id expected 'str', got {type(item_id).__name__!r}")
        # Validate new_folder_id
        if not isinstance(new_folder_id, str):
            raise TypeError(
                f"new_folder_id expected 'str', got {type(new_folder_id).__name__!r}"
            )
        # Validate new_name
        if new_name and not isinstance(new_name, str):
            raise TypeError(f"new_name expected 'str', got {type(new_name).__name__!r}")
        # Create request url based on input item id that should be moved
        request_url = self._api_drive_url + "items/" + item_id
        # Create the request body
        body: dict[str, Any] = {"parentReference": {"id": new_folder_id}}
        if new_name:
            body["name"] = new_name
        # Make the Graph API request
        response = httpx.patch(request_url, headers=self._headers, json=body)
        # Validate request response and parse
        self._raise_unexpected_response(response, 200, "item not moved", has_json=True)
        response_data = response.json()
        item_id = response_data["id"]
        parent_folder_id = response_data["parentReference"]["id"]
        # Return the item id and parent folder id
        return item_id, parent_folder_id

    @token_required
    def copy_item(
        self,
        item_id: str,
        new_folder_id: str,
        new_name: str | None = None,
        confirm_complete: bool = True,
        verbose: bool = False,
    ) -> str | None:
        """Copies an item (folder/file) within the connected OneDrive server-side.
        Positional arguments:
            item_id (str) -- item id of the folder or file to copy
            new_folder_id (str) -- item id of the folder to copy the item to
        Keyword arguments:
            new_name (str) -- optional new item name with extension (default = None)
            confirm_complete (bool) -- waits for the copy operation to finish before returning (default = True)
            verbose (bool) -- prints status message during the download process (default = False)
        Returns:
            item_id (str | None) -- item id of the new item (None returned if confirm_complete set to False)
        """
        # Validate item_id
        if not isinstance(item_id, str):
            raise TypeError(f"item_id expected 'str', got {type(item_id).__name__!r}")
        # Validate new_folder_id
        if not isinstance(new_folder_id, str):
            raise TypeError(
                f"new_folder_id expected 'str', got {type(new_folder_id).__name__!r}"
            )
        # Validate new_name
        if new_name and not isinstance(new_name, str):
            raise TypeError(f"new_name expected 'str', got {type(new_name).__name__!r}")
        # Create request url based on input item id that should be moved
        request_url = self._api_drive_url + "items/" + item_id + "/copy"
        # Create the request body
        body: dict[str, Any] = {
            "parentReference": {"driveId": self._drive_id, "id": new_folder_id}
        }
        if new_name:
            body["name"] = new_name
        # Make the Graph API request
        response = httpx.post(request_url, headers=self._headers, json=body)
        # Validate request response and parse
        self._raise_unexpected_response(response, 202, "item not copied")
        if verbose:
            print("Copy request sent.")
        if confirm_complete:
            monitor_url = response.headers.get("Location")
            wait_duration = 1
            previous_complete = 0
            while True:
                if verbose:
                    print(f"Waiting {wait_duration:.0f}s before checking progress")
                sleep(wait_duration)
                response = httpx.get(monitor_url, follow_redirects=True)
                response_data = response.json()
                if response_data["status"] == "completed":
                    if verbose:
                        print("Copy confirmed complete.")
                    break
                percentage_complete = response_data["percentageComplete"]
                if verbose:
                    print(f"Percentage complete = {percentage_complete}%")
                try:
                    wait_duration = (
                        100.0
                        / (percentage_complete - previous_complete)
                        * wait_duration
                        - wait_duration
                    )
                except ZeroDivisionError:
                    wait_duration = 10
                if wait_duration > 10:
                    wait_duration = 10
                elif wait_duration < 1:
                    wait_duration = 1
                previous_complete = percentage_complete
            new_item_id = response_data["resourceId"]
            # Return the item id
            return new_item_id
        else:
            return None

    @token_required
    def rename_item(self, item_id: str, new_name: str) -> str:
        """Renames an item (folder/file) without moving it within the connected OneDrive.
        Positional arguments:
            item_id (str) -- item id of the folder or file to rename
            new_name (str) -- new item name with extension
        Returns:
            item_name (str) -- new name of the folder or file that was renamed
        """
        # Validate item_id
        if not isinstance(item_id, str):
            raise TypeError(f"item_id expected 'str', got {type(item_id).__name__!r}")
        # Validate new_name
        if not isinstance(new_name, str):
            raise TypeError(f"new_name expected 'str', got {type(new_name).__name__!r}")
        # Create request url based on input item id that should be renamed
        request_url = self._api_drive_url + "items/" + item_id
        # Create the request body
        body = {"name": new_name}
        # Make the Graph API request
        response = httpx.patch(request_url, headers=self._headers, json=body)
        # Validate request response and parse
        self._raise_unexpected_response(
            response, 200, "item not renamed", has_json=True
        )
        response_data = response.json()
        item_name = response_data["name"]
        # Return the item name
        return item_name

    @token_required
    def delete_item(self, item_id: str, pre_confirm: bool = False) -> bool:
        """Deletes an item (folder/file) within the connected OneDrive. Potentially restorable in the OneDrive web browser client.
        Positional arguments:
            item_id (str) -- item id of the folder or file to be deleted
        Keyword arguments:
            pre_confirm (bool) -- confirm that you want to delete the file and not show the warning (default = False)
        Returns:
            confirmation (bool) -- True if item was deleted successfully
        """
        # Validate item_id
        if not isinstance(item_id, str):
            raise TypeError(f"item_id expected 'str', got {type(item_id).__name__!r}")
        # Validate pre_confirm
        if not isinstance(pre_confirm, bool):
            raise TypeError(
                f"pre_confirm expected 'bool', got {type(item_id).__name__!r}"
            )
        # Get the user to confirm that they want to delete
        if not pre_confirm:
            confirm = (
                input("Deleted files may not be restorable. Type 'delete' to confirm: ")
                .strip()
                .lower()
            )
            if confirm != "delete":
                print("Aborted.")
                return False
        # Create request url based on input item id that should be deleted
        request_url = self._api_drive_url + "items/" + item_id
        # Make the Graph API request
        response = httpx.delete(request_url, headers=self._headers)
        # Validate request response
        self._raise_unexpected_response(response, 204, "item not deleted")
        # Return confirmation of deletion
        return True

    @token_required
    def download_file(
        self, item_id: str, max_connections: int = 8, verbose: bool = False
    ) -> str:
        """Downloads a file to the current working directory asynchronously.
        Note folders cannot be downloaded, you need to use a loop instead.
        Positional arguments:
            item_id (str) -- item id of the file to be deleted
        Keyword arguments:
            max_connections (int) -- max concurrent open http requests, refer Docs regarding throttling limits
            verbose (bool) -- prints status message during the download process (default = False)
        Returns:
            file_name (str) -- returns the name of the file including extension
        """
        # Validate item_id
        if not isinstance(item_id, str):
            raise TypeError(f"item_id expected 'str', got {type(item_id).__name__!r}")
        # Validate max_connections
        if not isinstance(max_connections, int):
            raise TypeError(
                f"max_connections expected 'int', got {type(max_connections).__name__!r}"
            )
        if max_connections > 16:
            warnings.warn(
                f"max_connections={max_connections} could result in throttling and enforced cool-down period",
                stacklevel=2,
            )
        # Get item details
        file_details = self.detail_item(item_id)
        # Check that it is not a folder
        if "folder" in file_details:
            raise ValueError("item_id provided is for a folder, expected file item id")
        file_name = file_details["name"]
        size = file_details["size"]
        # If the file is empty, just create it and return
        if size == 0:
            Path(file_name).touch()
            logging.warning(
                f"downloaded file size=0, empty file '{file_name}' created."
            )
            return file_name
        # Create request url based on input item id to be downloaded
        request_url = self._api_drive_url + "items/" + item_id + "/content"
        # Make the Graph API request
        if verbose:
            print("Getting the file download url")
        response = httpx.get(request_url, headers=self._headers)
        # Validate request response and parse
        self._raise_unexpected_response(response, 302, "could not get download url")
        download_url = response.headers["Location"]
        logging.debug(f"download_url={download_url}")
        # Download the file asynchronously
        asyncio.run(
            self._download_async(
                download_url, file_name, size, max_connections, verbose
            )
        )
        # Return the file name
        return file_name

    async def _download_async(
        self,
        download_url: str,
        file_name: str,
        file_size: int,
        max_connections: int = 8,
        verbose: bool = False,
    ) -> None:
        """INTERNAL: Creates a list of co-routines each downloading one part of the file, and starts them.
        Positional arguments:
            download_url (str) -- url of the file to download
            file_name (str) -- name of the final file
            file_size (int) -- size of the file being downloaded
        Keyword arguments:
            max_connections (int) -- max concurrent open http requests
            verbose (bool) -- prints status message during the download process (default = False)
        """
        # Assert rather then check as this is an internal method
        assert isinstance(download_url, str)
        assert isinstance(file_name, str)
        assert isinstance(file_size, int)
        assert isinstance(max_connections, int)
        tasks = list()
        file_part_names = list()
        # This httpx.AsyncClient instance will be shared among the co-routines, passed as an argument
        timeout = httpx.Timeout(10.0, read=180.0)
        client = httpx.AsyncClient(timeout=timeout)
        # Creates a new temp directory via tempfile.TemporaryDirectory()
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Min chunk size, used to calculate the  number of concurrent connections based on file size
            min_typ_chunk_size = 1 * 1024 * 1024  # 1 MiB
            # Effective number of concurrent connections
            num_coroutines = file_size // (2 * min_typ_chunk_size) + 1
            # Assures the max number of co-routines/concurrent connections is equal to the provided one
            if num_coroutines > max_connections:
                num_coroutines = max_connections
            # Calculates the final size of the chunk that each co-routine will download
            typ_chunk_size = file_size // num_coroutines
            if verbose:
                pretty_size = round(file_size / 1000000, 1)
                print(
                    f"File {file_name} ({pretty_size}mb) will be downloaded in {num_coroutines} segments."
                )
            logging.debug(
                f"file_size={file_size}B, min_typ_chunk_size={min_typ_chunk_size}B, num_coroutines={num_coroutines}, typ_chunk_size={typ_chunk_size}"
            )
            for i in range(num_coroutines):
                # Get the file part Path, placed in the temp directory
                part_file_path = Path(tmp_dir).joinpath(file_name + "." + str(i + 1))
                # We save the file part Path for later use
                file_part_names.append(part_file_path)
                # On first iteration will be 0
                start = typ_chunk_size * i
                # If this is the last part, the `end` will be set to the file size minus one
                # This is needed to be sure we download the entire file.
                if i == num_coroutines - 1:
                    end = file_size - 1
                else:
                    end = start + typ_chunk_size - 1
                # We create a task and append it to the `task` list.
                tasks.append(
                    asyncio.create_task(
                        self._download_async_part(
                            client, download_url, part_file_path, start, end, verbose
                        )
                    )
                )
            # This awaits all the tasks in the `task` list to return
            await asyncio.gather(*tasks)
            # Closing the httpx.AsyncClient instance
            await client.aclose()
            # Join the downloaded file parts
            if verbose:
                print("Joining individual segments into single file")
            with open(file_name, "wb") as fw:
                for file_part in file_part_names:
                    with open(file_part, "rb") as fr:
                        shutil.copyfileobj(fr, fw)
                    file_part.unlink()

    async def _download_async_part(
        self,
        client: httpx.AsyncClient,
        download_url: str,
        part_file_path: Path,
        start: int,
        end: int,
        verbose: bool = False,
    ) -> None:
        """INTERNAL: Co-routine to download a part of a file asynchronously.
        Positional arguments:
            client (httpx) -- client object to use to make request
            download_url (str) -- url of the file to download
            part_file_path (str) -- path to the temporary part file
            start (int) -- byte range to start the download at
            end (int) -- byte range to end the download at
        Keyword arguments:
            verbose (bool) -- prints status message during the download process (default = False)
        """
        # Each co-routine opens its own file part to write into
        async with aiofiles.open(part_file_path, "wb") as fw:
            # Build the Range HTTP header and add the auth header
            headers = {"Range": f"bytes={start}-{end}"}
            headers.update(self._headers)
            if verbose:
                part_name = part_file_path.suffix.lstrip(".")
                print(
                    f"Starting download of file segment {part_name} (bytes {start}-{end})"
                )
            logging.debug(
                f"starting download segment={part_name} start={start} end={end}"
            )
            # Create an AsyncIterator over our GET request
            async with client.stream("GET", download_url, headers=headers) as response:
                # Iterates over incoming bytes in chunks and saves them to file
                self._raise_unexpected_response(
                    response, [200, 206], "item not downloaded"
                )
                write_chunk_size = 64 * 1024  # 64 KiB
                async for chunk in response.aiter_bytes(write_chunk_size):
                    await fw.write(chunk)
            if verbose:
                print(f"Finished download of file segment {part_name}")

    @token_required
    def upload_file(
        self,
        file_path: str | Path,
        new_file_name: str | None = None,
        parent_folder_id: str | None = None,
        if_exists: str = "rename",
        verbose: bool = False,
    ) -> str:
        """Uploads a file to a particular folder with a provided file name.
        Positional arguments:
            file_path (str|Path) -- path of the local source file to upload
        Keyword arguments:
            new_file_name (str) -- new name of the file as it should appear on OneDrive, with extension (default = None)
            parent_folder_id (str) -- item id of the folder to put the file within, if None then root (default = None)
            if_exists (str) -- action to take if the new folder already exists [fail, replace, rename] (default = "rename")
            verbose (bool) -- prints status message during the download process (default = False)
        Returns:
            item_id (str) -- item id of the newly uploaded file
        """
        # Validate file_path
        if not isinstance(file_path, str) and not isinstance(file_path, Path):
            raise TypeError(
                f"file_path expected 'str' or 'Path', got {type(file_path).__name__!r}"
            )
        # Validate new_file_name
        if new_file_name and not isinstance(new_file_name, str):
            raise TypeError(
                f"new_file_name expected 'str', got {type(new_file_name).__name__!r}"
            )
        # Validate parent_folder_id
        if parent_folder_id and not isinstance(parent_folder_id, str):
            raise TypeError(
                f"parent_folder_id expected 'str', got {type(parent_folder_id).__name__!r}"
            )
        # Set conflict behavior
        conflict_behavior = if_exists
        if conflict_behavior not in ("fail", "replace", "rename"):
            raise ValueError(
                f"if_exists expected 'fail', 'replace', or 'rename', got {if_exists!r}"
            )
        # Clean file path by removing escape slashes and converting to Path object
        # To-do: avoid the pathlib as it is a resource hog
        if os.name == "nt":  # Windows
            file_path = str(file_path).replace("/", "")
        else:  # Other systems including Mac, Linux
            file_path = str(file_path).replace("\\", "")
        file_path = Path(file_path)
        logging.debug(f"file_path={file_path}")
        # Set file name
        if new_file_name:
            destination_file_name = new_file_name
        else:
            destination_file_name = file_path.name
        # Check the path is valid and points to a file
        if not os.path.isfile(file_path):
            raise ValueError(
                f"file_path expected a path to an existing file, got '{file_path!s}'"
            )
        # Get file metadata
        file_size, file_created, file_modified = self._get_local_file_metadata(
            file_path
        )
        # Create request url for the upload session
        if parent_folder_id:
            request_url = self._api_drive_url + "items/" + parent_folder_id + ":/"
        else:
            request_url = self._api_drive_url + "root:/"
        request_url += (
            urllib.parse.quote(destination_file_name) + ":/createUploadSession"
        )
        logging.debug(f"upload session request_url={request_url}")
        # Create request body for the upload session
        body = {
            "item": {
                "@microsoft.graph.conflictBehavior": conflict_behavior,
                "name": destination_file_name,
                "fileSystemInfo": {
                    "createdDateTime": file_created,
                    "lastModifiedDateTime": file_modified,
                },
            }
        }
        logging.debug(f"upload session body={body}")
        # Make the Graph API request for the upload session
        if verbose:
            print(f"Requesting upload session")
        response = httpx.post(request_url, headers=self._headers, json=body)
        # Validate upload session request response and parse
        self._raise_unexpected_response(
            response, 200, "upload session could not be created", has_json=True
        )
        upload_url = response.json()["uploadUrl"]
        logging.debug(f"upload_url={upload_url}")
        # Determine the upload file chunk size
        chunk_size: int = (
            1024 * 320 * 16
        )  # = 5MiB. Docs: Must be multiple of 320KiB, recommend 5-10MiB, max 60MiB
        no_of_uploads: int = -(-file_size // chunk_size)
        logging.debug(
            f"chunk_size={chunk_size}B, file_size={file_size}, no_of_uploads={no_of_uploads}"
        )
        if verbose and no_of_uploads > 1:
            print(
                f"File {destination_file_name} will be uploaded in {no_of_uploads} segments"
            )
        logging.info(
            f"file {destination_file_name} will be uploaded in {no_of_uploads} segments"
        )
        # Create an upload connection client
        timeout = httpx.Timeout(10.0, read=180.0, write=180.0)
        client = httpx.Client(timeout=timeout)
        # Run in a try block to capture user cancellation request
        try:
            # Open the file pointer
            if verbose:
                print("Loading file")
            logging.info(f"opening file '{file_path}'")
            data = open(file_path, "rb")
            # Start the upload in a loop for as long as there is data left to upload
            n = 0
            while data.tell() < file_size:
                # Print the upload status
                n += 1
                if n == 1:
                    content_range_start = 0
                    content_range_end = chunk_size - 1
                    if verbose:
                        print(f"Uploading segment {n}/{no_of_uploads}")
                else:
                    if verbose:
                        print(
                            f"Uploading segment {n}/{no_of_uploads} (~{int((n-1)/no_of_uploads*100)}% complete)"
                        )
                logging.debug(
                    f"uploading file segment={n}, content_range_start={content_range_start}, content_range_end={content_range_end}"
                )
                # Upload chunks
                if (file_size - data.tell()) > chunk_size:
                    # Typical chunk upload
                    headers = {
                        "Content-Range": f"bytes {content_range_start}-{content_range_end}/{file_size}"
                    }
                    content = data.read(chunk_size)
                    response = client.put(
                        upload_url,
                        headers=headers,
                        content=content,
                    )
                    # Validate request response
                    self._raise_unexpected_response(
                        response, 202, f"could not upload chuck {n} of {no_of_uploads}"
                    )
                    # Calculate next chunk range
                    content_range_start = data.tell()
                    content_range_end = data.tell() + chunk_size - 1
                else:
                    # Final chunk upload
                    content_range_end = file_size - 1
                    headers = {
                        "Content-Range": f"bytes {content_range_start}-{content_range_end}/{file_size}"
                    }
                    content = data.read(chunk_size)
                    response = client.put(
                        upload_url,
                        headers=headers,
                        content=content,
                    )
        except KeyboardInterrupt:
            httpx.delete(upload_url)
            if verbose:
                print("Upload cancelled by user.")
            raise
        except Exception:
            httpx.delete(upload_url)
            raise
        finally:
            data.close()
            client.close()
        # Validate request response
        self._raise_unexpected_response(
            response, [200, 201], "item not uploaded", has_json=True
        )
        if verbose:
            print("Upload complete")
        # Return the file item id
        response_data = response.json()
        item_id = response_data["id"]
        return item_id

    def _get_local_file_metadata(self, file_path: str | Path) -> tuple[int, str, str]:
        """Retrieves local file metadata (size, dates).
        Note results differ based on platform, with creation date not available on Linux.
        Positional arguments:
            file_path (str|Path) -- path of the local source file to upload
        Returns:
            file_size (str) -- file size in bytes (B)
            creation_date (str) -- UTC ISO format file creation timestamp
            modified_date (str) -- UTC ISO format file last modified timestamp
        """
        # Validate file_path type and that the file exists
        if not isinstance(file_path, str) and not isinstance(file_path, Path):
            raise TypeError(
                f"file_path expected 'str' or 'Path', got {type(file_path).__name__!r}"
            )
        if not os.path.isfile(file_path):
            raise ValueError(
                f"file_path expected a path to an existing file, got '{file_path!s}'"
            )
        # Get the file size
        file_size = os.path.getsize(file_path)
        # Get the file modified time
        file_modified = os.path.getmtime(file_path)
        # Get the file creation time (platform specific)
        if os.name == "nt":
            # Windows OS
            file_created = os.path.getctime(file_path)
        else:
            # Other OS
            stat = os.stat(file_path)
            try:
                # Likely Mac OS
                file_created = stat.st_birthtime
            except AttributeError:
                # Likely Linux OS, fall back to last modified.
                file_created = stat.st_mtime
        # Convert the seconds to UTC ISO timestamps
        file_created_str = (
            datetime.fromtimestamp(file_created)
            .astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        file_modified_str = (
            datetime.fromtimestamp(file_modified)
            .astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        logging.debug(
            f"platform={os.name}, file_created_str={file_created_str}, file_modified_str={file_modified_str}"
        )
        return file_size, file_created_str, file_modified_str
