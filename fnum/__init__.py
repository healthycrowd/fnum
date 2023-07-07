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

    # Find what files we already have in order
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

    # Shift down existing ordered files so new ones are added at the end
    nummax = num - 1
    for filepath in dirpath.iterdir():
        if not filepath.is_file() or filepath.suffix not in suffixes:
            continue

        try:
            filenum = int(filepath.stem)
        except ValueError:
            continue

        if filenum > nummax:
            nummax = filenum

    def move_file(filepath):
        newpath = numpath(filepath.suffix)

        try:
            order_index = metadata.order.index(filepath.name)
            metadata.order[order_index] = newpath.name
        except ValueError:
            metadata.order.append(newpath.name)
        try:
            original_index = tuple(metadata.originals.values()).index(filepath.name)
            original_key = tuple(metadata.originals.keys())[original_index]
            metadata.originals[original_key] = newpath.name
        except ValueError:
            metadata.originals[filepath.name] = newpath.name

        filepath.rename(newpath)

    for filenum in range(num, nummax + 1):
        possible_names = tuple(dirpath / f"{filenum}{suffix}" for suffix in suffixes)
        used_suffixes = tuple(
            filepath for filepath in possible_names if filepath.exists()
        )
        if len(used_suffixes) > 1:
            raise FnumException(
                f"Unexpectedly found multiple existing files with number {filenum}"
            )

        if not used_suffixes:
            for filepath in possible_names:
                name = filepath.name
                if name in metadata.order or name in metadata.originals.values():
                    try:
                        metadata.order.remove(name)
                    except ValueError:
                        pass
                    try:
                        original_index = tuple(metadata.originals.values()).index(name)
                        original_key = tuple(metadata.originals.keys())[original_index]
                        del metadata.originals[original_key]
                    except ValueError:
                        pass

                    break
            continue

        filepath = used_suffixes[0]
        move_file(filepath)
        num += 1
        if int(filepath.stem) == nummax:
            break

    # Find new files
    files = list(dirpath.iterdir())
    if not progressbar:

        @contextmanager
        def noop_progressbar(*args, **kwargs):
            yield files

        progressbar = noop_progressbar
    with progressbar(files, length=len(files), label="Processing files") as bar:
        for filepath in bar:
            if not filepath.is_file() or filepath.suffix not in suffixes:
                continue

            try:
                if int(filepath.stem) <= num:
                    continue
            except ValueError:
                pass

            move_file(filepath)
            num += 1

    metadata.max = num - 1
    return metadata
