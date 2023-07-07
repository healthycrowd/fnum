from pathlib import Path
from contextlib import contextmanager

from .exceptions import FnumException
from .metadata import FnumMetadata, FnumMax


__version__ = "1.1.0"


def number_files(dirpath, suffixes, progressbar=None):
    dirpath = Path(dirpath)

    try:
        metadata = FnumMetadata.from_file(dirpath)
        regen_meta = False
    except FileNotFoundError:
        metadata = FnumMetadata.get_default()
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
            metadata.order.append(filepath.name)
            metadata.originals[filepath.name] = filepath.name
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
                order_index = metadata.order.index(filepath.name)
                metadata.order[order_index] = newpath.name
            except ValueError:
                metadata.order.append(newpath.name)
            try:
                original_index = metadata.originals.values().index(filepath.name)
                original_key = metadata.originals.keys(original_index)
                metadata.originals[original_key] = newpath.name
            except ValueError:
                metadata.originals[filepath.name] = newpath.name

            filepath.rename(newpath)

    metadata.max = num - 1
    return metadata
