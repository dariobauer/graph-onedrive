"""Tests the OneDrive decorators pytest."""
from datetime import datetime
from datetime import timedelta

import pytest
import respx


class TestTokenRequiredDecorator:
    """Tests the @token_required decorator."""

    def test_token_required(self, onedrive):
        # Make a call to a mathod that uses the decorator
        onedrive.get_usage()
        # No errors is not the best way of asserting but is expected
        assert True

    def test_token_required_expired(self, temp_onedrive):
        # Set the access token time as expired by 2 seconds
        temp_onedrive._access_expires = datetime.timestamp(
            datetime.now() - timedelta(seconds=2)
        )
        # Make a call to a mathod that uses the decorator
        temp_onedrive.get_usage()
        # Check to ensure that the _access_expires is now in the future
        assert temp_onedrive._access_expires > datetime.timestamp(datetime.now()) + 30
