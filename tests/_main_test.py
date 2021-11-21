"""Tests the helper functions primarily used to manage OneDrive instances using pytest."""
import json
import os
import re
from pathlib import Path

import httpx
import pytest

import graph_onedrive
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


class TestCreate:
    """Tests the create function."""

    def test_create(self, mock_graph_api, mock_auth_api):
        onedrive_instance = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        assert isinstance(onedrive_instance, OneDrive)

    @pytest.mark.parametrize(
        "client_id, client_secret, tenant, redirect_url, refresh_token, exp_msg",
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
                1.0,
                TENANT,
                REDIRECT,
                REFRESH_TOKEN,
                "client_secret expected 'str', got 'float'",
            ),
            (
                CLIENT_ID,
                CLIENT_SECRET,
                None,
                REDIRECT,
                REFRESH_TOKEN,
                "tenant expected 'str', got 'NoneType'",
            ),
            (
                CLIENT_ID,
                CLIENT_SECRET,
                TENANT,
                False,
                REFRESH_TOKEN,
                "redirect_url expected 'str', got 'bool'",
            ),
            (
                CLIENT_ID,
                CLIENT_SECRET,
                TENANT,
                REDIRECT,
                b"1",
                "refresh_token expected 'str', got 'bytes'",
            ),
        ],
    )
    def test_create_failure_type(
        self, client_id, client_secret, tenant, redirect_url, refresh_token, exp_msg
    ):
        with pytest.raises(TypeError) as excinfo:
            graph_onedrive.create(
                client_id=client_id,
                client_secret=client_secret,
                tenant=tenant,
                redirect_url=redirect_url,
                refresh_token=refresh_token,
            )
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestCreateFromFile:
    """Tests the create_from_config_file function."""

    @pytest.mark.parametrize(
        "redirect_url, refresh_token",
        [
            (REDIRECT, REFRESH_TOKEN),
            (False, REFRESH_TOKEN),
            (REDIRECT, False),
            (False, False),
        ],
    )
    @pytest.mark.filterwarnings("ignore:GraphAPIWarn")
    def test_create_from_file(
        self,
        tmp_path,
        monkeypatch,
        mock_graph_api,
        mock_auth_api,
        redirect_url,
        refresh_token,
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
        config_path = Path(temp_dir, "config.json")
        with open(config_path, "w") as fw:
            json.dump(config, fw)
        # If no refresh token provided then monkeypatch the auth input
        if not refresh_token:
            input_url = REDIRECT + "?code=" + AUTH_CODE
            monkeypatch.setattr("builtins.input", lambda _: input_url)
        # Run the test
        onedrive_instance = graph_onedrive.create_from_config_file(
            config_path, config_key
        )
        assert isinstance(onedrive_instance, OneDrive)

    @pytest.mark.parametrize(
        "config_path, config_key, exp_msg",
        [
            (123, None, "config_path expected 'str' or 'Path', got 'int'"),
            ("str", 4.1, "config_key expected 'str', got 'float'"),
        ],
    )
    def test_create_failure_type(self, config_path, config_key, exp_msg):
        with pytest.raises(TypeError) as excinfo:
            graph_onedrive.create_from_config_file(config_path, config_key)
        (msg,) = excinfo.value.args
        assert msg == exp_msg

    @pytest.mark.parametrize(
        "config_key_input, config, exp_msg",
        [
            (
                "bad-key",
                {"tenant_id": "blah"},
                "Config Error : Config dict key 'bad-key' incorrect",
            ),
            (
                "onedrive",
                {"tenant_id": "blah"},
                "Config Error : Config not in acceptable format",
            ),
        ],
    )
    def test_create_failure_key(self, tmp_path, config_key_input, config, exp_msg):
        # Make a temporary config file
        config = {"onedrive": config}
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, "config.json")
        with open(config_path, "w") as fw:
            json.dump(config, fw)
        # Run the test
        with pytest.raises(KeyError) as excinfo:
            graph_onedrive.create_from_config_file(config_path, config_key_input)
        (msg,) = excinfo.value.args
        assert msg == exp_msg


class TestSaveConfig:
    """Tests the save_to_config_file function."""

    @pytest.mark.parametrize(
        "config_key",
        [None, "onedrive", "my random key"],
    )
    def test_save_to_config_file(self, onedrive, tmp_path, config_key):
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, f"config-{config_key}.json")
        # Run the test
        if config_key:
            graph_onedrive.save_to_config_file(onedrive, config_path, config_key)
        else:
            graph_onedrive.save_to_config_file(onedrive, config_path)
        assert os.path.isfile(config_path)
        with open(config_path) as fr:
            config = json.load(fr)
        if config_key is None:
            config_key = "onedrive"
        assert config_key in config
        assert config[config_key]["tenant_id"] == onedrive._tenant_id
        assert config[config_key]["client_id"] == onedrive._client_id
        assert config[config_key]["client_secret_value"] == onedrive._client_secret
        assert config[config_key]["redirect_url"] == onedrive._redirect
        assert config[config_key]["refresh_token"] == onedrive.refresh_token

    def test_save_to_config_file_existing(self, onedrive, tmp_path):
        # Create an existing json file
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, "config.json")
        with open(config_path, "w") as fw:
            json.dump({"other": 100}, fw)
        # Run the test
        config_key = "new_config"
        graph_onedrive.save_to_config_file(onedrive, config_path, config_key)
        with open(config_path) as fr:
            config = json.load(fr)
        assert config_key in config
        assert config["other"] == 100

    @pytest.mark.parametrize(
        "onedrive_instance, config_path, config_key, exp_msg",
        [
            (
                None,
                "str",
                "str",
                "onedrive_instance expected 'OneDrive', got 'NoneType'",
            ),
            (
                "swap_real",
                123,
                "str",
                "config_path expected 'str' or 'Path', got 'int'",
            ),
            ("swap_real", "str", 4.1, "config_key expected 'str', got 'float'"),
        ],
    )
    def test_save_to_config_file_failure_type(
        self, onedrive, onedrive_instance, config_path, config_key, exp_msg
    ):
        if onedrive_instance == "swap_real":
            onedrive_instance = onedrive
        with pytest.raises(TypeError) as excinfo:
            graph_onedrive.save_to_config_file(
                onedrive_instance, config_path, config_key
            )
        (msg,) = excinfo.value.args
        assert msg == exp_msg
