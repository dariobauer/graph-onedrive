"""Sets-up and tears-down configuration used for testing."""
import json
from os import path

import pytest
import respx
from httpx import Response


# Get the absolute file path of the tests directory by locating this file
TESTS_DIR = path.dirname(path.abspath(__file__))

# Set the variables used to create the OneDrive instances in tests
REFRESH_TOKEN = ACCESS_TOKEN = "123"


def mock_response_json(key):
    """Read a json file and return values for given keys."""

    mocked_responses_path = path.join(TESTS_DIR, "mock_responses.json")

    with open(mocked_responses_path) as file:
        mocked_data = json.load(file)

    # Return the value if it exists, or an empty dict otherwise
    return mocked_data.get(key, {})


@pytest.fixture(scope="module")
def mock_graph_api():
    """Mock the Graph api for testing."""

    api_url = "https://graph.microsoft.com/v1.0/"
    headers = {"Accept": "*/*", "Authorization": "Bearer " + ACCESS_TOKEN}

    with respx.mock(base_url=api_url) as respx_mock:

        # Drive details
        drive_details_route = respx_mock.get(
            "me/drive/", headers=headers, name="get_drive_details"
        )
        drive_details_json = mock_response_json("drive-details")
        drive_details_route.return_value = Response(200, json=drive_details_json)

        # List directory
        list_dir_route = respx_mock.get(
            path__regex=r"me/drive/(root|items/[0-9a-zA-Z-]+)/children$",
            headers=headers,
            name="list_directory",
        )
        list_dir_json = mock_response_json("list-directory")
        list_dir_route.return_value = Response(200, json=list_dir_json)

        # Item details file - note item id has to start with 1 for test
        item_detail_file_route = respx_mock.get(
            path__regex=r"me/drive/items/1[0-9a-zA-Z-]+$",
            headers=headers,
            name="detail_item-file",
        )
        file_details_json = mock_response_json("item-details-file")
        item_detail_file_route.return_value = Response(200, json=file_details_json)

        # Item details folder - note item id has to start with 2 for test
        item_detail_folder_route = respx_mock.get(
            path__regex=r"me/drive/items/2[0-9a-zA-Z-]+$",
            headers=headers,
            name="detail_item-folder",
        )
        folder_details_json = mock_response_json("item-details-folder")
        item_detail_folder_route.return_value = Response(200, json=folder_details_json)

        # Make folder
        # To-do: create a side effect to take the body and return an appropriate response.
        make_folder_body = {
            "name": "tesy 1",
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename",
        }
        make_folder_route = respx_mock.post(
            path__regex=r"me/drive/(root|items/[0-9a-zA-Z-]+)/children$",
            headers=headers,
            name="make_folder",
            json=make_folder_body,
        )
        make_folder_json = mock_response_json("create-folder")
        make_folder_route.return_value = Response(201, json=make_folder_json)

        # Yield response to allow for teardown
        yield respx_mock


@pytest.fixture(scope="module")
def mock_auth_api():
    """Mock the Identity Platform api for testing."""

    auth_base_url = "https://login.microsoftonline.com/"

    with respx.mock(base_url=auth_base_url) as respx_mock:

        # Token
        token_route = respx_mock.post(
            path__regex=r"([0-9a-zA-Z-]+)/oauth2/v2.0/token$", name="get_tokens"
        )
        token_json = {
            "access_token": ACCESS_TOKEN,
            "refresh_token": REFRESH_TOKEN,
            "expires_in": 60,
        }
        token_route.return_value = Response(200, json=token_json)

        # Yield response to allow for teardown
        yield respx_mock
