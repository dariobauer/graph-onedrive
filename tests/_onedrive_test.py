"""Tests the OneDrive class using pytest."""
import pytest


class TestGetTokens:
    """Tests the _get_token method."""

    def test_get_token(self):
        ...

    def test_get_token_failure(self):
        ...


class TestAuthorization:
    """Tests the _get_authorization method."""

    def test_get_authorization(self):
        ...

    def test_get_authorization_failure(self):
        ...


class TestHeaders:
    """Tests the _create_headers method."""

    def test_create_headers(self):
        ...

    def test_create_headers_failure(self):
        ...


class TestDriveDetails:
    """Tests the _get_drive_details, get_usage methods."""

    # get_drive_details
    def test_get_drive_details(self, onedrive):
        assert onedrive._drive_id == "b!t18F8ybsHUq1z3..."
        assert onedrive._drive_name is None
        assert onedrive._drive_type == "business"
        assert onedrive._owner_id == "f22fca32-227..."
        assert onedrive._owner_email == None
        assert onedrive._owner_name == "Ryan Gregg"
        assert onedrive._quota_used == 64274237
        assert onedrive._quota_remaining == 1099447353539
        assert onedrive._quota_total == 1099511627776

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

    def test_get_usage_failure_attribute(self, onedrive):
        with pytest.raises(AttributeError) as excinfo:
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
        assert items[0].get("id") == "01KDJMOTN..."

    def test_list_directory_folder(self, onedrive):
        item_id = "309EC495-3E92-431D-9124-F0299633171D"
        items = onedrive.list_directory(item_id)
        assert items[0].get("id") == "01KDJMOTN..."

    def test_list_directory_failure(self):
        ...


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
    def test_detail_item(self, onedrive, item_id, exp_name):
        item_details = onedrive.detail_item(item_id)
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
    def test_detail_item_verbose(self, onedrive, capsys, item_id, exp_stout):
        item_details = onedrive.detail_item(item_id, verbose=True)
        stdout, sterr = capsys.readouterr()
        assert stdout == exp_stout

    def test_detail_item_failure(self):
        ...

    # item_type
    @pytest.mark.parametrize(
        "item_id, exp_type",
        [("1file342i6r8h4-g7g", "file"), ("2folder3428hb-ng73", "folder")],
    )
    def test_item_type(self, onedrive, item_id, exp_type):
        item_type = onedrive.item_type(item_id)
        assert item_type == exp_type

    def test_item_type_failure(self):
        ...

    # is_folder
    @pytest.mark.parametrize(
        "item_id, exp_bool",
        [("1file342i6r8h4-g7g", False), ("2folder3428hb-ng73", True)],
    )
    def test_is_folder(self, onedrive, item_id, exp_bool):
        is_folder = onedrive.is_folder(item_id)
        assert is_folder == exp_bool

    def test_is_folder_failure(self):
        ...

    # is_file
    @pytest.mark.parametrize(
        "item_id, exp_bool",
        [("1file342i6r8h4-g7g", True), ("2folder3428hb-ng73", False)],
    )
    def test_is_file(self, onedrive, item_id, exp_bool):
        is_file = onedrive.is_file(item_id)
        assert is_file == exp_bool

    def test_is_file_failure(self):
        ...


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
        self, onedrive, folder_name, parent_folder_id, check_existing, exp_str
    ):
        item_id = onedrive.make_folder(folder_name, parent_folder_id, check_existing)
        assert item_id == exp_str

    def test_make_folder_failure(self):
        ...


class TestMove:
    """Tests the move_item method."""

    def test_move_item(self):
        ...

    def test_move_item_failure(self):
        ...


class TestCopy:
    """Tests the copy_item method."""

    def test_copy_item(self):
        ...

    def test_copy_item_failure(self):
        ...


class TestRename:
    """Tests the rename_item method."""

    def test_rename_item(self):
        ...

    def test_rename_item_failure(self):
        ...


class TestDelete:
    """Tests the delete_item method."""

    def test_delete_item(self):
        ...

    def test_delete_item_failure(self):
        ...


class TestDownload:
    """Tests the download_file, _download_async, _download_async_part methods."""

    # download_file
    def test_download_file(self):
        ...

    def test_download_file_failure(self):
        ...

    """# _download_async
    async def test_download_async(self):
        ...

    async def test_download_async_failure(self):
        ...

    # _download_async_part
    async def test_download_async_part(self):
        ...

    async def test_download_async_part_failure(self):
        ...
    """


class TestUpload:
    """Tests the upload_file, _upload_large_file methods."""

    # upload_file
    def test_upload_file(self):
        ...

    def test_upload_file_failure(self):
        ...

    # _upload_large_file
    def test_upload_large_file(self):
        ...

    def test_upload_large_file_failure(self):
        ...
