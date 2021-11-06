"""Sets-up and tears-down configuration used for testing."""
import json
import os
import re

import httpx
import pytest
import respx

import graph_onedrive


# Set the variables used to create the OneDrive instances in tests
# Warning: certain tests require these to match the assertions in the tests
CLIENT_ID = CLIENT_SECRET = "abc"
REFRESH_TOKEN = "123"
ACCESS_TOKEN = "123"
TENANT = "test"
SCOPE = "offline_access files.readwrite"
REDIRECT = "http://localhost:8080"

# Get the absolute file path of the tests directory by locating this file
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Read mocked response content
with open(os.path.join(TESTS_DIR, "mock_responses.json")) as file:
    MOCKED_RESPONSE_DATA = json.load(file)

# Read mocked item content
with open(os.path.join(TESTS_DIR, "mock_items.json")) as file:
    MOCKED_ITEMS = json.load(file)["items"]


@pytest.fixture(scope="module")
def mock_graph_api():
    """Mock the Graph api for testing."""

    # Set the api expected route host and header
    api_url = "https://graph.microsoft.com/v1.0/"
    headers = {"Accept": "*/*", "Authorization": "Bearer " + ACCESS_TOKEN}

    # Create the mocked routes
    with respx.mock(base_url=api_url) as respx_mock:

        # Drive details
        drive_details_route = respx_mock.get(
            path="me/drive/", headers=headers, name="get_drive_details"
        ).mock(side_effect=side_effect_drive_details)

        # Make folder
        make_folder_route = respx_mock.post(
            path__regex=r"me/drive/(root|items/[0-9a-zA-Z-]+)/children$",
            headers=headers,
            json__folder={},
            name="make_folder",
        ).mock(side_effect=side_effect_make_folder)

        # List directory
        list_directory_route = respx_mock.get(
            path__regex=r"me/drive/(root|items/[0-9a-zA-Z-]+)/children$",
            headers=headers,
            name="list_directory",
        ).mock(side_effect=side_effect_list_dir)

        # Detail item
        detail_item_route = respx_mock.get(
            path__regex=r"me/drive/items/[0-9a-zA-Z-]+$",
            headers=headers,
            name="detail_item",
        ).mock(side_effect=side_effect_detail_item)

        # Move Item
        # Copy Item
        # Rename Item
        # Delete Item
        # Download File
        # Upload File

        yield respx_mock


def side_effect_drive_details(request):
    response_json = MOCKED_RESPONSE_DATA.get("drive-details")
    return httpx.Response(200, json=response_json)


def side_effect_list_dir(request):
    # If a parent folder is specfied, check it exists
    if "root" not in request.url.path:
        folder_id_re = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
        if folder_id_re:
            folder_id = folder_id_re.group(1)
        matching_item_list = [
            item
            for item in MOCKED_ITEMS
            if (item.get("id") == folder_id and "folder" in item)
        ]
        if not matching_item_list:
            error = {"error": {"message": "folder does not exist"}}
            return httpx.Response(400, json=error)
    # Prepare and return the response
    response_json = MOCKED_RESPONSE_DATA.get("list-directory")
    return httpx.Response(200, json=response_json)


def side_effect_detail_item(request):
    item_id_re = re.search("items/([0-9a-zA-Z-]+)", request.url.path)
    if item_id_re:
        item_id = item_id_re.group(1)
    matching_item_list = [item for item in MOCKED_ITEMS if item.get("id") == item_id]
    if not matching_item_list:
        error = {"error": {"message": "item not found"}}
        return httpx.Response(400, json=error)
    response_json = matching_item_list[0]
    return httpx.Response(200, json=response_json)


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
        error = {"error": {"message": "invalid request"}}
        return httpx.Response(400, json=error)
    # Check the conflict behaviour
    conflict_behaviour = body.get("@microsoft.graph.conflictBehavior", "rename")
    if conflict_behaviour not in ("fail", "replace", "rename"):
        error = {"error": {"message": "invalid conflict behaviour"}}
        return httpx.Response(400, json=error)
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
                    error = {"error": {"message": "item conflicts"}}
                    return httpx.Response(400, json=error)
                else:
                    new_folder_name += "-1"
        # Check parent exists
        if parent_id and parent_id == item["id"]:
            if "folder" in item:
                parent_id_valid = True
            else:
                error = {"error": {"message": "parent item id is not a folder"}}
                return httpx.Response(400, json=error)
    if "root" not in request.url.path and not parent_id_valid:
        error = {"error": {"message": "parent item does not exist"}}
        return httpx.Response(400, json=error)
    # Prepare and return the response
    response_json = MOCKED_RESPONSE_DATA.get("create-folder")
    response_json["name"] = new_folder_name
    return httpx.Response(201, json=response_json)


@pytest.fixture(scope="module")
def mock_auth_api():
    """Mock the Identity Platform api for testing."""

    # Set the auth rul
    auth_base_url = "https://login.microsoftonline.com/"

    with respx.mock(base_url=auth_base_url) as respx_mock:

        # Authorization Code - not currently used as instance created with refresh token
        """authorization_route = respx_mock.post(
            path__regex=r"([0-9a-zA-Z-]+)/oauth2/v2.0/token$",
            json__grant_type="authorization_code",
            name="access_using_authorization_code",
        ).mock(side_effect=side_effect_access_using_authorization_code)"""

        # Refresh Token
        refresh_route = respx_mock.post(
            path__regex=r"([0-9a-zA-Z-]+)/oauth2/v2.0/token$",
            json__grant_type="refresh_token",
            name="access_using_refresh_token",
        ).mock(side_effect=side_effect_access_using_refresh_token)

        yield respx_mock


def side_effect_access_using_refresh_token(request):
    body = json.loads(request.content)
    if body.get("refresh_token") != REFRESH_TOKEN:
        error = {"error": {"message": "invalid request"}}
        return httpx.Response(400, json=error)
    response_json = {
        "access_token": ACCESS_TOKEN,
        "refresh_token": REFRESH_TOKEN,
        "expires_in": 100,
    }
    return httpx.Response(200, json=response_json)


def side_effect_access_using_authorization_code(request):
    body = json.loads(request.content)
    if (
        body.get("client_id") != CLIENT_ID
        or body.get("client_secret") != CLIENT_SECRET
        or body.get("scope") != SCOPE
        or body.get("redirect_uri") != REDIRECT
        or body.get("code") is None  # To-do: check the code
    ):
        error = {"error": {"message": "invalid request"}}
        return httpx.Response(400, json=error)
    response_json = {
        "access_token": ACCESS_TOKEN,
        "refresh_token": REFRESH_TOKEN,
        "expires_in": 60,
    }
    return httpx.Response(200, json=response_json)


@pytest.fixture(scope="module")
def onedrive(mock_graph_api, mock_auth_api):
    onedrive = graph_onedrive.create(
        CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
    )
    yield onedrive
