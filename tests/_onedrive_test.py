"""Tests the OneDrive class using pytest."""
import json
import logging
import os
import re
from pathlib import Path

import httpx
import pytest
import yaml

from .conftest import ACCESS_TOKEN
from .conftest import AUTH_CODE
from .conftest import CLIENT_ID
from .conftest import CLIENT_SECRET
from .conftest import REDIRECT
from .conftest import REFRESH_TOKEN
from .conftest import SCOPE
from .conftest import TENANT
from .conftest import TESTS_DIR
from graph_onedrive._onedrive import GraphAPIError
from graph_onedrive._onedrive import OneDrive


class TestDunders:
    """Tests the instance double under methods."""

    # __init__
    @pytest.mark.parametrize(
        "refresh_token",
        [REFRESH_TOKEN, None],
    )
    def test_init(self, mock_graph_api, mock_auth_api, monkeypatch, refresh_token):
        # monkeypatch the Authorization step when no refresh token provided
        input_url = REDIRECT + "?code=" + AUTH_CODE
        monkeypatch.setattr("builtins.input", lambda _: input_url)
        # make the request
        assert OneDrive(CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, refresh_token)

    @pytest.mark.parametrize(
        "client_id, client_secret, tenant, redirect, refresh_token, exp_msg",
        [
            (
                123,
                CLIENT_SECRET,
                TENANT,
                REDIRECT,
                REFRESH_TOKEN,
                "client_id expected 'str', got 'int'",
            ),
            (
                CLIENT_ID,
                4.5,
                TENANT,
                REDIRECT,
                REFRESH_TOKEN,
                "client_secret expected 'str', got 'float'",
            ),
            (
                CLIENT_ID,
                CLIENT_SECRET,
                {},
                REDIRECT,
                REFRESH_TOKEN,
                "tenant expected 'str', got 'dict'",
            ),
            (
                CLIENT_ID,
                CLIENT_SECRET,
                TENANT,
                b"https://",
                REFRESH_TOKEN,
                "redirect_url expected 'str', got 'bytes'",
            ),
            (
                CLIENT_ID,
                CLIENT_SECRET,
                TENANT,
                REDIRECT,
                99,
                "refresh_token expected 'str', got 'int'",
            ),
        ],
    )
    def test_init_failure_type(
        self,
        mock_graph_api,
        mock_auth_api,
        client_id,
        client_secret,
        tenant,
        redirect,
        refresh_token,
        exp_msg,
    ):
        with pytest.raises(TypeError) as excinfo:
            OneDrive(client_id, client_secret, tenant, redirect, refresh_token)
        (msg,) = excinfo.value.args
        assert msg == exp_msg

    # __repr__
    def test_repr(self, onedrive):
        assert (
            repr(onedrive)
            == f"<OneDrive {onedrive._drive_type} {onedrive._drive_name} {onedrive._owner_name}>"
        )


class TestConstructors:
    """Tests the from_dict, from_file, from_json, from_yaml methods."""

    @pytest.mark.parametrize(
        "redirect_url, refresh_token, save_back, file_ext",
        [
            (REDIRECT, REFRESH_TOKEN, False, "json"),
            (False, REFRESH_TOKEN, True, "json"),
            (REDIRECT, False, True, "json"),
            (False, False, True, "json"),
            (REDIRECT, REFRESH_TOKEN, False, "yaml"),
            (False, REFRESH_TOKEN, True, "yaml"),
            (REDIRECT, False, True, "yaml"),
            (False, False, True, "yaml"),
        ],
    )
    def test_from_file(
        self,
        tmp_path,
        monkeypatch,
        mock_graph_api,
        mock_auth_api,
        redirect_url,
        refresh_token,
        save_back,
        file_ext,
    ):
        # Make a temporary config file
        config_key = "onedrive"
        config = {
            config_key: {
                "tenant_id": TENANT,
                "client_id": CLIENT_ID,
                "client_secret_value": CLIENT_SECRET,
            }
        }
        if redirect_url:
            config[config_key]["redirect_url"] = redirect_url
        if refresh_token:
            config[config_key]["refresh_token"] = refresh_token
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, f"config.{file_ext}")
        with open(config_path, "w") as fw:
            if file_ext == "json":
                json.dump(config, fw)
            elif file_ext == "yaml":
                yaml.safe_dump(config, fw)
            else:
                raise NotImplementedError("testing extension not implemented")
        # If no refresh token provided then monkeypatch the auth input
        if not refresh_token:
            input_url = REDIRECT + "?code=" + AUTH_CODE
            monkeypatch.setattr("builtins.input", lambda _: input_url)
        # Run the test
        onedrive_instance = OneDrive.from_file(
            config_path, config_key, save_refresh_token=save_back
        )
        assert isinstance(onedrive_instance, OneDrive)

    @pytest.mark.parametrize(
        "config_path, config_key, exp_msg",
        [
            (123, None, "config_path expected 'str' or 'Path', got 'int'"),
            ("str", 4.1, "config_key expected 'str', got 'float'"),
        ],
    )
    def test_from_file_failure_type(self, config_path, config_key, exp_msg):
        with pytest.raises(TypeError) as excinfo:
            OneDrive.from_file(config_path, config_key)
        (msg,) = excinfo.value.args
        assert msg == exp_msg

    @pytest.mark.parametrize(
        "config_key_input, config, exp_msg",
        [
            (
                "bad-key",
                {"tenant_id": "blah"},
                "config_key 'bad-key' not found in 'config.json'",
            ),
            (
                "onedrive",
                {"tenant_id": "blah", "client_secret_value": "test"},
                "expected client_id in first level of dictionary",
            ),
            (
                "onedrive",
                {"client_id": "blah", "client_secret_value": "test"},
                "expected tenant_id in first level of dictionary",
            ),
            (
                "onedrive",
                {"client_id": "blah", "tenant_id": "blah"},
                "expected client_secret_value in first level of dictionary",
            ),
        ],
    )
    def test_from_file_failure_key(self, tmp_path, config_key_input, config, exp_msg):
        # Make a temporary config file
        config = {"onedrive": config}
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, "config.json")
        with open(config_path, "w") as fw:
            json.dump(config, fw)
        # Run the test
        with pytest.raises(KeyError) as excinfo:
            OneDrive.from_file(config_path, config_key_input)
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestDeconstructors:
    """Tests the to_file, to_json, to_yaml methods."""

    @pytest.mark.parametrize(
        "config_key, file_ext",
        [
            (None, "json"),
            ("onedrive", "json"),
            ("my random key", "json"),
            (None, "yaml"),
            ("onedrive", "yaml"),
            ("my random key", "yaml"),
        ],
    )
    def test_to_file(self, onedrive, tmp_path, config_key, file_ext):
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, f"config-{config_key}.{file_ext}")
        # Run the test
        if config_key:
            onedrive.to_file(config_path, config_key)
        else:
            onedrive.to_file(config_path)
        assert os.path.isfile(config_path)
        with open(config_path) as fr:
            if file_ext == "json":
                config = json.load(fr)
            elif file_ext == "yaml":
                config = yaml.safe_load(fr)
            else:
                config = {}
        if config_key is None:
            config_key = "onedrive"
        assert config_key in config
        assert config[config_key]["tenant_id"] == onedrive._tenant_id
        assert config[config_key]["client_id"] == onedrive._client_id
        assert config[config_key]["client_secret_value"] == onedrive._client_secret
        assert config[config_key]["redirect_url"] == onedrive._redirect
        assert config[config_key]["refresh_token"] == onedrive.refresh_token

    def test_to_file_existing(self, onedrive, tmp_path):
        # Create an existing json file
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, "config.json")
        with open(config_path, "w") as fw:
            json.dump({"other": 100}, fw)
        # Run the test
        config_key = "new_config"
        onedrive.to_file(config_path, config_key)
        with open(config_path) as fr:
            config = json.load(fr)
        assert config_key in config
        assert config["other"] == 100

    @pytest.mark.parametrize(
        "config_path, config_key, exp_msg",
        [
            (
                123,
                "str",
                "file_path expected 'str' or 'Path', got 'int'",
            ),
            ("str", 4.1, "config_key expected 'str', got 'float'"),
        ],
    )
    def test_to_file_failure_type(self, onedrive, config_path, config_key, exp_msg):
        with pytest.raises(TypeError) as excinfo:
            onedrive.to_file(config_path, config_key)
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestResponseChecks:
    """Tests the _raise_unexpected_response method."""

    @pytest.mark.parametrize(
        "resp_code, check_code, message, has_json",
        [
            (200, 200, "", False),
            (400, [302, 400], "123", False),
            (500, ["blah", 500], "just a string", True),
        ],
    )
    def test_raise_unexpected_response(
        self, onedrive, resp_code, check_code, message, has_json
    ):
        response = httpx.Response(status_code=resp_code, json={"content": "nothing"})
        onedrive._raise_unexpected_response(
            response, check_code, message, has_json=has_json
        )
        assert True

    @pytest.mark.parametrize(
        "resp_code, resp_json, check_code, message, has_json, exp_msg",
        [
            (
                200,
                {"no": "content"},
                201,
                "just a test",
                False,
                "just a test (no error message returned)",
            ),
            (
                204,
                None,
                204,
                "test 123",
                True,
                "test 123 (response did not contain json)",
            ),
            (
                400,
                {"error": {"message": "Invalid request"}},
                204,
                "could not delete link",
                True,
                "could not delete link (Invalid request)",
            ),
            (
                500,
                {"error_description": "Unauthorized"},
                201,
                "could not get headers",
                True,
                "could not get headers (Unauthorized)",
            ),
        ],
    )
    def test_raise_unexpected_response_failure(
        self, onedrive, resp_code, check_code, message, resp_json, has_json, exp_msg
    ):
        response = httpx.Response(status_code=resp_code, json=resp_json)
        with pytest.raises(GraphAPIError) as excinfo:
            onedrive._raise_unexpected_response(
                response, check_code, message, has_json=has_json
            )
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestGetTokens:
    """Tests the _get_token method."""

    def test_get_tokens_using_auth_code(self, temp_onedrive, monkeypatch):
        # monkeypatch the response url typically input by user
        input_url = REDIRECT + "?code=" + AUTH_CODE
        monkeypatch.setattr("builtins.input", lambda _: input_url)
        # set the refresh token as empty
        temp_onedrive.refresh_token = ""
        # make the request
        temp_onedrive._get_token()
        assert temp_onedrive.refresh_token == REFRESH_TOKEN
        assert temp_onedrive._access_token == ACCESS_TOKEN

    def test_get_tokens_using_refresh_token(self, temp_onedrive):
        temp_onedrive._get_token()
        assert temp_onedrive.refresh_token == REFRESH_TOKEN
        assert temp_onedrive._access_token == ACCESS_TOKEN

    def test_get_token_failure_bad_request_token(self, temp_onedrive):
        temp_onedrive.refresh_token = "badtoken"
        with pytest.raises(GraphAPIError) as excinfo:
            temp_onedrive._get_token()
        (msg,) = excinfo.value.args
        assert msg == "could not get access token (Invalid request)"

    def test_get_token_failure_bad_return_access_token(
        self, temp_onedrive, mock_auth_api
    ):
        mock_auth_api.routes["access_token"].snapshot()
        mock_auth_api.routes["access_token"].side_effect = None
        mock_auth_api.routes["access_token"].return_value = httpx.Response(
            200, json={"access_token": None, "refresh_token": REFRESH_TOKEN}
        )
        with pytest.raises(GraphAPIError) as excinfo:
            temp_onedrive._get_token()
        (msg,) = excinfo.value.args
        assert msg == "response did not return an access token"
        mock_auth_api.routes["access_token"].rollback()

    def test_get_token_failure_bad_return_refresh_token(
        self, temp_onedrive, mock_auth_api, caplog
    ):
        mock_auth_api.routes["access_token"].snapshot()
        mock_auth_api.routes["access_token"].side_effect = None
        mock_auth_api.routes["access_token"].return_value = httpx.Response(
            200, json={"access_token": ACCESS_TOKEN, "refresh_token": None}
        )
        with caplog.at_level(logging.WARNING, logger="graph_onedrive"):
            temp_onedrive._get_token()
        assert len(caplog.records) == 1
        assert (
            str(caplog.records[0].message)
            == "token request did not return a refresh token, existing config not updated"
        )
        # old refresh token should still be set
        assert temp_onedrive.refresh_token == REFRESH_TOKEN
        mock_auth_api.routes["access_token"].rollback()

    def test_get_token_failure_unknown(self, temp_onedrive, mock_auth_api):
        mock_auth_api.routes["access_token"].snapshot()
        mock_auth_api.routes["access_token"].side_effect = None
        mock_auth_api.routes["access_token"].return_value = httpx.Response(400)
        with pytest.raises(GraphAPIError) as excinfo:
            temp_onedrive._get_token()
        (msg,) = excinfo.value.args
        assert msg == "could not get access token (no error message returned)"
        mock_auth_api.routes["access_token"].rollback()


class TestAuthorization:
    """Tests the _get_authorization method."""

    def test_get_authorization(self, temp_onedrive, monkeypatch):
        # monkeypatch the response url typically input by user
        input_url = REDIRECT + "?code=" + AUTH_CODE
        monkeypatch.setattr("builtins.input", lambda _: input_url)
        # make the request
        auth_code = temp_onedrive._get_authorization()
        assert auth_code == AUTH_CODE

    @pytest.mark.parametrize(
        "input_url, exp_msg",
        [
            (
                REDIRECT + "?code=&123&state=nomatch",
                "response 'state' not for this request, occurs when reusing an old authorization url",
            ),
            (REDIRECT + "?code=&", "response did not contain an authorization code"),
            (
                REDIRECT + "?code=123&state=blah",
                "response 'state' not for this request, occurs when reusing an old authorization url",
            ),
        ],
    )
    def test_get_authorization_failure(
        self, temp_onedrive, monkeypatch, input_url, exp_msg
    ):
        # monkeypatch the response url typically input by user
        monkeypatch.setattr("builtins.input", lambda _: input_url)
        # make the request
        with pytest.raises(GraphAPIError) as excinfo:
            temp_onedrive._get_authorization()
        (msg,) = excinfo.value.args
        assert msg == exp_msg

    def test_get_authorization_warn(self, temp_onedrive, monkeypatch, caplog):
        # monkeypatch the response url typically input by user
        input_url = REDIRECT + "?code=" + AUTH_CODE
        monkeypatch.setattr("builtins.input", lambda _: input_url)
        # make the request
        with caplog.at_level(logging.WARNING, logger="graph_onedrive"):
            auth_code = temp_onedrive._get_authorization()
        assert len(caplog.records) == 1
        assert (
            str(caplog.records[0].message)
            == "response 'state' was not in returned url, response not confirmed"
        )
        assert auth_code == AUTH_CODE


class TestHeaders:
    """Tests the _create_headers method."""

    def test_create_headers(self, temp_onedrive):
        temp_onedrive._headers = {}
        temp_onedrive._create_headers()
        exp_headers = {"Accept": "*/*", "Authorization": "Bearer " + ACCESS_TOKEN}
        assert temp_onedrive._headers == exp_headers

    def test_create_headers_failure_value(self, temp_onedrive):
        temp_onedrive._headers = {}
        temp_onedrive._access_token = ""
        with pytest.raises(ValueError) as excinfo:
            temp_onedrive._create_headers()
        (msg,) = excinfo.value.args
        assert msg == "expected self._access_token to be set, got empty string"


class TestDriveDetails:
    """Tests the _get_drive_details, get_usage methods."""

    # get_drive_details
    def test_get_drive_details(self, onedrive):
        onedrive._get_drive_details()
        assert (
            onedrive._drive_id
            == "b!-RIj2DuyvEyV1T4NlOaMHk8XkS_I8MdFlUCq1BlcjgmhRfAj3-Z8RY2VpuvV_tpd"
        )
        assert onedrive._drive_name == "OneDrive"
        assert onedrive._drive_type == "business"
        assert onedrive._owner_id == "48d31887-5fad-4d73-a9f5-3c356e68a038"
        assert onedrive._owner_email == "MeganB@M365x214355.onmicrosoft.com"
        assert onedrive._owner_name == "Megan Bowen"
        assert onedrive._quota_used == 106330475
        assert onedrive._quota_remaining == 1099217263127
        assert onedrive._quota_total == 1099511627776

    @pytest.mark.parametrize(
        "json_returned, exp_msg",
        [
            (
                {"error": {"code": "invalidRequest", "message": "Invalid request"}},
                "could not get drive details (Invalid request)",
            ),
            (None, "could not get drive details (no error message returned)"),
        ],
    )
    def test_get_drive_details_failure(
        self, temp_onedrive, mock_graph_api, json_returned, exp_msg
    ):
        mock_graph_api.routes["drive_details"].snapshot()
        mock_graph_api.routes["drive_details"].side_effect = None
        mock_graph_api.routes["drive_details"].return_value = httpx.Response(
            400, json=json_returned
        )
        with pytest.raises(GraphAPIError) as excinfo:
            temp_onedrive._get_drive_details()
        (msg,) = excinfo.value.args
        assert msg == exp_msg
        mock_graph_api.routes["drive_details"].rollback()

    # get_usage
    @pytest.mark.parametrize(
        "unit, exp_used, exp_capacity, exp_unit",
        [
            ("b", 106330475, 1099511627776, "b"),
            ("kb", 103838.4, 1073741824, "kb"),
            ("MB", 101.4, 1048576, "mb"),
            ("gb", 0.1, 1024, "gb"),
            (None, 0.1, 1024, "gb"),
        ],
    )
    def test_get_usage(self, onedrive, unit, exp_used, exp_capacity, exp_unit):
        if unit == None:
            used, capacity, unit = onedrive.get_usage(refresh=True)
        else:
            used, capacity, unit = onedrive.get_usage(unit=unit)
        assert round(used, 1) == round(exp_used, 1)
        assert round(capacity, 1) == round(exp_capacity, 1)
        assert unit == exp_unit

    def test_get_usage_verbose(self, onedrive, capsys):
        onedrive.get_usage(verbose=True)
        stdout, sterr = capsys.readouterr()
        assert stdout == "Using 0.1 gb (0.01%) of total 1024.0 gb.\n"

    def test_get_usage_failure_value(self, onedrive):
        with pytest.raises(ValueError) as excinfo:
            onedrive.get_usage(unit="TB")
        (msg,) = excinfo.value.args
        assert msg == "'tb' is not a supported unit"

    @pytest.mark.parametrize(
        "unit, exp_msg",
        [
            (1, "unit expected 'str', got 'int'"),
            (None, "unit expected 'str', got 'NoneType'"),
        ],
    )
    def test_get_usage_failure_type(self, onedrive, unit, exp_msg):
        with pytest.raises(TypeError) as excinfo:
            onedrive.get_usage(unit=unit)
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestListingDirectories:
    """Tests the list_directory method."""

    def test_list_directory_root(self, onedrive):
        items = onedrive.list_directory()
        assert items[0].get("id") == "01BYE5RZ6QN3ZWBTUFOFD3GSPGOHDJD36K"

    def test_list_directory_folder(self, onedrive):
        item_id = "01BYE5RZYFPM65IDVARFELFLNTXR4ZKABD"
        items = onedrive.list_directory(item_id)
        assert items[0].get("id") == "01BYE5RZZWSN2ASHUEBJH2XJJ25WSEBUJ3"

    @pytest.mark.skip(reason="not implemented")
    def test_list_directory_failure(self, onedrive):
        ...

    def test_list_directory_failure_type(self, onedrive):
        with pytest.raises(TypeError) as excinfo:
            onedrive.list_directory(123)
        (msg,) = excinfo.value.args
        assert msg == "folder_id expected 'str', got 'int'"


class TestSearch:
    """Tests the search method."""

    @pytest.mark.parametrize(
        "query, top, exp_len",
        [
            ("Contoso", 4, 4),
            ("Sales", 200, 6),
            ("does not exist", 150, 0),
        ],
    )
    def test_search(self, onedrive, query, top, exp_len):
        items = onedrive.search(query, top=top)
        assert len(items) == exp_len

    @pytest.mark.skip(reason="not implemented")
    def test_search_failure(self, onedrive):
        ...

    @pytest.mark.parametrize(
        "query, top, exp_msg",
        [
            (123, 4, "query expected 'str', got 'int'"),
            ("123", 4.0, "top expected 'int', got 'float'"),
        ],
    )
    def test_search_failure_type(self, onedrive, query, top, exp_msg):
        with pytest.raises(TypeError) as excinfo:
            onedrive.search(query, top)
        (msg,) = excinfo.value.args
        assert msg == exp_msg

    @pytest.mark.parametrize(
        "query",
        [
            "",
            " ",
            "%20",
        ],
    )
    def test_search_failure_value(self, onedrive, query):
        with pytest.raises(ValueError) as excinfo:
            onedrive.search(query)
        (msg,) = excinfo.value.args
        assert (
            msg
            == "cannot search for blank string. Did you mean list_directory(folder_id=None)?"
        )


class TestItemDetails:
    """Tests the detail_item, item_type, is_folder, is_file methods."""

    # detail_item
    @pytest.mark.parametrize(
        "item_id, exp_name",
        [
            ("01BYE5RZ2XXKUBPDYT7JGLPHYXALBIXKEL", "Contoso Patent Template.docx"),
            ("01BYE5RZ6TAJHXA5GMWZB2HDLD7SNEXFFU", "CR-227 Project"),
        ],
    )
    def test_detail_item(self, onedrive, item_id, exp_name):
        item_details = onedrive.detail_item(item_id)
        assert item_details.get("name") == exp_name

    @pytest.mark.parametrize(
        "item_id, exp_stout",
        [
            (
                "01BYE5RZ2XXKUBPDYT7JGLPHYXALBIXKEL",
                "item id: 01BYE5RZ2XXKUBPDYT7JGLPHYXALBIXKEL\n"
                "name: Contoso Patent Template.docx\n"
                "type: file\n"
                "created: 2017-08-07T16:03:47Z by: Megan Bowen\n"
                "last modified: 2017-08-10T17:06:12Z by: Megan Bowen\n"
                "size: 85596\n"
                "web url: https://m365x214355-my.sharepoint.com/personal/meganb_m365x214355_onmicrosoft_com/_layouts/15/Doc.aspx?sourcedoc=%7B17A8BA57-138F-4CFA-B79F-1702C28BA88B%7D&file=Contoso%20Patent%20Template.docx&action=default&mobileredirect=true\n"
                "file system created: 2017-08-07T16:03:47Z\n"
                "file system last modified: 2017-08-10T17:06:12Z\n"
                "file quickXor hash: jWK86kNVvULlV/oFKuGvDKybt+I=\n",
            ),
            (
                "01BYE5RZ6TAJHXA5GMWZB2HDLD7SNEXFFU",
                "item id: 01BYE5RZ6TAJHXA5GMWZB2HDLD7SNEXFFU\n"
                "name: CR-227 Project\n"
                "type: folder\n"
                "created: 2017-08-07T16:17:40Z by: Megan Bowen\n"
                "last modified: 2017-08-07T16:17:40Z by: Megan Bowen\n"
                "size: 6934759\n"
                "web url: https://m365x214355-my.sharepoint.com/personal/meganb_m365x214355_onmicrosoft_com/Documents/CR-227%20Project\n"
                "file system created: 2017-08-07T16:17:40Z\n"
                "file system last modified: 2017-08-07T16:17:40Z\n"
                "child count: 5\n",
            ),
        ],
    )
    def test_detail_item_verbose(self, onedrive, capsys, item_id, exp_stout):
        item_details = onedrive.detail_item(item_id, verbose=True)
        stdout, sterr = capsys.readouterr()
        assert stdout == exp_stout

    @pytest.mark.skip(reason="not implemented")
    def test_detail_item_failure(self):
        ...

    # detail_item_path
    def test_detail_item_path(self, onedrive):
        item_path = "Contoso Electronics/Contoso Electronics Sales Presentation.pptx"
        item_details = onedrive.detail_item_path(item_path)
        assert item_details.get("name") == "Contoso Electronics Sales Presentation.pptx"

    # item_type
    @pytest.mark.parametrize(
        "item_id, exp_type",
        [
            ("01BYE5RZ6KU4MREZDFEVGKWRBC7OK4ET3J", "file"),
            ("01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P", "folder"),
        ],
    )
    def test_item_type(self, onedrive, item_id, exp_type):
        item_type = onedrive.item_type(item_id)
        assert item_type == exp_type

    @pytest.mark.skip(reason="not implemented")
    def test_item_type_failure(self):
        ...

    # is_folder
    @pytest.mark.parametrize(
        "item_id, exp_bool",
        [
            ("01BYE5RZ6KU4MREZDFEVGKWRBC7OK4ET3J", False),
            ("01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P", True),
        ],
    )
    def test_is_folder(self, onedrive, item_id, exp_bool):
        is_folder = onedrive.is_folder(item_id)
        assert is_folder == exp_bool

    @pytest.mark.skip(reason="not implemented")
    def test_is_folder_failure(self):
        ...

    # is_file
    @pytest.mark.parametrize(
        "item_id, exp_bool",
        [
            ("01BYE5RZ6KU4MREZDFEVGKWRBC7OK4ET3J", True),
            ("01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P", False),
        ],
    )
    def test_is_file(self, onedrive, item_id, exp_bool):
        is_file = onedrive.is_file(item_id)
        assert is_file == exp_bool

    @pytest.mark.skip(reason="not implemented")
    def test_is_file_failure(self):
        ...


class TestSharingLink:
    """Tests the create_share_link method."""

    @pytest.mark.parametrize(
        "item_id, link_type, password, expiration, scope, exp_link",
        [
            (
                "01BYE5RZ6KU4MREZDFEVGKWRBC7OK4ET3J",
                "view",
                None,
                None,
                "anonymous",
                "https://onedrive.com/fakelink",
            ),
            (
                "01BYE5RZ6KU4MREZDFEVGKWRBC7OK4ET3J",
                "edit",
                None,
                None,
                "anonymous",
                "https://onedrive.com/fakelink",
            ),
            (
                "01BYE5RZ6KU4MREZDFEVGKWRBC7OK4ET3J",
                "edit",
                None,
                None,
                "organization",
                "https://onedrive.com/fakelink",
            ),
            (
                "01BYE5RZ6KU4MREZDFEVGKWRBC7OK4ET3J",
                "view",
                None,
                None,
                "anonymous",
                "https://onedrive.com/fakelink",
            ),
            (
                "01BYE5RZ6KU4MREZDFEVGKWRBC7OK4ET3J",
                "edit",
                None,
                None,
                "anonymous",
                "https://onedrive.com/fakelink",
            ),
            (
                "01BYE5RZ6KU4MREZDFEVGKWRBC7OK4ET3J",
                "edit",
                None,
                None,
                "organization",
                "https://onedrive.com/fakelink",
            ),
            (
                "01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P",
                "edit",
                None,
                None,
                "organization",
                "https://onedrive.com/fakelink",
            ),
        ],
    )
    def test_create_share_link(
        self, onedrive, item_id, link_type, password, expiration, scope, exp_link
    ):
        link = onedrive.create_share_link(
            item_id, link_type, password, expiration, scope
        )
        assert link == exp_link

    @pytest.mark.parametrize(
        "item_id, link_type, password, expiration, scope, exp_msg",
        [
            (
                "999",
                "view",
                None,
                None,
                "anonymous",
                "share link could not be created (Invalid request)",
            ),
        ],
    )
    def test_create_share_link_failure_graph(
        self, onedrive, item_id, link_type, password, expiration, scope, exp_msg
    ):
        with pytest.raises(GraphAPIError) as excinfo:
            onedrive.create_share_link(item_id, link_type, password, expiration, scope)
        (msg,) = excinfo.value.args
        assert msg == exp_msg

    @pytest.mark.parametrize(
        "item_id, link_type, password, expiration, scope, exp_msg",
        [
            (
                "999",
                {"view"},
                None,
                None,
                "anonymous",
                "link_type expected 'str', got 'set'",
            ),
        ],
    )
    def test_create_share_link_failure_type(
        self, onedrive, item_id, link_type, password, expiration, scope, exp_msg
    ):
        with pytest.raises(TypeError) as excinfo:
            onedrive.create_share_link(item_id, link_type, password, expiration, scope)
        (msg,) = excinfo.value.args
        assert msg == exp_msg

    @pytest.mark.parametrize(
        "item_id, link_type, password, expiration, scope, exp_msg",
        [
            (
                "999",
                "view ",
                None,
                None,
                "anonymous",
                "link_type expected 'view', 'edit', or 'embed', got 'view '",
            ),
            (
                "999",
                "embed",
                None,
                None,
                "anonymous",
                "link_type='embed' is not available for business OneDrive accounts",
            ),
            (
                "999",
                "view",
                "password",
                None,
                "anonymous",
                "password is not available for business OneDrive accounts",
            ),
        ],
    )
    def test_create_share_link_failure_value(
        self, onedrive, item_id, link_type, password, expiration, scope, exp_msg
    ):
        with pytest.raises(ValueError) as excinfo:
            onedrive.create_share_link(item_id, link_type, password, expiration, scope)
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestMakeFolder:
    """Tests the make_folder method."""

    @pytest.mark.parametrize(
        "folder_name, parent_folder_id, check_existing, exp_str",
        [
            ("tesy 1", "01BYE5RZ4CPC5XBOTZCFD2CT7SZFNICEYC", True, "ACEA49D1-144"),
            ("tesy 1", "01BYE5RZ4CPC5XBOTZCFD2CT7SZFNICEYC", False, "ACEA49D1-144"),
            ("tesy 1", None, True, "ACEA49D1-144"),
            ("tesy 1", None, False, "ACEA49D1-144")
            # To-do: allow for other folder names by using a side effect in the mock route
        ],
    )
    def test_make_folder(
        self, onedrive, folder_name, parent_folder_id, check_existing, exp_str
    ):
        item_id = onedrive.make_folder(folder_name, parent_folder_id, check_existing)
        assert item_id == exp_str

    @pytest.mark.skip(reason="not implemented")
    def test_make_folder_failure(self):
        ...


class TestMove:
    """Tests the move_item method."""

    @pytest.mark.parametrize(
        "item_id, new_folder_id, new_name",
        [
            (
                "01BYE5RZ53CPZEMSJFTZDJ6AEFVZP3C3BG",
                "01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P",
                "new-item-name.txt",
            ),
            (
                "01BYE5RZ53CPZEMSJFTZDJ6AEFVZP3C3BG",
                "01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P",
                None,
            ),
        ],
    )
    def test_move_item(self, onedrive, item_id, new_folder_id, new_name):
        returned_item_id, folder_id = onedrive.move_item(
            item_id, new_folder_id, new_name
        )
        assert returned_item_id == item_id
        assert folder_id == new_folder_id

    @pytest.mark.parametrize(
        "item_id, new_folder_id",
        [
            ("123", "01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P"),
            ("01BYE5RZ53CPZEMSJFTZDJ6AEFVZP3C3BG", "456"),
        ],
    )
    def test_move_item_failure(self, onedrive, item_id, new_folder_id):
        with pytest.raises(GraphAPIError) as excinfo:
            onedrive.move_item(item_id, new_folder_id)
        (msg,) = excinfo.value.args
        assert msg == "item not moved (Invalid request)"

    @pytest.mark.parametrize(
        "item_id, new_folder_id, new_name, exp_msg",
        [
            (123, "new_folder_id", None, "item_id expected 'str', got 'int'"),
            ("item_id", None, None, "new_folder_id expected 'str', got 'NoneType'"),
            (
                "item_id",
                "new_folder_id",
                b"name",
                "new_name expected 'str', got 'bytes'",
            ),
        ],
    )
    def test_move_item_failure_type(
        self, onedrive, item_id, new_folder_id, new_name, exp_msg
    ):
        with pytest.raises(TypeError) as excinfo:
            onedrive.move_item(item_id, new_folder_id, new_name)
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestCopy:
    """Tests the copy_item method."""

    @pytest.mark.parametrize(
        "new_name, confirm_complete, exp_return",
        [
            ("new-item-name.txt", True, "01MOWKYVJML57KN2ANMBA3JZJS2MBGC7KM"),
            ("new-item-name.txt", False, None),
            (None, True, "01MOWKYVJML57KN2ANMBA3JZJS2MBGC7KM"),
        ],
    )
    def test_copy_item(self, onedrive, new_name, confirm_complete, exp_return):
        item_id = "01BYE5RZ53CPZEMSJFTZDJ6AEFVZP3C3BG"
        new_folder_id = "01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P"
        returned_item_id = onedrive.copy_item(
            item_id, new_folder_id, new_name, confirm_complete
        )
        assert returned_item_id != item_id
        assert returned_item_id != new_folder_id
        assert returned_item_id == exp_return

    @pytest.mark.parametrize(
        "confirm_complete, exp_return, exp_stdout",
        [
            (
                True,
                "01MOWKYVJML57KN2ANMBA3JZJS2MBGC7KM",
                "Copy request sent.\nWaiting 1s before checking progress\nPercentage complete = 96.7%\nWaiting 1s before checking progress\nCopy confirmed complete.\n",
            ),
            (False, None, "Copy request sent.\n"),
        ],
    )
    def test_copy_item_verbose(
        self, onedrive, capsys, confirm_complete, exp_return, exp_stdout
    ):
        item_id = "01BYE5RZ53CPZEMSJFTZDJ6AEFVZP3C3BG"
        new_folder_id = "01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P"
        returned_item_id = onedrive.copy_item(
            item_id, new_folder_id, "new-item-name.txt", confirm_complete, True
        )
        assert returned_item_id == exp_return
        stdout, sterr = capsys.readouterr()
        # Note that the stout alternates between partically complete and complete bassed on call count
        # You may need to rerun all the tests if there is an issue to reset the call count
        assert stdout == exp_stdout

    @pytest.mark.parametrize(
        "item_id, new_folder_id",
        [
            ("123", "01BYE5RZ5YOS4CWLFWORAJ4U63SCA3JT5P"),
            ("01BYE5RZ53CPZEMSJFTZDJ6AEFVZP3C3BG", "456"),
        ],
    )
    def test_copy_item_failure(self, onedrive, item_id, new_folder_id):
        with pytest.raises(GraphAPIError) as excinfo:
            onedrive.copy_item(item_id, new_folder_id)
        (msg,) = excinfo.value.args
        assert msg == "item not copied (Invalid request)"

    @pytest.mark.parametrize(
        "item_id, new_folder_id, new_name, exp_msg",
        [
            (123, "new_folder_id", None, "item_id expected 'str', got 'int'"),
            ("item_id", None, None, "new_folder_id expected 'str', got 'NoneType'"),
            (
                "item_id",
                "new_folder_id",
                b"name",
                "new_name expected 'str', got 'bytes'",
            ),
        ],
    )
    def test_copy_item_failure_type(
        self, onedrive, item_id, new_folder_id, new_name, exp_msg
    ):
        with pytest.raises(TypeError) as excinfo:
            onedrive.copy_item(item_id, new_folder_id, new_name)
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestRename:
    """Tests the rename_item method."""

    def test_rename_item(self, onedrive):
        item_id = "01BYE5RZ53CPZEMSJFTZDJ6AEFVZP3C3BG"
        new_name = "new-item-name.txt"
        returned_name = onedrive.rename_item(item_id, new_name)
        assert returned_name == new_name

    @pytest.mark.skip(reason="not implemented")
    def test_rename_item_failure(self):
        ...


class TestDelete:
    """Tests the delete_item method."""

    def test_delete_item(self, onedrive):
        response = onedrive.delete_item(
            "01BYE5RZ53CPZEMSJFTZDJ6AEFVZP3C3BG", pre_confirm=True
        )
        assert isinstance(response, bool)
        assert response == True

    @pytest.mark.parametrize(
        "input_str, exp_bool",
        [("delete", True), ("DeLeTe ", True), ("D elete", False)],
    )
    def test_delete_item_manual_confirm(
        self, onedrive, monkeypatch, input_str, exp_bool
    ):
        monkeypatch.setattr("builtins.input", lambda _: input_str)
        response = onedrive.delete_item("01BYE5RZ53CPZEMSJFTZDJ6AEFVZP3C3BG")
        assert isinstance(response, bool)
        assert response == exp_bool

    def test_delete_item_failure(self, onedrive):
        with pytest.raises(GraphAPIError) as excinfo:
            onedrive.delete_item("999", pre_confirm=True)
        (msg,) = excinfo.value.args
        assert msg == "item not deleted (Invalid request)"

    @pytest.mark.parametrize(
        "item_id, pre_confirm, exp_msg",
        [
            (999, False, "item_id expected 'str', got 'int'"),
            ("999", "true", "pre_confirm expected 'bool', got 'str'"),
        ],
    )
    def test_delete_item_failure_type(self, onedrive, item_id, pre_confirm, exp_msg):
        with pytest.raises(TypeError) as excinfo:
            onedrive.delete_item(item_id, pre_confirm)
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestDownload:
    """Tests the download_file, _download_async, _download_async_part methods."""

    # download_file
    @pytest.mark.skip(reason="not implemented")
    def test_download_file(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    def test_download_file_failure(self):
        ...

    """# _download_async
    @pytest.mark.skip(reason="not implemented")
    async def test_download_async(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    async def test_download_async_failure(self):
        ...

    # _download_async_part
    @pytest.mark.skip(reason="not implemented")
    async def test_download_async_part(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    async def test_download_async_part_failure(self):
        ...
    """


class TestUpload:
    """Tests the upload_file, _upload_large_file methods."""

    # upload_file
    @pytest.mark.parametrize(
        "new_file_name, parent_folder_id, if_exists, size",
        [
            (None, None, "rename", 1024),
            (None, None, "fail", 1000),
            (None, None, "replace", 25446),
            ("hello hello_there-01", None, "rename", 87486),
            ("large_archive.zip", None, "rename", 5791757),
            ("my_movie.mov", "01BYE5RZ5MYLM2SMX75ZBIPQZIHT6OAYPB", "rename", 485),
        ],
    )
    def test_upload_file(
        self, onedrive, tmp_path, new_file_name, parent_folder_id, if_exists, size
    ):
        # Make a temporary file, at least one case should be larger than the upload chunk size (5MiB)
        temp_dir = Path(tmp_path, "temp_upload")
        temp_dir.mkdir()
        file_path = Path(temp_dir, "temp_file.txt")
        file_path.write_bytes(os.urandom(size))
        # Make the request
        item_id = onedrive.upload_file(
            file_path, new_file_name, parent_folder_id, if_exists
        )
        assert item_id == "91231001"

    def test_upload_file_verbose(self, onedrive, tmp_path, capsys):
        # Make a temporary file, at least one case should be larger than the upload chunk size (5MiB)
        temp_dir = Path(tmp_path, "temp_upload")
        temp_dir.mkdir()
        file_path = Path(temp_dir, "temp_file.txt")
        file_path.write_bytes(os.urandom(5791757))
        onedrive.upload_file(file_path, verbose=True)
        stdout, sterr = capsys.readouterr()
        assert (
            stdout == "Requesting upload session\n"
            "File temp_file.txt will be uploaded in 2 segments\n"
            "Loading file\n"
            "Uploading segment 1/2\n"
            "Uploading segment 2/2 (~50% complete)\n"
            "Upload complete\n"
        )

    def test_upload_file_failure(self, onedrive, tmp_path):
        # Make a temporary file, at least one case should be larger than the upload chunk size (5MiB)
        temp_dir = Path(tmp_path, "temp_upload")
        temp_dir.mkdir()
        file_path = Path(temp_dir, "temp_file.txt")
        file_path.write_bytes(os.urandom(100))
        with pytest.raises(GraphAPIError) as excinfo:
            onedrive.upload_file(file_path, parent_folder_id="not-valid-id")
        (msg,) = excinfo.value.args
        assert msg == "upload session could not be created (Invalid request)"

    @pytest.mark.parametrize(
        "file_path, new_file_name, parent_folder_id, exp_msg",
        [
            (123, "str", "str", "file_path expected 'str' or 'Path', got 'int'"),
            ("str", 4.0, "str", "new_file_name expected 'str', got 'float'"),
            ("str", "str", 123, "parent_folder_id expected 'str', got 'int'"),
        ],
    )
    def test_upload_file_failure_type(
        self, onedrive, file_path, new_file_name, parent_folder_id, exp_msg
    ):
        with pytest.raises(TypeError) as excinfo:
            onedrive.upload_file(file_path, new_file_name, parent_folder_id)
        (msg,) = excinfo.value.args
        assert msg == exp_msg

    def test_upload_file_failure_value(self, onedrive):
        with pytest.raises(ValueError) as excinfo:
            onedrive.upload_file("file_path", if_exists="delete")
        (msg,) = excinfo.value.args
        assert msg == "if_exists expected 'fail', 'replace', or 'rename', got 'delete'"

    def test_upload_file_failure_bad_path(self, onedrive):
        with pytest.raises(ValueError) as excinfo:
            onedrive.upload_file("non-existing")
        (msg,) = excinfo.value.args
        assert (
            msg == "file_path expected a path to an existing file, got 'non-existing'"
        )

    # _get_local_file_metadata
    def test_get_local_file_metadata(self, onedrive):
        file_path = os.path.join(TESTS_DIR, "__init__.py")
        (
            file_size,
            file_created_str,
            file_modified_str,
        ) = onedrive._get_local_file_metadata(file_path)
        assert file_size == 0
        timestamp_format = "^(?:20|19)[0-9]{2}-(?:0[0-9]|1[012])-(?:[0-2][0-9]|3[01])T(?:[01][0-9]|2[0-3])(?::[0-5][0-9]){2}Z$"
        assert re.search(timestamp_format, file_created_str)
        assert re.search(timestamp_format, file_modified_str)
        # These timestamp asserts are buggy on some platforms, take care if updating
        # assert file_created_str == "2021-11-07T06:46:23Z"
        # assert file_modified_str == "2021-11-07T06:46:23Z"

    def test_get_local_file_metadata_failure_type(self, onedrive):
        with pytest.raises(TypeError) as excinfo:
            onedrive._get_local_file_metadata(123)
        (msg,) = excinfo.value.args
        assert msg == "file_path expected 'str' or 'Path', got 'int'"

    def test_get_local_file_metadata_failure_bad_path(self, onedrive):
        with pytest.raises(ValueError) as excinfo:
            onedrive._get_local_file_metadata("non-existing-file")
        (msg,) = excinfo.value.args
        assert (
            msg
            == "file_path expected a path to an existing file, got 'non-existing-file'"
        )
