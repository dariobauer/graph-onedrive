"""Tests the config functions using pytest."""

import json
import sys
from pathlib import Path
from typing import Any
from typing import Dict
from unittest import mock

import pytest
import toml
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
from graph_onedrive._config import dump_config
from graph_onedrive._config import load_config


class TestLoad:
    """Tests the load_config function."""

    @pytest.mark.parametrize(
        "config_path, config_key",
        [
            ("config.json", "onedrive"),
            ("test.yaml", "test_2"),
            ("unknown.txt.toml", "one more test"),
        ],
    )
    def test_load_config(self, tmp_path, config_path, config_key):
        # Make a temporary config file
        config = {
            config_key: {
                "tenant_id": TENANT,
                "client_id": CLIENT_ID,
                "client_secret_value": CLIENT_SECRET,
                "redirect_url": REDIRECT,
                "refresh_token": REFRESH_TOKEN,
            }
        }
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, config_path)
        with open(config_path, "w") as fw:
            if str(config_path).endswith(".json"):
                json.dump(config, fw)
            elif str(config_path).endswith(".yaml"):
                yaml.safe_dump(config, fw)
            elif str(config_path).endswith(".toml"):
                toml.dump(config, fw)
        # Test load
        data = load_config(config_path, config_key)
        assert data == config[config_key]

    def test_load_config_raw(self, tmp_path):
        config_key = "onedrive"
        # Make a temporary config file
        config = {
            config_key: {
                "tenant_id": TENANT,
                "client_id": CLIENT_ID,
                "client_secret_value": CLIENT_SECRET,
                "redirect_url": REDIRECT,
                "refresh_token": REFRESH_TOKEN,
            },
            "other data": 1234,
        }
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, "raw.yaml")
        with open(config_path, "w") as fw:
            if str(config_path).endswith(".json"):
                json.dump(config, fw)
            elif str(config_path).endswith(".yaml"):
                yaml.safe_dump(config, fw)
            elif str(config_path).endswith(".toml"):
                toml.dump(config, fw)
        # Test load
        data = load_config(config_path)
        assert data == config

    def test_load_config_failure(self): ...


class TestDump:
    """Tests the dump_config function."""

    @pytest.mark.parametrize(
        "config_path",
        ["config.json", "test.yaml", "unknown.txt.toml"],
    )
    def test_dump_config(self, tmp_path, config_path):
        config_key: str = "onedrive"
        initial_file: dict[str, Any] = {
            config_key: {
                "tenant_id": TENANT,
                "client_id": CLIENT_ID,
                "client_secret_value": CLIENT_SECRET,
                "redirect_url": REDIRECT,
                "refresh_token": REFRESH_TOKEN,
            },
            "other data": 1234,
        }
        temp_dir = Path(tmp_path, "temp_config")
        temp_dir.mkdir()
        config_path = Path(temp_dir, config_path)
        with open(config_path, "w") as fw:
            if str(config_path).endswith(".json"):
                json.dump(initial_file, fw)
            elif str(config_path).endswith(".yaml"):
                yaml.safe_dump(initial_file, fw)
            elif str(config_path).endswith(".toml"):
                toml.dump(initial_file, fw)
        # Test load
        new_config = {
            "tenant_id": TENANT,
            "client_id": CLIENT_ID,
            "client_secret_value": CLIENT_SECRET,
            "redirect_url": REDIRECT,
            "refresh_token": "new",
        }
        dump_config(new_config, config_path, config_key)
        # Verify data
        with open(config_path) as fr:
            if str(config_path).endswith(".json"):
                read_data = json.load(fr)
            elif str(config_path).endswith(".yaml"):
                read_data = yaml.safe_load(fr)
            elif str(config_path).endswith(".toml"):
                read_data = toml.load(fr)
        initial_file[config_key]["refresh_token"] = "new"
        assert read_data == initial_file

    def test_dump_config_failure(self): ...
