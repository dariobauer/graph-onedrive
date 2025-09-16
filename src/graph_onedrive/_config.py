"""Configuration file related functions."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Optional, IO

# Set logger
logger = logging.getLogger(__name__)

# Define type aliases for loader and dumper functions
_load_toml: Callable[[IO[Any]], Any] | None = None
_dump_toml: Callable[[Any, IO[str]], object] | None = None
_load_yaml: Callable[[IO[bytes]], Any] | None = None
_dump_yaml: Callable[[Any, IO[str]], None] | None = None

# try to import PyYAML
try:
    import yaml

    _load_yaml = lambda f: yaml.safe_load(f)
    _dump_yaml = lambda obj, fp: yaml.safe_dump(obj, fp)
    logger.debug("yaml imported successfully, YAML config files supported")
except ImportError:
    _load_yaml = None
    _dump_yaml = None
    logger.debug("yaml could not be imported, YAML config files not supported")

# try to import a toml packages to read and write toml files
# default: no dumper
_dump_toml = None

# Try tomllib (read only, Python 3.11+)
try:
    import tomllib

    _load_toml = lambda f: tomllib.load(f)
    logger.debug(
        "tomllib imported successfully, reading of TOML config files supported"
    )
except ImportError:
    try:
        import tomli

        _load_toml = lambda f: tomli.load(f)
        logger.debug(
            "tomli imported successfully, reading of TOML config files supported"
        )
    except ImportError:
        _load_toml = None

# Try toml (read/write)
try:
    import toml

    if _load_toml is None:
        _load_toml = lambda f: toml.load(f)
    _dump_toml = lambda obj, fp: toml.dump(obj, fp)
    logger.debug(
        "toml imported successfully, reading and writing of TOML config files supported"
    )
except ImportError:
    pass

# Try tomli_w (write only)
if _dump_toml is None:
    try:
        import tomli_w

        _dump_toml = lambda obj, fp: fp.write(tomli_w.dumps(obj))
        logger.debug(
            "tomli_w imported successfully, writing of TOML config files supported"
        )
    except ImportError:
        pass

# Try tomlkit (read/write)
if _dump_toml is None or _load_toml is None:
    try:
        import tomlkit

        if _load_toml is None:
            _load_toml = lambda f: tomlkit.parse(f.read())
            logger.debug(
                "tomlkit imported successfully, reading of TOML config files supported"
            )
        if _dump_toml is None:
            _dump_toml = lambda obj, fp: fp.write(tomlkit.dumps(obj))
            logger.debug(
                "tomlkit imported successfully, writing of TOML config files supported"
            )
    except ImportError:
        logger.debug("toml files are either not at all, or not fully supported")


def load_config(
    config_path: str | Path, config_key: str | None = None
) -> dict[str, Any]:
    """INTERNAL: Loads a config dictionary object from a file.
    Positional arguments:
        config_path (str|Path) -- path to configuration file
        config_key (str) -- key of the item storing the configuration (default = None)
    Returns:
        config (dict) -- returns the decoded dictionary contents
    """
    # convert to a Path object
    config_path = Path(config_path)

    # check that the file exists
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # check the file type
    suffix = config_path.suffix.lower()

    # read the config file
    with config_path.open("rb") as config_file:
        if suffix in (".json",):
            logger.debug(f"loading {config_path} as a json file")
            config = json.load(config_file)
        elif suffix in (".yaml", ".yml"):
            if _load_yaml is None:
                raise ImportError(
                    "PyYAML is required to parse YAML files. Install with `pip install pyyaml`."
                )
            logger.debug(f"loading {config_path} as a yaml file")
            config = _load_yaml(config_file)
        elif suffix in (".toml",):
            if _load_toml is None:
                raise ImportError(
                    "No TOML parser available. Install one of: Python >=3.11 (tomllib), tomli, or toml."
                )
            logger.debug(f"loading {config_path} as a toml file")
            config = _load_toml(config_file)
        else:
            raise NotImplementedError(f"Unsupported config format: {suffix}")

    # return raw data if option set
    if config_key is None:
        logger.debug(f"returning the raw data without checking the contents")
        return config

    # return the configuration after checking that the config key
    try:
        return config[config_key]
    except KeyError:
        raise KeyError(f"config_key '{config_key}' not found in '{config_path.name}'")


def dump_config(
    config: dict[str, str], config_path: str | Path, config_key: str
) -> None:
    """INTERNAL: Dumps a config dictionary object to a file.
    Positional arguments:
        config (dict) -- dictionary of key value pairs
        config_path (str|Path) -- path to configuration file
        config_key (str) -- key of the item storing the configuration
    """
    # Load existing file
    try:
        main_config = load_config(config_path)
        logger.debug(f"{config_path} file already exists, data loaded")
    except FileNotFoundError:
        main_config = {}
        logger.debug(f"{config_path} does not yet exist, new file will be created")

    # Update values
    main_config.update({config_key: config})

    # Dump to file
    suffix = Path(config_path).suffix.lower()
    with open(config_path, "w", encoding="utf-8") as config_file:
        if suffix in (".json",):
            logger.debug(f"dumping data to {config_path} as a json file")
            json.dump(main_config, config_file, indent=4)
        elif suffix in (".yaml", ".yml"):
            if _dump_yaml is None:
                raise ImportError(
                    "PyYAML is required to write YAML files. Install with `pip install pyyaml`."
                )
            logger.debug(f"dumping data to {config_path} as a yaml file")
            _dump_yaml(main_config, config_file)
        elif suffix in (".toml",):
            if _dump_toml is None:
                raise ImportError(
                    "No TOML writer available. Install the 'toml' package with `pip install toml`."
                )
            logger.debug(f"dumping data to {config_path} as a toml file")
            _dump_toml(main_config, config_file)
        else:
            raise NotImplementedError(f"Unsupported config file type: {suffix}")
