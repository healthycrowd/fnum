import pytest

from fnum import number_files, FnumMetadata
from fnum.exceptions import FnumException

from .number import make_files, temp_dir, assert_numbered_dir


TEST_FILES = ["a", "b", "c", "d", "e"]


def test_number_files_success_one_suffix():
    test_files = ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]
    with temp_dir(test_files) as dirpath:
        number_files(dirpath, suffixes=[".txt"])
        assert_numbered_dir(test_files, dirpath)


def test_number_files_success_multiple_suffixes():
    test_files = ["a.txt", "b.text", "c.txt", "d.text", "e.txt"]
    with temp_dir(test_files) as dirpath:
        number_files(dirpath, suffixes=[".txt", ".text"])
        assert_numbered_dir(test_files, dirpath)


def test_number_files_success_no_renames():
    test_files = ["1.txt", "2.txt", "3.txt", "4.txt", "5.txt"]
    with temp_dir(test_files) as dirpath:
        number_files(dirpath, suffixes=[".txt"])
        assert_numbered_dir(test_files, dirpath, ordered=True)


def test_number_files_success_no_files():
    test_files = []
    with temp_dir(test_files) as dirpath:
        number_files(dirpath, suffixes=[".txt"])
        assert_numbered_dir(test_files, dirpath)


def test_number_files_success_multiple_runs_add():
    test_files = ["a.txt", "b.txt", "c.txt"]
    with temp_dir(test_files) as dirpath:
        number_files(dirpath, suffixes=[".txt"])
        assert_numbered_dir(test_files, dirpath)

        test_files = ["d.txt", "e.txt"]
        make_files(test_files, dirpath)
        number_files(dirpath, suffixes=[".txt"])
        assert_numbered_dir(test_files, dirpath, start=4)


def test_number_files_success_multiple_runs_remove():
    test_files = ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]
    with temp_dir(test_files[0:2]) as dirpath:
        number_files(dirpath, suffixes=[".txt"])
        make_files(test_files[2:3], dirpath)
        number_files(dirpath, suffixes=[".txt"])
        make_files(test_files[3:4], dirpath)
        number_files(dirpath, suffixes=[".txt"])
        make_files(test_files[4:5], dirpath)
        number_files(dirpath, suffixes=[".txt"])
        assert_numbered_dir(test_files, dirpath)

        (dirpath / "3.txt").unlink()
        number_files(dirpath, suffixes=[".txt"])
        test_files = ["d.txt", "e.txt"]
        assert_numbered_dir(test_files, dirpath, start=3, ordered=True)


def test_number_files_success_multiple_runs_add_and_remove():
    test_files = ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]
    with temp_dir(test_files[0:2]) as dirpath:
        number_files(dirpath, suffixes=[".txt"])
        make_files(test_files[2:3], dirpath)
        number_files(dirpath, suffixes=[".txt"])
        make_files(test_files[3:4], dirpath)
        number_files(dirpath, suffixes=[".txt"])
        make_files(test_files[4:5], dirpath)
        number_files(dirpath, suffixes=[".txt"])
        assert_numbered_dir(test_files, dirpath)

        (dirpath / "3.txt").unlink()
        make_files(["f.txt"], dirpath)
        number_files(dirpath, suffixes=[".txt"], write_metadata=True)
        metadata = FnumMetadata.from_file(dirpath)
        test_files = ["d.txt", "e.txt", "f.txt"]
        assert_numbered_dir(test_files, dirpath, start=3, ordered=True)
        assert metadata.order == ["1.txt", "2.txt", "3.txt", "4.txt", "5.txt"]
        assert len(metadata.originals.keys()) == 5, metadata.originals
        assert metadata.max == 5


def test_number_files_fail_conflicting_files():
    test_files = ["1.txt", "1.text"]
    with temp_dir(test_files) as dirpath:
        with pytest.raises(FnumException):
            number_files(dirpath, suffixes=[".txt", ".text"])


def test_number_files_success_with_missing_imeta():
    test_files = ["a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg"]
    with temp_dir(test_files) as dirpath:
        number_files(dirpath, suffixes=[".jpg"], include_imeta=True)
        assert_numbered_dir(test_files, dirpath)


def test_number_files_success_with_imeta():
    test_files = ["a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg"]
    meta_files = ["a.json", "b.json", "c.json", "d.json", "e.json"]
    with temp_dir(test_files + meta_files) as dirpath:
        number_files(dirpath, suffixes=[".jpg"], include_imeta=True)
        assert_numbered_dir(test_files, dirpath)


def test_number_files_success_order_new():
    test_files = ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]
    with temp_dir([]) as dirpath:
        number_files(dirpath, suffixes=[".txt"], write_metadata=True)
        make_files(test_files, dirpath)
        metadata = FnumMetadata.from_file(dirpath)
        metadata.order = test_files
        metadata.to_file(dirpath)

        number_files(dirpath, suffixes=[".txt"], write_metadata=True)
        assert_numbered_dir(test_files, dirpath, ordered=True)


def test_number_files_success_order_existing():
    test_files = ["5.txt", "3.txt", "1.txt", "2.txt", "4.txt"]
    with temp_dir([]) as dirpath:
        number_files(dirpath, suffixes=[".txt"], write_metadata=True)
        make_files(test_files, dirpath)
        metadata = FnumMetadata.from_file(dirpath)
        metadata.order = test_files
        metadata.to_file(dirpath)

        number_files(dirpath, suffixes=[".txt"], write_metadata=True)
        file_order = ["1.txt", "2.txt", "3.txt", "4.txt", "5.txt"]
        assert_numbered_dir(file_order, dirpath, ordered=True)
        metadata = FnumMetadata.from_file(dirpath)
        assert metadata.order == test_files


def test_number_files_fail_broken_order():
    test_files = ["1.txt", "2.txt", "3.txt", "4.txt", "5.txt"]
    with temp_dir(test_files) as dirpath:
        number_files(dirpath, suffixes=[".txt"], write_metadata=True)
        metadata = FnumMetadata.from_file(dirpath)
        metadata.order.remove("3.txt")
        metadata.to_file(dirpath)
        (dirpath / "2.txt").unlink()

        with pytest.raises(FnumException):
            number_files(dirpath, suffixes=[".txt"], write_metadata=True)


def test_number_files_success_add_with_order():
    test_files = ["1.txt", "2.txt"]
    with temp_dir(test_files) as dirpath:
        number_files(dirpath, suffixes=[".txt"], write_metadata=True)
        new_files = ["101.txt", "200.txt", "100.txt", "new.txt"]
        make_files(new_files, dirpath)
        metadata = FnumMetadata.from_file(dirpath)
        metadata.order += new_files
        metadata.to_file(dirpath)

        number_files(dirpath, suffixes=[".txt"], write_metadata=True)
        file_order = ["1.txt", "2.txt", "3.txt", "4.txt", "5.txt"]
        assert_numbered_dir(
            file_order,
            dirpath,
            ordered=True,
            contents=["1", "2", "100", "101", "200", "new"],
        )
        metadata = FnumMetadata.from_file(dirpath)
        assert metadata.order == ["1.txt", "2.txt", "4.txt", "5.txt", "3.txt", "6.txt"]
