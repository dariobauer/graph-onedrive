"""OneDrive context manager.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from graph_onedrive._onedrive import OneDrive


@contextmanager
def OneDriveManager(
    file_path: str | Path, config_key: str = "onedrive"
) -> Generator[OneDrive, None, None]:
    """Context manager for the OneDrive class, only use this if you want to save and read from a file.
    Positional arguments:
        file_path (str|Path) -- path to configuration json file
    Keyword arguments:
        config_key (str) -- key of the json item storing the configuration (default = "onedrive")
    Returns:
        onedrive_instance (OneDrive) -- OneDrive object instance
    """
    logging.info("OneDriveManager creating instance")
    onedrive_instance = OneDrive.from_json(file_path, config_key)
    yield onedrive_instance
    logging.info("OneDriveManager saving instance configuration to file")
    onedrive_instance.to_json(file_path, config_key)
