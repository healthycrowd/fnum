from pathlib import Path
from contextlib import contextmanager
import yaml


class FnumException(Exception):
    pass


def number_files(dirpath, suffixes, progressbar=None):
    dirpath = Path(dirpath)

    try:
        with open(str(dirpath / "metadata.yaml"), "r") as fh:
            metadata = fh.read()
            metadata = yaml.safe_load(metadata)
        regen_meta = False
    except FileNotFoundError:
        metadata = {
            "order": [],
            "originals": {},
        }
        regen_meta = True

    num = 1

    def numpath(suffix):
        return dirpath / (str(num) + suffix)

    while used_suffixes := tuple(
        suffix for suffix in suffixes if numpath(suffix).exists()
    ):
        if len(used_suffixes) > 1:
            raise FnumException(
                f"Unexpectedly found multiple existing files with number {num}"
            )
        if regen_meta:
            filepath = numpath(used_suffixes[0])
            metadata["order"].append(filepath.name)
            metadata["originals"][filepath.name] = filepath.name
        num += 1

    files = list(dirpath.iterdir())
    if not progressbar:

        @contextmanager
        def noop_progressbar(*args, **kwargs):
            pass

        progressbar = noop_progessbar
    with progressbar(files, length=len(files), label="Processing files") as bar:
        for filepath in bar:
            if not filepath.is_file() or filepath.suffix not in suffixes:
                continue

            try:
                if int(filepath.stem) <= num:
                    continue
            except ValueError:
                pass

            newpath = numpath(filepath.suffix)
            num += 1

            try:
                order_index = metadata["order"].index(filepath.name)
                metadata["order"][order_index] = newpath.name
            except ValueError:
                metadata["order"].append(newpath.name)
            try:
                original_index = metadata["originals"].values().index(filepath.name)
                original_key = metadata["originals"].keys(original_index)
                metadata["originals"][original_key] = newpath.name
            except ValueError:
                metadata["originals"][filepath.name] = newpath.name

            filepath.rename(newpath)

    metadata["max"] = num - 1
    return metadata


def write_max(dirpath, metadata):
    dirpath = Path(dirpath)

    with open(str(dirpath / "fnum.max.txt"), "w") as fh:
        fh.write(str(metadata["max"]))


def write_metadata(dirpath, metadata):
    dirpath = Path(dirpath)

    with open(str(dirpath / "fnum.metadata.yaml"), "w") as fh:
        fh.write(yaml.safe_dump(metadata))
