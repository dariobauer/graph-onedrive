"""Configuration file related functions."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from typing import Optional

# Set logger
logger = logging.getLogger(__name__)

# import the PyYAML optional dependency
try:
    import yaml

    optionals_yaml = True
    logger.debug("yaml imported successfully, YAML config files supported")
except ImportError:
    optionals_yaml = False
    logger.debug("yaml could not be imported, YAML config files not supported")

# import the TOML optional dependency
try:
    import toml

    optionals_toml = True
    logger.debug("toml imported successfully, TOML config files supported")
except ImportError:
    optionals_toml = False
    logger.debug("toml could not be imported, TOML config files not supported")

# Create a tuple of acceptable config file extensions, typically used for str.endswith()
if optionals_yaml and optionals_toml:
    CONFIG_EXTS: tuple[str, ...] = (".json", ".yaml", ".toml")
elif optionals_yaml:
    CONFIG_EXTS = (".json", ".yaml")
elif optionals_toml:
    CONFIG_EXTS = (".json", ".toml")
else:
    CONFIG_EXTS = (".json",)


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
    # check the file type
    _check_file_type(config_path)

    # read the config file
    with open(config_path) as config_file:
        if str(config_path).endswith(".json"):
            logger.debug(f"loading {config_path} as a json file")
            config = json.load(config_file)
        elif str(config_path).endswith(".yaml"):
            logger.debug(f"loading {config_path} as a yaml file")
            config = yaml.safe_load(config_file)
        elif str(config_path).endswith(".toml"):
            logger.debug(f"loading {config_path} as a toml file")
            config = toml.load(config_file)
        else:
            raise NotImplementedError("config file type not supported")

    # return raw data if option set
    if config_key is None:
        logger.debug(f"returning the raw data without checking the contents")
        return config

    # return the configuration after checking that the config key
    try:
        return config[config_key]
    except KeyError:
        raise KeyError(
            f"config_key '{config_key}' not found in '{Path(config_path).name}'"
        )


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
    with open(config_path, "w") as config_file:
        if str(config_path).endswith(".json"):
            logger.debug(f"dumping data to {config_path} as a json file")
            json.dump(main_config, config_file, indent=4)
        elif str(config_path).endswith(".yaml"):
            logger.debug(f"dumping data to {config_path} as a yaml file")
            yaml.safe_dump(main_config, config_file)
        elif str(config_path).endswith(".toml"):
            logger.debug(f"dumping data to {config_path} as a toml file")
            toml.dump(main_config, config_file)
        else:
            raise NotImplementedError("config file type not supported")


def _check_file_type(
    file_path: str | Path, accepted_formats: tuple[str, ...] = CONFIG_EXTS
) -> bool:
    """INTERNAL: Checks a file extension type compared to a tuple of acceptable types.
    Positional arguments:
        file_path (str|Path) -- a path to a file
    Keyword arguments:
        accepted_formats (tuple) -- tuple of acceptable file extensions (default = (".json", ".yaml", ".toml"))
    Returns:
        (bool) -- True if acceptable, otherwise raises TypeError
    """
    # Return true if the file has an acceptable extension
    if str(file_path).endswith(accepted_formats):
        return True

    # Raise TypeErrors but provide hints for toml and yaml files
    if str(file_path).endswith(".yaml"):
        raise TypeError(
            f"file path was to yaml file but PyYAML is not installed, Hint: 'pip install pyyaml'"
        )
    elif str(file_path).endswith(".toml"):
        raise TypeError(
            f"file path was to toml file but TOML is not installed, Hint: 'pip install toml'"
        )
    else:
        raise TypeError(
            f"file path must have {' or '.join([i for i in accepted_formats])} extension"
        )
