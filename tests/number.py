from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import contextmanager
from imeta import ImageMetadata


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


def assert_imeta(filepath, data):
    metapath = Path(ImageMetadata.for_image(str(filepath)))
    assert metapath.exists(), f"Missing file {metapath.name}"
    expected = metapath.read_text()
    assert data == expected, f"{metapath.name} contains {data}, expected {expected}"


def assert_numbered_dir(
    files, dirpath, start=1, ordered=False, with_imeta=False, contents=None
):
    found = []
    originalpaths = tuple(Path(filename) for filename in files)
    expected_data = [originalpath.stem for originalpath in originalpaths]
    suffixes = {originalpath.suffix for originalpath in originalpaths}

    for index, filename in enumerate(files):
        if ordered:
            suffix = Path(filename).suffix
            expected = contents[index] if contents else Path(filename).stem
            filepath = dirpath / f"{index+start}{suffix}"
            data = filepath.read_text()
            assert (
                data == expected
            ), f"{filepath.name} contains {data}, expected {expected}"
            if data in expected_data:
                expected_data.remove(data)
            if with_imeta:
                assert_imeta(filepath, data)
        else:
            for suffix in suffixes:
                filepath = dirpath / f"{index+start}{suffix}"
                if filepath.exists():
                    data = filepath.read_text()
                    assert (
                        data in contents if contents else expected_data
                    ), f"Unexpected data {data} in file {filepath.name}"
                    expected_data.remove(data)
                    if with_imeta:
                        assert_imeta(filepath, data)
                    break
            else:
                assert (
                    False
                ), f"Missing file {index+start}, attempted suffixes {suffixes}"

    if not contents:
        assert not expected_data, expected_data
