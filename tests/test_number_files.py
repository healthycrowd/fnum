import pytest

from fnum import number_files
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
        make_files(test_files[3:5], dirpath)
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
        make_files(test_files[3:5], dirpath)
        number_files(dirpath, suffixes=[".txt"])
        assert_numbered_dir(test_files, dirpath)

        (dirpath / "3.txt").unlink()
        make_files(["f.txt"], dirpath)
        number_files(dirpath, suffixes=[".txt"])
        test_files = ["d.txt", "e.txt", "f.txt"]
        assert_numbered_dir(test_files, dirpath, start=3, ordered=True)


def test_number_files_fail_conflicting_files():
    test_files = ["1.txt", "1.text"]
    with temp_dir(test_files) as dirpath:
        with pytest.raises(FnumException):
            number_files(dirpath, suffixes=[".txt", ".text"])
