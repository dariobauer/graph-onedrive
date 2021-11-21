"""Sets-up and tears-down configuration used for testing."""
import json
import os
import re
import urllib.parse
import warnings
from typing import List
from typing import Tuple

import httpx
import pytest
import respx

import graph_onedrive


# Set the variables used to create the OneDrive instances in tests
# Warning: certain tests require these to match the assertions in the tests
CLIENT_ID = "1a2B3"
CLIENT_SECRET = "4c5D6"
AUTH_CODE = "7e8F9"
REFRESH_TOKEN = "10g11H"
ACCESS_TOKEN = "12i13J"
TENANT = "test"
SCOPE = "offline_access files.readwrite"
REDIRECT = "http://localhost:8080"

# Get the absolute file path of the tests directory by locating this file
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Read mocked response content
with open(os.path.join(TESTS_DIR, "mock_responses.json")) as file:
    MOCKED_RESPONSE_DATA = json.load(file)
MOCKED_ITEMS = MOCKED_RESPONSE_DATA["list-root"]["value"]


@pytest.fixture(scope="module")
def mock_graph_api():
    """Mock the Graph api for testing."""

    # Set the api expected route host and header
    api_url = "https://graph.microsoft.com/v1.0/"
    headers = {"Accept": "*/*", "Authorization": "Bearer " + ACCESS_TOKEN}

    # Create the mocked routes
    # IMPORTANT: routes ordered by most specific top as respx it will use first match
    with respx.mock(base_url=api_url, assert_all_called=False) as respx_mock:

        # Make folder
        make_folder_route = respx_mock.post(
            path__regex=r"me/drive/(?:root|items/[0-9a-zA-Z-]+)/children$",
            headers=headers,
            json__folder={},
            name="make_folder",
        ).mock(side_effect=side_effect_make_folder)

        # List directory
        list_directory_route = respx_mock.get(
            path__regex=r"me/drive/(?:root|items/[0-9a-zA-Z-]+)/children$",
            headers=headers,
            name="list_directory",
        ).mock(side_effect=side_effect_list_dir)

        # Sharing Link
        share_link_route = respx_mock.post(
            path__regex=r"me/drive/items/[0-9a-zA-Z-]+/createLink$",
            headers=headers,
            name="create_share_link",
        ).mock(side_effect=side_effect_sharing_link)

        # Patch Item - Move, Rename
        patch_item_route = respx_mock.patch(
            path__regex=r"me/drive/items/[0-9a-zA-Z-]+$",
            headers=headers,
            name="patch_item",
        ).mock(side_effect=side_effect_patch_item)

        # Copy Item
        copy_item_route = respx_mock.post(
            path__regex=r"me/drive/items/[0-9a-zA-Z-]+/copy$",
            headers=headers,
            name="copy_item",
        ).mock(side_effect=side_effect_copy_item)
        # note monitor route is in non base url context manager

        # Copy Item Monitor
        # host specified as not using base_url
        copy_item_monitor_route = respx_mock.get(
            host__regex=r"[0-9a-zA-Z-]+.sharepoint.com",
            path__regex=r"/_api/v2.0/monitor/[0-9a-zA-Z-]+$",
            name="copy_item_monitor",
        ).mock(side_effect=side_effect_copy_item_monitor)

        # Delete Item
        delete_item_route = respx_mock.delete(
            path__regex=r"me/drive/items/[0-9a-zA-Z-]+$",
            headers=headers,
            name="delete_item",
        ).mock(side_effect=side_effect_delete_item)

        # Download File

        # Upload File Session
        # Note this doesn't match non-standard characters as encoding is decoded by respx
        upload_session_route = respx_mock.post(
            path__regex=r"me/drive/(?:root|items/[0-9a-zA-Z-]+):/[0-9a-zA-Z-_.%+ ]+:/createUploadSession$",
            headers=headers,
            name="upload_session",
        ).mock(side_effect=side_effect_upload_session)

        # Upload File Delete Session
        # host specified as not using base_url
        upload_session_delete_route = respx_mock.delete(
            host__regex=r"[0-9a-zA-Z-]+.up.1drv.com",
            path__regex=r"/up/[0-9a-zA-Z]+$",
            name="delete_upload_session",
        ).mock(return_value=httpx.Response(204))

        # Upload File
        # host specified as not using base_url
        upload_item_route = respx_mock.put(
            host__regex=r"[0-9a-zA-Z-]+.up.1drv.com",
            path__regex=r"/up/[0-9a-zA-Z]+$",
            name="upload_item",
        ).mock(side_effect=side_effect_upload_item)

        # Detail item
        detail_item_route = respx_mock.get(
            path__regex=r"me/drive/items/[0-9a-zA-Z-]+$",
            headers=headers,
            name="detail_item",
        ).mock(side_effect=side_effect_detail_item)

        # Drive details
        drive_details_route = respx_mock.get(
            path="me/drive/", headers=headers, name="drive_details"
        ).mock(side_effect=side_effect_drive_details)

        yield respx_mock


def side_effect_detail_item(request):
    item_id_match = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
    if not item_id_match:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Check if the item id provided corresponds to an item in the mocked items list (root only)
    matching_item_list = [
        item for item in MOCKED_ITEMS if item.get("id") == item_id_match.group(1)
    ]
    if not matching_item_list:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    return httpx.Response(200, json=matching_item_list[0])


def side_effect_drive_details(request):
    return httpx.Response(200, json=MOCKED_RESPONSE_DATA["drive-details"])


def side_effect_list_dir(request):
    # return early if root
    if "root" in request.url.path:
        return httpx.Response(200, json=MOCKED_RESPONSE_DATA["list-root"])
    # Extract the item id
    item_id_match = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
    if not item_id_match:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Check if the item id provided corresponds to an item in the mocked items list (root only)
    matching_item_list = [
        item for item in MOCKED_ITEMS if (item.get("id") == item_id_match.group(1))
    ]
    if not matching_item_list:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    elif "folder" not in matching_item_list[0]:
        # If item is not a folder then return an empty list of children
        return httpx.Response(200, json=MOCKED_RESPONSE_DATA["list-directory-empty"])
    # Prepare and return the response
    return httpx.Response(200, json=MOCKED_RESPONSE_DATA["list-directory"])


def side_effect_make_folder(request):
    # Get the parent folder
    if "root" in request.url.path:
        parent_id = None
    else:
        parent_id_re = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
        if parent_id_re:
            parent_id = parent_id_re.group(1)
    # Load the body
    try:
        body = json.loads(request.content)
        new_folder_name = body["name"]
    except:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Check the conflict behaviour
    conflict_behaviour = body.get("@microsoft.graph.conflictBehavior", "rename")
    if conflict_behaviour not in ("fail", "replace", "rename"):
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Load mocked items from file and loop through them
    mocked_items = MOCKED_ITEMS
    parent_id_valid = False
    for item in mocked_items:
        # Check new folder does not conflict
        if (
            "folder" in item
            and conflict_behaviour != "replace"
            and item["name"] == new_folder_name
        ):
            if (parent_id and item["parentReference"]["id"] == parent_id) or (
                parent_id is None and item["parentReference"]["path"] == "/drive/root:"
            ):
                if conflict_behaviour == "fail":
                    return httpx.Response(
                        400, json=MOCKED_RESPONSE_DATA["invalid-request"]
                    )
                else:
                    new_folder_name += "-1"
        # Check parent exists
        if parent_id and parent_id == item["id"]:
            if "folder" in item:
                parent_id_valid = True
            else:
                return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    if "root" not in request.url.path and not parent_id_valid:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Prepare and return the response
    response_json = MOCKED_RESPONSE_DATA["create-folder"]
    response_json["name"] = new_folder_name
    return httpx.Response(201, json=response_json)


def side_effect_sharing_link(request):
    item_id_re = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
    if item_id_re:
        item_id = item_id_re.group(1)
    # Load the body
    try:
        body = json.loads(request.content)
        link_type = body["type"]
        scope = body["scope"]
    except:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    password = body.get("password")
    expiration = body.get("expirationDateTime")
    matching_item_list = [item for item in MOCKED_ITEMS if item.get("id") == item_id]
    if not matching_item_list:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    response_json = {"link": {"webUrl": "https://onedrive.com/fakelink"}}
    if link_type == "embed":
        response_json["link"]["webHtml"] = "<iframe>...</iframe>"
    return httpx.Response(201, json=response_json)


def side_effect_patch_item(request):
    # If a parent folder is specfied, check it exists
    item_id_re = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
    if item_id_re:
        matching_item_list = [
            item for item in MOCKED_ITEMS if item.get("id") == item_id_re.group(1)
        ]
        if not matching_item_list:
            return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Load the body
    try:
        body = json.loads(request.content)
    except:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Prepare and return the response
    response_json = MOCKED_RESPONSE_DATA["patch-item"]
    new_folder_id = body.get("parentReference", {}).get("id")
    if new_folder_id:
        if not [
            item
            for item in MOCKED_ITEMS
            if item.get("id") == new_folder_id and "folder" in item
        ]:
            return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
        response_json["parentReference"]["id"] = new_folder_id
    new_name = body.get("name")
    if new_name:
        response_json["name"] = new_name
    return httpx.Response(200, json=response_json)


def side_effect_copy_item(request):
    # If a parent folder is specfied, check it exists
    item_id_re = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
    if item_id_re:
        item_id = item_id_re.group(1)
        matching_item_list = [
            item for item in MOCKED_ITEMS if item.get("id") == item_id
        ]
    else:
        matching_item_list = []
    if not matching_item_list:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Load the body
    try:
        body = json.loads(request.content)
        new_folder_id = body["parentReference"]["id"]
        new_name = body.get("name")
    except Exception:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    if not [
        item
        for item in MOCKED_ITEMS
        if item.get("id") == new_folder_id and "folder" in item
    ]:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Return the monitor url
    headers = {
        "Location": "https://m365x214355-my.sharepoint.com/_api/v2.0/monitor/4A3407B5-88FC-4504-8B21-0AABD3412717"
    }
    return httpx.Response(202, headers=headers)


def side_effect_copy_item_monitor(request, route):
    # If this is the first call return progress otherwise return the finished response
    if (route.call_count + 1) % 2 == 0:
        return httpx.Response(202, json=MOCKED_RESPONSE_DATA["copy-item-progress"])
    else:
        return httpx.Response(202, json=MOCKED_RESPONSE_DATA["copy-item-complete"])


def side_effect_delete_item(request):
    # Check item exists
    item_id_re = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
    if not item_id_re or not [
        item for item in MOCKED_ITEMS if item.get("id") == item_id_re.group(1)
    ]:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    return httpx.Response(204)


def side_effect_upload_session(request):
    # If a parent folder is specfied, check it exists
    parent_id_re = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
    if parent_id_re:
        item_id = parent_id_re.group(1)
        matching_item_list = [
            item
            for item in MOCKED_ITEMS
            if item.get("id") == item_id and "folder" in item
        ]
        if not matching_item_list:
            return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Check the file name
    file_name_raw = re.search(
        ":/([0-9a-zA-Z-_.%+]+):/createUploadSession", str(request.url.raw_path)
    )
    if not file_name_raw:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Load and give the body a few simple checks
    if request.content:
        try:
            body = json.loads(request.content)["item"]
        except Exception:
            return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
        conflict_behaviour = body.get("@microsoft.graph.conflictBehavior", "rename")
        if conflict_behaviour not in ("rename", "replace", "fail"):
            return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
        if file_name_raw.group(1) != urllib.parse.quote(body.get("name")):
            return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Returns an upload url
    return httpx.Response(200, json=MOCKED_RESPONSE_DATA["upload-session"])


def side_effect_upload_item(request):
    # Load headers
    try:
        content_range = request.headers["Content-Range"]
        byte_re = re.search("^bytes ([0-9]+)-([0-9]+)/([0-9]+)$", content_range)
        if byte_re:
            content_range_start = int(byte_re.group(1))
            content_range_end = int(byte_re.group(2))
            file_size = int(byte_re.group(3))
    except Exception:
        return httpx.Response(400, json=MOCKED_RESPONSE_DATA["invalid-request"])
    if request.headers.get("Authorization"):
        return httpx.Response(401, json=MOCKED_RESPONSE_DATA["invalid-request"])
    if (
        content_range_start >= content_range_end
        or content_range_start >= file_size
        or content_range_end >= file_size
    ):
        return httpx.Response(416, json=MOCKED_RESPONSE_DATA["invalid-request"])
    # Check if this is the last chunk
    if content_range_end != (file_size - 1):
        response_json = {
            "expirationDateTime": "2015-01-29T09:21:55.523Z",
            "nextExpectedRanges": [f"{content_range_end+1}-"],
        }
        return httpx.Response(202, json=response_json)
    # Upload finished
    return httpx.Response(201, json=MOCKED_RESPONSE_DATA["upload-complete"])


@pytest.fixture(scope="module")
def mock_auth_api():
    """Mock the Identity Platform api for testing."""

    # Set the auth rul
    auth_base_url = "https://login.microsoftonline.com/"

    with respx.mock(base_url=auth_base_url) as respx_mock:

        # Authorization Code and Refresh Token
        token_route = respx_mock.post(
            path__regex=r"[0-9a-zA-Z-]+/oauth2/v2.0/token$",
            name="access_token",
        ).mock(side_effect=side_effect_access_token)

        yield respx_mock


def side_effect_access_token(request):
    # Parse and decode the request content, typed to help mypy
    body_encoded: List[Tuple[bytes, bytes]] = urllib.parse.parse_qsl(request.content)
    body = {key.decode(): value.decode() for (key, value) in body_encoded}
    # Check the content is as expected
    grant_type = body["grant_type"]
    error = {"error_description": "Invalid request"}
    if grant_type not in ("authorization_code", "refresh_token"):
        return httpx.Response(400, json=error)
    elif (
        body["client_id"] != CLIENT_ID
        or body["client_secret"] != CLIENT_SECRET
        or body["scope"] != SCOPE
        or body["redirect_uri"] != REDIRECT
    ):
        return httpx.Response(400, json=error)
    elif grant_type == "refresh_token":
        if (
            body.get("refresh_token") is None
            or body.get("refresh_token") != REFRESH_TOKEN
        ):
            return httpx.Response(400, json=error)
    elif grant_type == "authorization_code":
        if body.get("code") is None or body.get("code") != AUTH_CODE:
            return httpx.Response(400, json=error)
    # Return the tokens
    response_json = {
        "access_token": ACCESS_TOKEN,
        "refresh_token": REFRESH_TOKEN,
        "expires_in": 100,
    }
    return httpx.Response(200, json=response_json)


@pytest.fixture(scope="module")
def onedrive(mock_graph_api, mock_auth_api):
    """Creates a OneDrive instance, scope for whole module so is shared for efficiency.
    Use temp_onedrive instead if intending to edit the instance attributes."""
    onedrive = graph_onedrive.create(
        CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
    )
    yield onedrive


@pytest.fixture(scope="function")
def temp_onedrive(mock_graph_api, mock_auth_api):
    """Creates a OneDrive instance, scope limited to the function, so can be negatively altered."""
    onedrive = graph_onedrive.create(
        CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
    )
    yield onedrive
