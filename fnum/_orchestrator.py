import logging
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
            intiter = iter(range(numrange.start, numrange.end + 1))
            try:
                while True:
                    yield next(intiter)
            except StopIteration:
                pass
            numrange = numrange.next

    def __bool__(self):
        return self.start is not None

    def __repr__(self):
        return str(list(self))


class _NumberOrchestrator:
    num = 1
    metadata = None
    regen_meta = False

    ordered_ranges = None
    ordered_files = None
    unordered_ranges = None
    unordered_files = None
    new_files = None
    removed_files = None

    log = None

    def __init__(self, dirpath, suffixes, write_metadata, write_max, include_imeta):
        self.log = logging.getLogger(__name__)

        self.dirpath = Path(dirpath)
        self.suffixes = suffixes
        self.write_metadata = write_metadata
        self.write_max = write_max
        self.include_imeta = include_imeta

        try:
            self.metadata = FnumMetadata.from_file(dirpath)
        except FileNotFoundError:
            if self.write_metadata or self.write_max:
                self.metadata = FnumMetadata.get_default()
                self.regen_meta = True

    def numpath(self, suffix):
        return self.dirpath / (str(self.num) + suffix)

    def move_file(self, filepath):
        newpath = self.numpath(filepath.suffix)
        self.log.debug(f"Renaming {filepath.name} to {newpath.name}")
        if newpath.exists():
            raise FnumException(
                f"Can't override existing file {newpath.name} while renaming {filepath.name}"
            )

        if self.metadata:
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
        self.num += 1

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

    def find_movable(self):
        self.ordered_ranges = NumRanges()
        self.ordered_files = {}
        self.unordered_ranges = NumRanges()
        self.unordered_files = {}
        self.new_files = []
        self.removed_files = []
        self.log.debug(f"Numbering will start from {self.num}")

        # Find files in metadata file's order
        if self.metadata:
            for name in self.metadata.order:
                filepath = self.dirpath / name
                if filepath.exists():
                    try:
                        num = int(Path(name).stem)
                        if num >= self.num:
                            self.ordered_ranges += num
                            self.ordered_files[num] = filepath
                    except ValueError:
                        self.new_files.append(filepath)
                    continue

                self.log.debug(f"Missing {name}, removing from metadata")
                self.removed_files.append(name)

        for filepath in self.dirpath.iterdir():
            if not filepath.is_file() or filepath.suffix not in self.suffixes:
                continue

            try:
                num = int(filepath.stem)
                if num >= self.num and num not in self.ordered_files:
                    self.unordered_ranges += num
                    self.unordered_files[num] = filepath
            except ValueError:
                if filepath not in self.new_files:
                    self.new_files.append(filepath)

    def move_numbered(self):
        for num in self.ordered_ranges:
            self.move_file(self.ordered_files[num])
        for num in self.unordered_ranges:
            self.move_file(self.unordered_files[num])

    def move_new(self):
        for filepath in self.new_files:
            self.move_file(filepath)

    def maybe_write_metadata(self):
        if not self.metadata:
            return

        for name in self.removed_files:
            try:
                self.metadata.order.remove(name)
            except ValueError:
                pass
            try:
                original_index = tuple(self.metadata.originals.values()).index(name)
                original_key = tuple(self.metadata.originals.keys())[original_index]
                del self.metadata.originals[original_key]
            except ValueError:
                pass

        self.metadata.max = self.num - 1
        if self.write_max:
            self.metadata.get_max().to_file(self.dirpath)
        if self.write_metadata:
            self.metadata.to_file(self.dirpath)
