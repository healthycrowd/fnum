from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import contextmanager
import pytest

from fnum import number_files
from fnum.exceptions import FnumException


TEST_FILES = ["a", "b", "c", "d", "e"]


@contextmanager
def temp_dir(files):
    with TemporaryDirectory() as tempdir:
        dirpath = Path(tempdir)
        for filename in files:
            filepath = dirpath / filename
            filepath.write_text(filepath.stem)
        yield dirpath


def assert_numbered_dir(files, dirpath, start=1, ordered=False):
    found = []
    originalpaths = tuple(dirpath / filename for filename in files)
    expected_data = [originalpath.stem for originalpath in originalpaths]
    suffixes = {originalpath.suffix for originalpath in originalpaths}

    for index, filename in enumerate(files):
        if ordered:
            filepath = dirpath / filename
            data = filepath.read_text()
            assert data == filepath.stem
            if data in expected_data:
                expected_data.remove(data)
        else:
            for suffix in suffixes:
                filepath = dirpath / f"{index+start}{suffix}"
                if filepath.exists():
                    data = filepath.read_text()
                    if data in expected_data:
                        expected_data.remove(data)
                        break
                    else:
                        assert False, f"Unexpected data {data} in file {filepath.name}"
            else:
                assert (
                    False
                ), f"Missing file {index+start}, attempted suffixes {suffixes}"

    assert not expected_data, expected_data


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


@pytest.mark.skip()
def test_number_files_success_multiple_runs_add():
    pass


@pytest.mark.skip()
def test_number_files_success_multiple_runs_remove():
    pass


@pytest.mark.skip()
def test_number_files_success_multiple_runs_add_and_remove():
    pass


@pytest.mark.skip()
def test_number_files_fail_conflicting_files():
    pass


@pytest.mark.skip()
def test_write_max_success():
    pass


@pytest.mark.skip()
def test_write_metadata_success():
    pass


@pytest.mark.skip()
def test_cli():
    pass
