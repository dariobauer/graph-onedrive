"""Tests the OneDrive class using pytest."""
import pytest

import graph_onedrive


# Set the variables used to create the OneDrive instances in tests
# Warning: many tests require these to match the mock routes in conftest.py
CLIENT_ID = CLIENT_SECRET = "abc"
REFRESH_TOKEN = "123"
TENANT = "test"
REDIRECT = "http://localhost:8080"


class TestGetTokens:
    """Tests the _get_token method."""

    def test_get_token(self):
        NotImplemented

    def test_get_token_exceptions(self):
        NotImplemented


class TestAuthorization:
    """Tests the _get_authorization method."""

    def test_get_authorization(self):
        NotImplemented

    def test_get_authorization_exceptions(self):
        NotImplemented


class TestHeaders:
    """Tests the _create_headers method."""

    def test_create_headers(self):
        NotImplemented

    def test_create_headers_exceptions(self):
        NotImplemented


class TestDriveDetails:
    """Tests the _get_drive_details, get_usage methods."""

    # get_drive_details
    def test_get_drive_details(self, mock_auth_api, mock_graph_api):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        assert test_drive._drive_id == "b!t18F8ybsHUq1z3..."
        assert test_drive._drive_name is None
        assert test_drive._drive_type == "business"
        assert test_drive._owner_id == "f22fca32-227..."
        assert test_drive._owner_email == None
        assert test_drive._owner_name == "Ryan Gregg"
        assert test_drive._quota_used == 64274237
        assert test_drive._quota_remaining == 1099447353539
        assert test_drive._quota_total == 1099511627776

    def test_get_drive_details_exceptions(self):
        NotImplemented

    # get_usage
    @pytest.mark.parametrize(
        "unit, exp_used, exp_capacity, exp_unit",
        [
            ("b", 64274237, 1099511627776, "b"),
            ("kb", 62767.8, 1073741824, "kb"),
            ("MB", 61.3, 1048576, "mb"),
            ("gb", 0.1, 1024, "gb"),
            (None, 0.1, 1024, "gb"),
        ],
    )
    def test_get_usage(
        self, mock_auth_api, mock_graph_api, unit, exp_used, exp_capacity, exp_unit
    ):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        if unit == None:
            used, capacity, unit = test_drive.get_usage()
        else:
            used, capacity, unit = test_drive.get_usage(unit=unit)
        assert round(used, 1) == round(exp_used, 1)
        assert round(capacity, 1) == round(exp_capacity, 1)
        assert unit == exp_unit

    def test_get_usage_verbose(self, mock_auth_api, mock_graph_api, capsys):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        test_drive.get_usage(verbose=True)
        stdout, sterr = capsys.readouterr()
        assert stdout == "Using 0.1 gb (0.01%) of total 1024.0 gb.\n"

    def test_get_usage_exceptions(self, mock_auth_api, mock_graph_api):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        with pytest.raises(AttributeError):
            test_drive.get_usage(unit="tb")
        with pytest.raises(AttributeError):
            test_drive.get_usage(unit=None)


class TestListingDirectories:
    """Tests the list_directory method."""

    def test_list_directory_root(self, mock_auth_api, mock_graph_api):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        items = test_drive.list_directory()
        assert items[0].get("id") == "01KDJMOTN..."

    def test_list_directory_folder(self, mock_auth_api, mock_graph_api):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        item_id = "309EC495-3E92-431D-9124-F0299633171D"
        items = test_drive.list_directory(item_id)
        assert items[0].get("id") == "01KDJMOTN..."

    def test_list_directory_exceptions(self):
        NotImplemented


class TestItemDetails:
    """Tests the detail_item, item_type, is_folder, is_file methods."""

    # detail_item
    @pytest.mark.parametrize(
        "item_id, exp_name",
        [
            ("1file342i6r8h4-g7g", "2021-02-08 18.53.41.mov"),
            ("2folder3428hb-ng73", "temp"),
        ],
    )
    def test_detail_item(self, mock_auth_api, mock_graph_api, item_id, exp_name):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        item_details = test_drive.detail_item(item_id)
        assert item_details.get("name") == exp_name

    @pytest.mark.parametrize(
        "item_id, exp_stout",
        [
            (
                "1file342i6r8h4-g7g",
                "id: 01KDJMOTOM62V...\nname: 2021-02-08 18.53.41.mov\ntype: file\ncreated: 2021-10-23T23:24:56Z by: Ryan Gregg\nmodified: 2021-10-23T23:25:48Z by: Ryan Gregg\nsize: 4926874\nweb url: https://consco.sharepoint.com/personal/consco/Documents/temp/2021-02-08%2018.53.41.mov\n",
            ),
            (
                "2folder3428hb-ng73",
                "id: 01KDJMOTNGDMA4KB...\nname: temp\ntype: folder\ncreated: 2021-10-24T08:56:48Z by: Ryan Gregg\nmodified: 2021-10-24T08:56:48Z by: Ryan Gregg\nsize: 19528345\nweb url: https://constco.sharepoint.com/personal/consco/Documents/temp\n",
            ),
        ],
    )
    def test_detail_item_verbose(
        self, mock_auth_api, mock_graph_api, capsys, item_id, exp_stout
    ):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        item_details = test_drive.detail_item(item_id, verbose=True)
        stdout, sterr = capsys.readouterr()
        assert stdout == exp_stout

    def test_detail_item_exceptions(self):
        NotImplemented

    # item_type
    @pytest.mark.parametrize(
        "item_id, exp_type",
        [("1file342i6r8h4-g7g", "file"), ("2folder3428hb-ng73", "folder")],
    )
    def test_item_type(self, mock_auth_api, mock_graph_api, item_id, exp_type):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        item_type = test_drive.item_type(item_id)
        assert item_type == exp_type

    def test_item_type_exceptions(self):
        NotImplemented

    # is_folder
    @pytest.mark.parametrize(
        "item_id, exp_bool",
        [("1file342i6r8h4-g7g", False), ("2folder3428hb-ng73", True)],
    )
    def test_is_folder(self, mock_auth_api, mock_graph_api, item_id, exp_bool):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        is_folder = test_drive.is_folder(item_id)
        assert is_folder == exp_bool

    def test_is_folder_exceptions(self):
        NotImplemented

    # is_file
    @pytest.mark.parametrize(
        "item_id, exp_bool",
        [("1file342i6r8h4-g7g", True), ("2folder3428hb-ng73", False)],
    )
    def test_is_file(self, mock_auth_api, mock_graph_api, item_id, exp_bool):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        is_file = test_drive.is_file(item_id)
        assert is_file == exp_bool

    def test_is_file_exceptions(self):
        NotImplemented


class TestMakeFolder:
    """Tests the make_folder method."""

    @pytest.mark.parametrize(
        "folder_name, parent_folder_id, check_existing, exp_str",
        [
            ("tesy 1", "hssdf97ds", True, "ACEA49D1-144..."),
            ("tesy 1", "hssdf97ds", False, "ACEA49D1-144..."),
            ("tesy 1", None, True, "ACEA49D1-144..."),
            ("tesy 1", None, False, "ACEA49D1-144...")
            # To-do: allow for other folder names by using a side effect in the mock route
        ],
    )
    def test_make_folder(
        mock_auth_api,
        mock_graph_api,
        folder_name,
        parent_folder_id,
        check_existing,
        exp_str,
    ):
        test_drive = graph_onedrive.create(
            CLIENT_ID, CLIENT_SECRET, TENANT, REDIRECT, REFRESH_TOKEN
        )
        item_id = test_drive.make_folder(folder_name, parent_folder_id, check_existing)
        assert item_id == exp_str

    def test_make_folder_exceptions(self):
        NotImplemented


class TestMove:
    """Tests the move_item method."""

    def test_move_item(self):
        NotImplemented

    def test_move_item_exceptions(self):
        NotImplemented


class TestCopy:
    """Tests the copy_item method."""

    def test_copy_item(self):
        NotImplemented

    def test_copy_item_exceptions(self):
        NotImplemented


class TestRename:
    """Tests the rename_item method."""

    def test_rename_item(self):
        NotImplemented

    def test_rename_item_exceptions(self):
        NotImplemented


class TestDelete:
    """Tests the delete_item method."""

    def test_delete_item(self):
        NotImplemented

    def test_delete_item_exceptions(self):
        NotImplemented


class TestDownload:
    """Tests the download_file, _download_async, _download_async_part methods."""

    # download_file
    def test_download_file(self):
        NotImplemented

    def test_download_file_exceptions(self):
        NotImplemented

    """# _download_async
    async def test_download_async(self):
        NotImplemented

    async def test_download_async_exceptions(self):
        NotImplemented

    # _download_async_part
    async def test_download_async_part(self):
        NotImplemented

    async def test_download_async_part_exceptions(self):
        NotImplemented
    """


class TestUpload:
    """Tests the upload_file, _upload_large_file methods."""

    # upload_file
    def test_upload_file(self):
        NotImplemented

    def test_upload_file_exceptions(self):
        NotImplemented

    # _upload_large_file
    def test_upload_large_file(self):
        NotImplemented

    def test_upload_large_file_exceptions(self):
        NotImplemented
