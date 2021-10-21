"""Contains the OneDrive object class to interact through the Graph API using the Python package Graph-OneDrive.
"""
import functools
import json
import os
import re
import secrets
import shutil
import urllib.parse
import warnings
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from time import sleep
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import requests

from graph_onedrive._decorators import token_required


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
    Methods:
        get_usage           -- account current usage and total capacity
        list_directory      -- lists all of the items and their attributes within a directory
        detail_item         -- get item details
        make_folder         -- creates a folder
        move_item           -- moves an item
        copy_item           -- copies an item
        rename_item         -- renames an item
        delete_item         -- deletes an item
        download_file       -- downloads a file to the working directory
        upload_file         -- uploads a file as a single piece if small and otherwise calls upload_large_file
        upload_large_file   -- uploads a file in chunks, typically calling upload_file is suggested
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
        refresh_token: Optional[str] = None,
    ) -> None:
        # Set private attributes
        self._client_id = client_id
        self._client_secret = client_secret
        self._tenant_id = tenant
        self._auth_url = self._AUTH_BASE_URL + self._tenant_id + self._AUTH_ENDPOINT
        self._scope = "files.readwrite"
        self._redirect = redirect_url
        self._access_token = ""
        self._access_expires = 0.0
        # Set public attributes
        if refresh_token:
            self.refresh_token: str = refresh_token
        else:
            self.refresh_token = ""
        # Initiate generation of authorization tokens
        self._get_token()
        self._create_headers()
        self._get_drive_details()

    def _get_token(self) -> None:
        """INTERNAL: Get access and refresh tokens from the Graph API.
        Calls get_authorization function if an existing refresh token (from a previous session) is not provided.
        """

        # Generate request body
        request_url = self._auth_url + "token"
        body = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": "offline_access " + self._scope,
            "redirect_uri": self._redirect,
        }

        # Set grant type
        # If no refresh token provided, get new authorization code
        if self.refresh_token != "":
            body["grant_type"] = "refresh_token"
            body["refresh_token"] = self.refresh_token
        else:
            authorization_code = self._get_authorization()
            body["grant_type"] = "authorization_code"
            body["code"] = authorization_code

        # Make the request
        response = requests.post(request_url, data=body)
        status_code = response.status_code
        response_data = json.loads(response.text)

        # Check response was okay
        if status_code != 200:
            error_descrpition = response_data.get(
                "error_description", "Unknown error - no error description returned"
            )
            raise Exception(f"API Error : {error_descrpition} ")

        # Set the access and refresh tokens to the instance attributes
        try:
            self._access_token = response_data["access_token"]
        except KeyError:
            raise Exception("Response Error : Response did not return an access token")
        try:
            self.refresh_token = response_data["refresh_token"]
        except KeyError:
            warnings.warn(
                "Response Warn : Response did not return a refresh token, existing config not updated",
                stacklevel=2,
            )

        # Set an expiry time, removing 60 seconds assumed for processing
        expires = response_data["expires_in"] - 60
        expires = datetime.now() + timedelta(seconds=expires)
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
        state = "".join(secrets.choice(alphabet) for i in range(10))

        # Generate request url
        request_url = self._auth_url + "authorize"
        request_url += "?client_id=" + self._client_id
        request_url += "&response_type=code"
        request_url += "&redirect_uri=" + urllib.parse.quote_plus(self._redirect)
        request_url += "&response_mode=query"
        request_url += "&scope=offline_access%20" + self._scope
        request_url += "&state=" + state

        # Make request (manually)
        print("Manual app authorization required.")
        print("Step 1: Copy the below URL and paste into a web browser.")
        print("AUTHORIZATION URL --------------")
        print(request_url)
        print("--------------------------------")
        print("Step 2: Authorize the app using your account.")
        print("You will be redirected (potentially to an error page - this is normal)")
        print(
            "Step 3: Copy the response URL - click into the address bar and copy all."
        )
        response = input("Step 4: paste the response here: ").strip()

        # Verify the state which ensures the response is for this request
        return_state = re.search("&state=([^&]+)", response)
        if return_state:
            if return_state.group(1) != state:
                raise Exception(
                    "Response Error : Response 'state' did not correspond to request, typically occurs when reusing an old authorization url"
                )
        else:
            warnings.warn(
                "Response Warn : Response 'state' was not in returned url, response could not be confirmed as being for this request",
                stacklevel=2,
            )

        # Extract the code from the response
        authorization_code_re = re.search("code=([^&]+)", response)
        if authorization_code_re is None:
            raise Exception("The response did not contain an authorization code.")
        authorization_code = authorization_code_re.group(1)

        # Return the authorization code to be used to get tokens
        return authorization_code

    def _create_headers(self) -> None:
        """INTENRAL: Create headers for the http request to the Graph API."""
        self._headers = {
            "Accept": "*/*",
            "Authorization": "Bearer " + self._access_token,
        }

    @token_required
    def _get_drive_details(self) -> None:
        """INTERNAL: Gets the drive details"""
        # Generate request url
        request_url = self._API_URL + "me/drive/"
        response = requests.get(request_url, headers=self._headers)
        response_data = json.loads(response.text)
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
    ) -> Tuple[float, float, str]:
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
        if refresh:
            self._get_drive_details()
        # Read usage values
        used = self._quota_used
        capacity = self._quota_total
        # Convert to requested unit unit
        if unit == "gb":
            used = round(used / (1024 * 1024 * 1024), 2)
            capacity = round(capacity / (1024 * 1024 * 1024), 2)
        elif unit == "mb":
            used = round(used / (1024 * 1024), 2)
            capacity = round(capacity / (1024 * 1024), 2)
        elif unit == "kb":
            used = round(used / (1024), 2)
            capacity = round(capacity / (1024), 2)
        else:
            unit = "b"
        # Print usage
        if verbose:
            print(
                f"Using {used} {unit} ({round(used*100/capacity, 2)}%) of total {capacity} {unit}."
            )
        # Return usage and capacity in requested units
        return used, capacity, unit

    @token_required
    def list_directory(
        self, folder_id: Optional[str] = None, verbose: bool = False
    ) -> List[Dict[Any, Any]]:
        """List the files and folders within the input folder/root of the connected OneDrive.
        Keyword arguments:
            folder_id (str) -- the item id of the folder to look into, None being the root directory (default = None)
            verbose (bool) -- print the items along with their ids (default = False)
        Returns:
            items (dict) -- details of all the items within the requested directory
        """
        # Check if folder id was provided and create the request url
        if folder_id:
            request_url = self._API_URL + "me/drive/items/" + folder_id + "/children"
        else:
            request_url = self._API_URL + "me/drive/root/children"
        # Make the Graph API request
        response = requests.get(request_url, headers=self._headers)
        # Validate request response and parse
        if response.status_code != 200:
            print(response.text)
            raise Exception(f"API Error! : {response.status_code}")
        items = json.loads(response.text)
        items = items.get("value", {})
        # Print the items in the directory along with their item ids
        if verbose:
            for entries in range(len(items)):
                print(items[entries]["name"], "| item-id >", items[entries]["id"])
        # Return the items dictionary
        return items

    @token_required
    def detail_item(self, item_id: str, verbose: bool = False) -> Dict[str, Any]:
        """Retrieves the metadata for an item.
        Positional arguments:
            item_id (str) -- item id of the folder or file
        Keyword arguments:
            verbose (bool) -- print the main parts of the item metadata (default = False)
        Returns:
            item_details (dict) -- metadata of the requested item
        """
        # Create request url based on input item id
        request_url = self._API_URL + "me/drive/items/" + item_id
        # Make the Graph API request
        response = requests.get(request_url, headers=self._headers)
        # Validate request response and parse
        if response.status_code != 200:
            print(response.text)
            raise Exception(
                f"API Error {response.status_code}: item could not be detailed."
            )
        response_data = json.loads(response.text)
        # Print the item details
        if verbose:
            print("id:", response_data.get("id"))
            print("name:", response_data.get("name"))
            if "folder" in response_data:
                print("type:", "folder")
            else:
                print("type:", "file")
            print(
                "created:",
                response_data.get("createdDateTime"),
                "by:",
                response_data.get("createdBy", {}).get("user", {}).get("displayName"),
            )
            print(
                "modified:",
                response_data.get("lastModifiedDateTime"),
                "by:",
                response_data.get("lastModifiedBy", {})
                .get("user", {})
                .get("displayName"),
            )
            print("size:", response_data.get("size"))
            print("web url:", response_data.get("webUrl"))
        # Return the item details
        return response_data

    @token_required
    def make_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None,
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
        # Create request url based on input parent folder
        if parent_folder_id:
            request_url = (
                self._API_URL + "me/drive/items/" + parent_folder_id + "/children"
            )
        else:
            request_url = self._API_URL + "me/drive/root/children"
        # Set conflict behaviour
        if if_exists == "fail":
            conflictBehavior = "fail"
        elif if_exists == "replace":
            conflictBehavior = "replace"
        elif if_exists == "rename":
            conflictBehavior = "rename"
        else:
            raise Exception(
                "if_exists input value was not valid. Str type of values 'fail', 'replace', 'rename', are only accepted."
            )
        # Check if folder already exists
        if check_existing:
            items = self.list_directory(parent_folder_id)
            for i, entry in enumerate(items):
                if entry.get("name") == folder_name and "folder" in entry:
                    return entry["id"]

        # Create the request body
        body = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": conflictBehavior,
        }
        # Make the Graph API request
        response = requests.post(request_url, headers=self._headers, json=body)
        # Validate request response and parse
        if response.status_code != 201:
            print(response.text)
            raise Exception(f"API Error {response.status_code}: folder was not created")
        response_data = json.loads(response.text)
        folder_id = response_data["id"]
        # Return the folder item id
        return folder_id

    @token_required
    def move_item(
        self, item_id: str, new_folder_id: str, new_name: Optional[str] = None
    ) -> Tuple[str, str]:
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
        # Create request url based on input item id that should be moved
        request_url = self._API_URL + "me/drive/items/" + item_id
        # Create the request body
        body: Dict[str, Any] = {"parentReference": {"id": new_folder_id}}
        if new_name:
            body["name"] = new_name
        # Make the Graph API request
        response = requests.patch(request_url, headers=self._headers, json=body)
        # Validate request response and parse
        if response.status_code != 200:
            print(response.text)
            raise Exception(
                f"API Error {response.status_code}: item could not be moved."
            )
        response_data = json.loads(response.text)
        item_id = response_data["id"]
        parent_folder_id = response_data["parentReference"]["id"]
        # Return the item id and parent folder id
        return item_id, parent_folder_id

    @token_required
    def copy_item(
        self,
        item_id: str,
        new_folder_id: str,
        new_name: Optional[str] = None,
        confirm_complete: bool = False,
    ) -> str:
        """Copies an item (folder/file) within the connected OneDrive server-side.
        Positional arguments:
            item_id (str) -- item id of the folder or file to copy
            new_folder_id (str) -- item id of the folder to copy the item to
        Keyword arguments:
            new_name (str) -- optional new item name with extension (default = None)
            confirm_complete (bool) -- waits for the copy operation to finish before returning (default = False)
        Returns:
            item_id (str) -- item id of the new item
        """
        # Create request url based on input item id that should be moved
        request_url = self._API_URL + "me/drive/items/" + item_id + "copy"
        # Create the request body
        body: Dict[str, Any] = {
            "parentReference": {"driveId": self._drive_id, "id": new_folder_id}
        }
        if new_name:
            body["name"] = new_name
        # Make the Graph API request
        response = requests.post(request_url, headers=self._headers, json=body)
        # Validate request response and parse
        if response.status_code != 202:
            raise Exception(f"API Error: item could not be copied.")
        monitor_url = response.url
        if confirm_complete:
            wait_duration = 10
            previous_complete = 0
            while True:
                sleep(wait_duration)
                response = requests.get(monitor_url)
                response_data = json.loads(response.text)
                if response_data["status"] == "completed":
                    break
                percentage_complete = response_data["percentageComplete"]
                wait_duration = (
                    100.0 / (percentage_complete - previous_complete) * wait_duration
                    - wait_duration
                )
                if wait_duration > 30:
                    wait_duration = 30
                previous_complete = percentage_complete

        new_item_id = response_data["resourceId"]
        # Return the item id
        return new_item_id

    @token_required
    def rename_item(self, item_id: str, new_name: str) -> str:
        """Renames an item (folder/file) without moving it within the connected OneDrive.
        Positional arguments:
            item_id (str) -- item id of the folder or file to rename
            new_name (str) -- new item name with extension
        Returns:
            item_name (str) -- new name of the folder or file that was renamed
        """
        # Create request url based on input item id that should be renamed
        request_url = self._API_URL + "me/drive/items/" + item_id
        # Create the request body
        body = {"name": new_name}
        # Make the Graph API request
        response = requests.patch(request_url, headers=self._headers, json=body)
        # Validate request response and parse
        if response.status_code != 200:
            print(response.text)
            raise Exception(
                f"API Error {response.status_code}: item could not be renamed."
            )
        response_data = json.loads(response.text)
        item_name = response_data["name"]
        # Return the item id and parent folder id
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
        request_url = self._API_URL + "me/drive/items/" + item_id
        # Make the Graph API request
        response = requests.delete(request_url, headers=self._headers)
        # Validate request response
        if response.status_code != 204:
            print(response.text)
            raise Exception(
                f"API Error {response.status_code}: item could not be deleted."
            )
        # Return confirmation of deletion
        return True

    @token_required
    def download_file(self, item_id: str) -> str:
        """Downloads the file to the current working directory. Note folders cannot be downloaded.
        Positional arguments:
            item_id (str) -- item id of the file to be deleted
        Returns:
            file_name (str) -- returns the name of the file including extension
        """
        # Get item details
        details = self.detail_item(item_id)
        # Check that it is not a folder
        if "folder" in details:
            raise Exception(
                "Item id provided is for a folder which this function does not permit."
            )
        # Create request url based on input item id to be downloaded
        request_url = self._API_URL + "me/drive/items/" + item_id + "/content"
        # Make the Graph API request
        response = requests.get(
            request_url, headers=self._headers, allow_redirects=False
        )
        # Validate request response and parse
        if response.status_code != 302:
            print(response.text)
            raise Exception(
                f"API Error {response.status_code}: item could not be downloaded."
            )
        download_url = response.headers["Location"]
        # Download the file
        file_name = details["name"]
        # file_name = url.split("/")[-1]
        with requests.get(download_url, stream=True) as r:
            r.raw.read = functools.partial(r.raw.read, decode_content=True)
            with open(file_name, "wb") as f:
                shutil.copyfileobj(r.raw, f, length=16 * 1024 * 1024)
        # Return the data in a text format
        return file_name

    @token_required
    def upload_file(
        self,
        file_path: Union[str, Path],
        new_file_name: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        if_exists: str = "rename",
    ) -> str:
        """Uploads a file to a particular folder with a provided file name.
        Delegates the upload task to the upload_large_file function if required.
            Positional arguments:
                file_path (str|Path) -- path of the file on the drive
            Keyword arguments:
                new_file_name (str) -- new name of the file as it should appear on OneDrive, without extension (default = None)
                parent_folder_id (str) -- item id of the folder to put the file within, if None then root (default = None)
                if_exists (str) -- action to take if the new folder already exists [fail, replace, rename] (default = "rename")
            Returns:
                item_id (str) -- item id of the newly uploaded file
        """
        # Set conflict behaviour
        if if_exists == "fail":
            conflict_behavior = "fail"
        elif if_exists == "replace":
            conflict_behavior = "replace"
        elif if_exists == "rename":
            conflict_behavior = "rename"
        else:
            raise Exception(
                "if_exists input value was not valid. Str type of values 'fail', 'replace', 'rename', are only accepted."
            )
        # Ensure file_path is a Path type and remove escape slashes
        if os.name == "nt":  # Windows
            file_path = str(file_path).replace("/", "")
        else:  # Other systems including posix (Mac, Linux)
            file_path = str(file_path).replace("\\", "")
        file_path = Path(file_path)
        # Set file name
        if new_file_name:
            file_name = new_file_name
        else:
            file_name = file_path.name
        # Checks the file size and delegates the task to the upload_large_file function if required
        file_size = os.path.getsize(file_path)
        basic_file_limit = 4 * 1024 * 1024
        if file_size > basic_file_limit:
            print(f"Large file, uploading in chunks")
            response = self.upload_large_file(
                file_path, file_name, parent_folder_id, if_exists
            )
            return response
        # Create request url based on input values
        if parent_folder_id:
            request_url = self._API_URL + "me/drive/items/" + parent_folder_id + ":/"
        else:
            request_url = self._API_URL + "me/drive/root:/"
        request_url += (
            file_name
            + ":/content"
            + "?@microsoft.graph.conflictBehavior="
            + conflict_behavior
        )
        # Open the file into memory
        print("Loading file")
        content = open(file_path, "rb")
        # Make the Graph API request
        print("Uploading file")
        response = requests.put(request_url, headers=self._headers, data=content)
        # Close file
        content.close()
        # Validate request response and parse
        if response.status_code != 201 and response.status_code != 200:
            print(response.text)
            raise Exception(
                f"API Error {response.status_code}: could not upload file: {file_path}"
            )
        response_data = json.loads(response.text)
        item_id = response_data["id"]
        # Return the file item id
        return item_id

    @token_required
    def upload_large_file(
        self,
        file_path: Union[str, Path],
        new_file_name: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        if_exists: str = "rename",
    ) -> str:
        """Uploads a file in chunks to a particular folder with a provided file name.
        Positional arguments:
            file_path (str|Path) -- path of the file on the drive
        Keyword arguments:
            new_file_name (str) -- new name of the file as it should appear on OneDrive, without extension (default = None)
            parent_folder_id (str) -- item id of the folder to put the file within, if None then root (default = None)
            if_exists (str) -- action to take if the new folder already exists [fail, replace, rename] (default = "rename")
        Returns:
            item_id (str) -- item id of the newly uploaded file
        """
        # Set conflict behaviour
        if if_exists == "fail":
            conflict_behavior = "fail"
        elif if_exists == "replace":
            conflict_behavior = "replace"
        elif if_exists == "rename":
            conflict_behavior = "rename"
        else:
            raise Exception(
                f"if_exists={if_exists} not valid. Str type of values 'fail', 'replace', 'rename', are only accepted."
            )
        # Ensure file_path is a Path type
        file_path = Path(file_path)
        # Set file name
        if new_file_name:
            file_name = new_file_name
        else:
            file_name = file_path.name
        # Create request url for the upload session
        if parent_folder_id:
            request_url = self._API_URL + "me/drive/items/" + parent_folder_id + ":/"
        else:
            request_url = self._API_URL + "me/drive/root:/"
        request_url += file_name + ":/createUploadSession"
        # Create request body for the upload session
        body = {
            "item": {
                "@odata.type": "microsoft.graph.driveItemUploadableProperties",
                "@microsoft.graph.conflictBehavior": conflict_behavior,
            }
        }
        # Make the Graph API request for the upload session
        print(f"Requesting upload session using url")
        response = requests.post(request_url, headers=self._headers)
        # Validate upload session request response and parse
        if response.status_code != 200:
            print(response.text)
            raise Exception(
                f"API Error {response.status_code}, could not upload file: {file_path}"
            )
        upload_url = json.loads(response.text)
        upload_url = upload_url["uploadUrl"]
        # Determine the upload file size and chunks
        file_size = os.path.getsize(file_path)
        chunk_size = 320 * 1024 * 10  # Has to be multiple of 320 kb
        no_of_uploads = -(-file_size // chunk_size)
        content_range_start = 0
        if file_size < chunk_size:
            content_range_end = file_size
        else:
            content_range_end = chunk_size - 1
        # Open the file pointer
        print("Loading file")
        data = open(file_path, "rb")
        # Run in a try block to capture user cancellation request
        try:
            # Start the upload in a loop for as long as there is data left to upload
            n = 0
            while data.tell() < file_size:
                # Print the upload status
                n += 1
                if n == 1:
                    print(f"Uploading chunk {n}/{no_of_uploads}")
                else:
                    print(
                        f"Uploading chunk {n}/{no_of_uploads}  (~{int((n-1)/no_of_uploads*100)}% complete)"
                    )
                # Upload chunks
                if (file_size - data.tell()) > chunk_size:
                    # Typical chunk upload
                    headers = {
                        "Content-Range": "bytes "
                        + str(content_range_start)
                        + "-"
                        + str(content_range_end)
                        + "/"
                        + str(file_size)
                    }
                    content = data.read(chunk_size)
                    response = requests.put(upload_url, headers=headers, data=content)
                    # Validate request response
                    if response.status_code != 202:
                        data.close()
                        response2 = requests.delete(upload_url)
                        raise Exception(
                            f"API Error {response.status_code}: could not upload chuck {n} of {no_of_uploads}"
                        )
                    # Calculate next chunk range
                    content_range_start = data.tell()
                    content_range_end = data.tell() + chunk_size - 1
                else:
                    # Final chunk upload
                    content_range_end = file_size - 1
                    headers = {
                        "Content-Range": "bytes "
                        + str(content_range_start)
                        + "-"
                        + str(content_range_end)
                        + "/"
                        + str(file_size)
                    }
                    content = data.read(chunk_size)
                    response = requests.put(upload_url, headers=headers, data=content)
                    print("Upload complete")
        except KeyboardInterrupt:
            # Upload cancelled, send delete request
            data.close()
            response2 = requests.delete(upload_url)
            print("Upload cancelled by user.")
        # Close the file
        data.close()
        # Validate request response and parse
        if response.status_code != 201 and response.status_code != 200:
            print(response.text)
            response2 = requests.delete(upload_url)
            raise Exception(
                f"API Error {response.status_code}: could not upload file: {file_path}"
            )
        response_data = json.loads(response.text)
        item_id = response_data["id"]
        # Return the file item id
        return item_id
