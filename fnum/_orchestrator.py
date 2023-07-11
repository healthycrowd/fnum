from pathlib import Path
from imeta import ImageMetadata

from .exceptions import FnumException
from .metadata import FnumMetadata


class NumRange:
    def __init__(self, start, end=None):
        self.start = start
        self.end = self.start if end is None else end
        self.next = None

    def __contains__(self, item):
        return self.start <= item <= self.end

    def __repr__(self):
        return str((self.start, self.end))

    def combine_next(self):
        if self.next and self.next.start == self.end + 1:
            self.end = self.next.end
            self.next = self.next.next

    def walk_add(self, other):
        if other == self.start - 1:
            self.start = other
            return self
        if other < self.start:
            newrange = self.__class__(other)
            newrange.next = self
            return newrange
        if other in self:
            return self
        if other == self.end + 1:
            self.end = other
            self.combine_next()
            return self
        if not self.next:
            newrange = self.__class__(other)
            self.next = newrange
            return self
        if other < self.next.start:
            newrange = self.__class__(other)
            newrange.next = self.next
            self.next = newrange
            return self
        self.next = self.next.walk_add(other)
        self.combine_next()
        return self


class NumRanges:
    def __init__(self):
        self.start = None

    def __iadd__(self, other):
        if not self.start:
            self.start = NumRange(other)
        else:
            self.start = self.start.walk_add(other)
        return self

    def __iter__(self):
        numrange = self.start
        while numrange:
            yield numrange
            numrange = numrange.next

    def __bool__(self):
        return self.start is not None

    def __repr__(self):
        return str(list(self))


class _NumberOrchestrator:
    num = 1
    metadata = None
    regen_meta = False
    new_ordered = None

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
        if self.metadata:
            numbered = NumRanges()
            numbered_names = {}
            self.new_ordered = []

            for name in self.metadata.order:
                try:
                    num = int(Path(name).stem)
                    numbered += num
                    numbered_names[num] = name
                except ValueError:
                    self.new_ordered.append(name)

            for numrange in numbered:
                if numrange.end < self.num:
                    continue
                for num in range(numrange.start, numrange.end + 1):
                    if num < self.num:
                        continue
                    original_key = tuple(self.metadata.originals.keys())[original_index]
                    self.metadata.originals[original_key] = numbered_names[num]
                    filepath = Path(self.dirpath / numbered_names[num])
                    self.move_file(filepath)
                    self.num += 1

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
