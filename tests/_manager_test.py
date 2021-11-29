"""Tests the OneDrive context manager using pytest."""
import json
from pathlib import Path

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


class TestManager:
    """Tests the context manager."""

    @pytest.mark.parametrize(
        "redirect_url, refresh_token",
        [
            (REDIRECT, REFRESH_TOKEN),
            (False, REFRESH_TOKEN),
            (REDIRECT, False),
            (False, False),
        ],
    )
    def test_manager(
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
        with graph_onedrive.OneDriveManager(config_path) as onedrive:
            assert isinstance(onedrive, OneDrive)

    @pytest.mark.parametrize(
        "config_path, config_key, exp_msg",
        [
            (123, None, "config_path expected 'str' or 'Path', got 'int'"),
            ("str", 4.1, "config_key expected 'str', got 'float'"),
        ],
    )
    def test_manager_failure_type(self, config_path, config_key, exp_msg):
        with pytest.raises(TypeError) as excinfo:
            with graph_onedrive.OneDriveManager(config_path, config_key) as onedrive:
                pass
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
                {"tenant_id": "blah"},
                "expected client_id in first level of dictionary",
            ),
        ],
    )
    def test_manager_failure_key(self, tmp_path, config_key_input, config, exp_msg):
        # Make a temporary config file
        config = {"onedrive": config}
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, "config.json")
        with open(config_path, "w") as fw:
            json.dump(config, fw)
        # Run the test
        with pytest.raises(KeyError) as excinfo:
            with graph_onedrive.OneDriveManager(
                config_path, config_key_input
            ) as onedrive:
                pass
        (msg,) = excinfo.value.args
        assert msg == exp_msg
