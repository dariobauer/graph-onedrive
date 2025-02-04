"""OneDrive context manager."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Generator

from graph_onedrive._onedrive import OneDrive


# Set logger
logger = logging.getLogger(__name__)


@contextmanager
def OneDriveManager(
    config_path: str | Path, config_key: str = "onedrive"
) -> Generator[OneDrive]:
    """Context manager for the OneDrive class, only use this if you want to save and read from a file.
    Positional arguments:
        config_path (str|Path) -- path to configuration file
    Keyword arguments:
        config_key (str) -- key of the item storing the configuration (default = "onedrive")
    Returns:
        onedrive_instance (OneDrive) -- OneDrive object instance
    """
    logger.info("OneDriveManager creating instance")
    onedrive_instance = OneDrive.from_file(config_path, config_key)
    yield onedrive_instance
    logger.info("OneDriveManager saving instance configuration to file")
    onedrive_instance.to_file(config_path, config_key)
