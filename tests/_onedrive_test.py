"""Tests the OneDrive class using pytest."""
import pytest

from .conftest import ACCESS_TOKEN
from .conftest import CLIENT_ID
from .conftest import REDIRECT
from .conftest import REFRESH_TOKEN
from .conftest import SCOPE
from .conftest import TENANT


class TestGetTokens:
    """Tests the _get_token method."""

    def test_get_tokens_using_auth_code(self, temp_onedrive):
        temp_onedrive.refresh_token == ""
        temp_onedrive._get_token()
        assert temp_onedrive.refresh_token == REFRESH_TOKEN
        assert temp_onedrive._access_token == ACCESS_TOKEN

    def test_get_tokens_using_refresh_token(self, temp_onedrive):
        temp_onedrive._get_token()
        assert temp_onedrive.refresh_token == REFRESH_TOKEN
        assert temp_onedrive._access_token == ACCESS_TOKEN

    @pytest.mark.skip(reason="not implemented")
    def test_get_token_failure(self):
        ...


class TestAuthorization:
    """Tests the _get_authorization method."""

    @pytest.mark.skip(reason="not implemented")
    def test_get_authorization(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    def test_get_authorization_failure(self):
        ...


class TestHeaders:
    """Tests the _create_headers method."""

    def test_create_headers(self, temp_onedrive):
        temp_onedrive._headers = {}
        temp_onedrive._create_headers()
        exp_headers = {"Accept": "*/*", "Authorization": "Bearer " + ACCESS_TOKEN}
        assert temp_onedrive._headers == exp_headers

    def test_create_headers_failure_type(self, temp_onedrive):
        temp_onedrive._headers = {}
        temp_onedrive._access_token = 123
        with pytest.raises(TypeError) as excinfo:
            temp_onedrive._create_headers()
        (msg,) = excinfo.value.args
        assert msg == "expected self._access_token to be type 'str', got type 'int'"

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
        assert onedrive._drive_id == "b!t18F8ybsHUq1z3"
        assert onedrive._drive_name is None
        assert onedrive._drive_type == "business"
        assert onedrive._owner_id == "f22fca32-227"
        assert onedrive._owner_email == None
        assert onedrive._owner_name == "Ryan Gregg"
        assert onedrive._quota_used == 64274237
        assert onedrive._quota_remaining == 1099447353539
        assert onedrive._quota_total == 1099511627776

    @pytest.mark.skip(reason="not implemented")
    def test_get_drive_details_failure(self):
        ...

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
    def test_get_usage(self, onedrive, unit, exp_used, exp_capacity, exp_unit):
        if unit == None:
            used, capacity, unit = onedrive.get_usage()
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
        assert msg == "Input Error : 'tb' is not a supported unit"

    @pytest.mark.parametrize(
        "unit, exp_msg",
        [
            (1, "Input Error : unit expected type 'str', got type 'int'"),
            (None, "Input Error : unit expected type 'str', got type 'NoneType'"),
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
        assert items[0].get("id") == "01KDJMOTN"

    def test_list_directory_folder(self, onedrive):
        item_id = "01KDJMOTNGDMA4KB"
        items = onedrive.list_directory(item_id)
        assert items[0].get("id") == "01KDJMOTN"

    @pytest.mark.skip(reason="not implemented")
    def test_list_directory_failure(self):
        ...


class TestItemDetails:
    """Tests the detail_item, item_type, is_folder, is_file methods."""

    # detail_item
    @pytest.mark.parametrize(
        "item_id, exp_name",
        [
            ("01KDJMOTOM62V", "2021-02-08 18.53.41.mov"),
            ("01KDJMOTNGDMA4KB", "temp"),
        ],
    )
    def test_detail_item(self, onedrive, item_id, exp_name):
        item_details = onedrive.detail_item(item_id)
        assert item_details.get("name") == exp_name

    @pytest.mark.parametrize(
        "item_id, exp_stout",
        [
            (
                "01KDJMOTOM62V",
                "item id: 01KDJMOTOM62V\n"
                "name: 2021-02-08 18.53.41.mov\n"
                "type: file\n"
                "created: 2021-10-23T23:24:56Z by: Ryan Gregg\n"
                "last modified: 2021-10-23T23:25:48Z by: Ryan Gregg\n"
                "size: 4926874\n"
                "web url: https://consco.sharepoint.com/personal/consco/Documents/temp/2021-02-08%2018.53.41.mov\n"
                "file system created: 2021-10-23T23:24:56Z\n"
                "file system last modified: 2021-10-23T23:25:48Z\n"
                "file quickXor hash: wFwchJC3Iwr99ytGd+8vuSXCe0A=\n",
            ),
            (
                "01KDJMOTNGDMA4KB",
                "item id: 01KDJMOTNGDMA4KB\n"
                "name: temp\n"
                "type: folder\n"
                "created: 2021-10-24T08:56:48Z by: Ryan Gregg\n"
                "last modified: 2021-10-24T08:56:48Z by: Ryan Gregg\n"
                "size: 19528345\n"
                "web url: https://constco.sharepoint.com/personal/consco/Documents/temp\n"
                "file system created: 2021-10-24T08:56:48Z\n"
                "file system last modified: 2021-10-24T08:56:48Z\n",
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

    # item_type
    @pytest.mark.parametrize(
        "item_id, exp_type",
        [("01KDJMOTOM62V", "file"), ("01KDJMOTNGDMA4KB", "folder")],
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
        [("01KDJMOTOM62V", False), ("01KDJMOTNGDMA4KB", True)],
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
        [("01KDJMOTOM62V", True), ("01KDJMOTNGDMA4KB", False)],
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
                "01KDJMOTOM62V",
                "view",
                None,
                None,
                "anonymous",
                "https://onedrive.com/fakelink",
            ),
            (
                "01KDJMOTOM62V",
                "edit",
                None,
                None,
                "anonymous",
                "https://onedrive.com/fakelink",
            ),
            (
                "01KDJMOTOM62V",
                "edit",
                None,
                None,
                "organization",
                "https://onedrive.com/fakelink",
            ),
            (
                "01KDJMOTNGDMA4KB",
                "view",
                None,
                None,
                "anonymous",
                "https://onedrive.com/fakelink",
            ),
            (
                "01KDJMOTNGDMA4KB",
                "edit",
                None,
                None,
                "anonymous",
                "https://onedrive.com/fakelink",
            ),
            (
                "01KDJMOTNGDMA4KB",
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
                "API Error : share link could not be created (item not found)",
            ),
        ],
    )
    def test_create_share_link_failure_generic(
        self, onedrive, item_id, link_type, password, expiration, scope, exp_msg
    ):
        with pytest.raises(Exception) as excinfo:
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
                "link_type expected type 'str', got 'set'",
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
            ("tesy 1", "01KDJMOTNGDMA4KB", True, "ACEA49D1-144"),
            ("tesy 1", "01KDJMOTNGDMA4KB", False, "ACEA49D1-144"),
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

    @pytest.mark.skip(reason="not implemented")
    def test_move_item(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    def test_move_item_failure(self):
        ...


class TestCopy:
    """Tests the copy_item method."""

    @pytest.mark.skip(reason="not implemented")
    def test_copy_item(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    def test_copy_item_failure(self):
        ...


class TestRename:
    """Tests the rename_item method."""

    @pytest.mark.skip(reason="not implemented")
    def test_rename_item(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    def test_rename_item_failure(self):
        ...


class TestDelete:
    """Tests the delete_item method."""

    @pytest.mark.skip(reason="not implemented")
    def test_delete_item(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    def test_delete_item_failure(self):
        ...


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
    @pytest.mark.skip(reason="not implemented")
    def test_upload_file(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    def test_upload_file_failure(self):
        ...

    # _upload_large_file
    @pytest.mark.skip(reason="not implemented")
    def test_upload_large_file(self):
        ...

    @pytest.mark.skip(reason="not implemented")
    def test_upload_large_file_failure(self):
        ...
