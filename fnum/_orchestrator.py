from pathlib import Path
from imeta import ImageMetadata

from .exceptions import FnumException
from .metadata import FnumMetadata


class _NumberOrchestrator:
    num = 1
    metadata = None
    regen_meta = False

    def __init__(self, dirpath, suffixes, write_metadata, write_max, include_imeta):
        self.dirpath = Path(dirpath)
        self.suffixes = suffixes
        self.write_metadata = write_metadata
        self.write_max = write_max
        self.include_imeta = include_imeta

        try:
            self.metadata = FnumMetadata.from_file(dirpath)
            self.regen_meta = False
        except FileNotFoundError:
            if self.write_metadata or self.write_max:
                self.metadata = FnumMetadata.get_default()
                self.regen_meta = True
            else:
                # remove this when possible
                self.metadata = FnumMetadata.get_default()
                self.regen_meta = True

    def numpath(self, suffix):
        return self.dirpath / (str(self.num) + suffix)

    def move_file(self, filepath):
        newpath = self.numpath(filepath.suffix)
        if newpath.exists():
            raise FnumException("Can't override existing file {newpath.name}")

        try:
            order_index = self.metadata.order.index(filepath.name)
            self.metadata.order[order_index] = newpath.name
        except ValueError:
            self.metadata.order.append(newpath.name)
        try:
            original_index = tuple(self.metadata.originals.values()).index(
                filepath.name
            )
            original_key = tuple(self.metadata.originals.keys())[original_index]
            self.metadata.originals[original_key] = newpath.name
        except ValueError:
            self.metadata.originals[filepath.name] = newpath.name

        filepath.rename(newpath)
        if self.include_imeta:
            metapath = Path(ImageMetadata.for_image(str(filepath)))
            newmetapath = metapath.parents[0] / f"{newpath.stem}{metapath.suffix}"
            try:
                metapath.rename(newmetapath)
            except FileNotFoundError:
                pass

    def find_ordered(self):
        # Find what files we already have in order
        while used_suffixes := tuple(
            suffix for suffix in self.suffixes if self.numpath(suffix).exists()
        ):
            if len(used_suffixes) > 1:
                raise FnumException(
                    f"Unexpectedly found multiple existing files with number {self.num}"
                )
            if self.regen_meta:
                filepath = self.numpath(used_suffixes[0])
                self.metadata.order.append(filepath.name)
                self.metadata.originals[filepath.name] = filepath.name
            self.num += 1

    def downshift_numbered(self):
        # Shift down existing ordered files so new ones are added at the end
        nummax = self.num - 1
        for filepath in self.dirpath.iterdir():
            if not filepath.is_file() or filepath.suffix not in self.suffixes:
                continue

            try:
                filenum = int(filepath.stem)
            except ValueError:
                continue

            if filenum > nummax:
                nummax = filenum

        for filenum in range(self.num, nummax + 1):
            possible_names = tuple(
                self.dirpath / f"{filenum}{suffix}" for suffix in self.suffixes
            )
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
                    if (
                        name in self.metadata.order
                        or name in self.metadata.originals.values()
                    ):
                        try:
                            self.metadata.order.remove(name)
                        except ValueError:
                            pass
                        try:
                            original_index = tuple(
                                self.metadata.originals.values()
                            ).index(name)
                            original_key = tuple(self.metadata.originals.keys())[
                                original_index
                            ]
                            del self.metadata.originals[original_key]
                        except ValueError:
                            pass

                        break
                continue

            filepath = used_suffixes[0]
            self.move_file(filepath)
            self.num += 1
            if int(filepath.stem) == nummax:
                break

    def number_new_files(self):
        for filepath in self.dirpath.iterdir():
            if not filepath.is_file() or filepath.suffix not in self.suffixes:
                continue
            try:
                if int(filepath.stem) <= self.num:
                    continue
            except ValueError:
                pass

            self.move_file(filepath)
            self.num += 1

    def maybe_write_metadata(self):
        if not self.metadata:
            return

        self.metadata.max = self.num - 1
        if self.write_max:
            self.metadata.get_max().to_file(self.dirpath)
        if self.write_metadata:
            self.metadata.to_file(self.dirpath)
