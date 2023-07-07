from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import contextmanager


def make_files(files, dirpath):
    for filename in files:
        filepath = dirpath / filename
        filepath.write_text(filepath.stem)


@contextmanager
def temp_dir(files):
    with TemporaryDirectory() as tempdir:
        dirpath = Path(tempdir)
        make_files(files, dirpath)
        yield dirpath


def assert_numbered_dir(files, dirpath, start=1, ordered=False):
    found = []
    originalpaths = tuple(Path(filename) for filename in files)
    expected_data = [originalpath.stem for originalpath in originalpaths]
    suffixes = {originalpath.suffix for originalpath in originalpaths}

    for index, filename in enumerate(files):
        if ordered:
            suffix = Path(filename).suffix
            expected = Path(filename).stem
            filepath = dirpath / f"{index+start}{suffix}"
            data = filepath.read_text()
            assert data == expected
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
