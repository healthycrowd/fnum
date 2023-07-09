from pathlib import Path
from tempfile import TemporaryDirectory
import yaml

from fnum import FnumMetadata, FnumMax


TEST_DATA = {
    "order": ["1.txt", "2.txt", "3.txt"],
    "originals": {
        "a.txt": "1.txt",
        "b.txt": "2.txt",
        "c.txt": "3.txt",
    },
    "max": 3,
}
TEST_MAX = 1


def assert_metadata(data, metadata):
    for key, value in data.items():
        assert getattr(metadata, key) == value


def test_metadata_from_dict_success():
    metadata = FnumMetadata(TEST_DATA)
    assert_metadata(TEST_DATA, metadata)


def test_metadata_from_str_success():
    data_str = yaml.safe_dump(TEST_DATA)

    metadata = FnumMetadata.from_str(data_str)
    assert_metadata(TEST_DATA, metadata)


def test_metadata_from_file_success():
    data_str = yaml.safe_dump(TEST_DATA)
    tmpdir = TemporaryDirectory()
    filepath = Path(tmpdir.name) / "fnum.metadata.yaml"
    filepath.write_text(data_str)

    metadata = FnumMetadata.from_file(tmpdir.name)
    assert_metadata(TEST_DATA, metadata)


def test_metadata_to_dict_success():
    metadata = FnumMetadata(TEST_DATA)
    assert dict(metadata) == TEST_DATA


def test_metadata_to_str_success():
    metadata = FnumMetadata(TEST_DATA)
    assert str(metadata) == yaml.safe_dump(TEST_DATA)


def test_metadata_to_file_success():
    metadata = FnumMetadata(TEST_DATA)
    tmpdir = TemporaryDirectory()
    filepath = Path(tmpdir.name) / "fnum.metadata.yaml"

    metadata.to_file(tmpdir.name)
    data_str = filepath.read_text()
    assert data_str == yaml.safe_dump(TEST_DATA)


def test_metadata_contains_success():
    metadata = FnumMetadata(TEST_DATA)
    assert metadata.contains("1.txt") == True
    assert metadata.contains("a.txt") == True
    assert metadata.contains("nope.txt") == False
    assert_metadata(TEST_DATA, metadata)


def test_max_from_str_success():
    assert FnumMax.from_str(str(TEST_MAX)).value == TEST_MAX


def test_max_from_file_success():
    tmpdir = TemporaryDirectory()
    filepath = Path(tmpdir.name) / "fnum.max.yaml"
    filepath.write_text(str(TEST_MAX))

    fmax = FnumMax.from_file(tmpdir.name)
    assert fmax.value == TEST_MAX


def test_max_to_str_success():
    assert str(FnumMax(TEST_MAX)) == str(TEST_MAX)


def test_max_to_file_success():
    tmpdir = TemporaryDirectory()
    filepath = Path(tmpdir.name) / "fnum.max.yaml"
    fmax = FnumMax(TEST_MAX)

    fmax.to_file(tmpdir.name)
    assert filepath.read_text() == str(TEST_MAX)


def test_metadata_file_unicode():
    test_str = "<Imagé *>"
    test_data = {
        "order": [test_str],
        "originals": {test_str: test_str},
        "max": 1,
    }
    tmpdir = TemporaryDirectory()
    filepath = Path(tmpdir.name) / "fnum.metadata.yaml"

    metadata = FnumMetadata(test_data)
    metadata.to_file(tmpdir.name)
    data_str = filepath.read_text()
    assert data_str == yaml.safe_dump(test_data, allow_unicode=True)

    metadata = FnumMetadata.from_file(tmpdir.name)
    assert dict(metadata) == test_data

    data_str = filepath.read_bytes()
    assert test_str.encode() in data_str
