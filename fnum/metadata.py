from pathlib import Path
from collections import OrderedDict
import yaml


class FnumMetadata:
    _FIELDS = ["order", "originals", "max"]
    _FILENAME = "fnum.metadata.yaml"

    def __init__(self, data):
        self._raw_data = data
        for field in self._FIELDS:
            setattr(self, field, data.get(field))

    @classmethod
    def from_str(cls, data_str):
        data = yaml.safe_load(data_str)
        return cls(data)

    @classmethod
    def from_file(cls, dirpath):
        data_str = (Path(dirpath) / cls._FILENAME).read_text()
        return cls.from_str(data_str)

    @classmethod
    def get_default(cls):
        return FnumMetadata(
            {
                "order": [],
                "originals": {},
                "max": None,
            }
        )

    def get_max(self):
        return FnumMax(self.max)

    def __iter__(self):
        data = OrderedDict()
        for field in self._FIELDS:
            data[field] = getattr(self, field)
        for key in self._raw_data.keys():
            if key not in data:
                data[key] = self._raw_data[key]
        return data.items().__iter__()

    def __repr__(self):
        data_str = yaml.safe_dump(dict(self))
        return data_str

    def to_file(self, dirpath):
        data_str = str(self)
        (Path(dirpath) / self._FILENAME).write_text(data_str)


class FnumMax:
    _FILENAME = "fnum.max.yaml"

    def __init__(self, value):
        self.value = value

    @classmethod
    def from_str(cls, value_str):
        return cls(int(value_str))

    @classmethod
    def from_file(cls, dirpath):
        value_str = (Path(dirpath) / cls._FILENAME).read_text()
        return cls.from_str(value_str)

    def __repr__(self):
        return str(self.value)

    def to_file(self, dirpath):
        value_str = str(self)
        (Path(dirpath) / self._FILENAME).write_text(value_str)
