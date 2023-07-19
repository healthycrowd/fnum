from click.testing import CliRunner
import pytest

from fnum.cli import cli
from fnum.metadata import FnumMetadata, FnumMax

from .number import make_files, temp_dir, assert_numbered_dir


SUCCESS_OUTPUT = """Analyzing files...
Processing files...
"""


@pytest.mark.parametrize("file_count", [n for n in range(6)])
def test_cli_success(file_count):
    runner = CliRunner()
    test_files = [
        chr(ord("a") + n) + (".txt" if n % 2 == 0 else ".text")
        for n in range(file_count)
    ]

    with temp_dir(test_files) as dirpath:
        result = runner.invoke(
            cli,
            [
                ".txt,.text",
                str(dirpath),
                "--write-max",
                "--write-metadata",
                "--include-imeta",
            ],
        )
        assert result.exit_code == 0
        assert result.output == SUCCESS_OUTPUT
        assert_numbered_dir(test_files, dirpath)

        fmax = FnumMax.from_file(str(dirpath))
        assert fmax.value == len(test_files)

        metadata = FnumMetadata.from_file(str(dirpath))
        assert all(
            (f"{num}.txt" in metadata.order or f"{num}.text" in metadata.order)
            for num in range(1, len(test_files) + 1)
        )
        assert len(metadata.order) == len(test_files)
        assert all(filename in metadata.originals.keys() for filename in test_files)
        assert all(
            (
                f"{num}.txt" in metadata.originals.values()
                or f"{num}.text" in metadata.originals.values()
            )
            for num in range(1, len(test_files) + 1)
        )
        assert metadata.max == len(test_files)


def test_cli_success_verbose():
    runner = CliRunner()
    file_count = 5
    test_files = [
        chr(ord("a") + n) + (".txt" if n % 2 == 0 else ".text")
        for n in range(file_count)
    ]

    with temp_dir(test_files) as dirpath:
        result = runner.invoke(
            cli,
            [
                ".txt,.text",
                str(dirpath),
                "--write-max",
                "--write-metadata",
                "--include-imeta",
                "--verbose",
            ],
        )
        assert result.exit_code == 0
        assert len(result.output) > len(SUCCESS_OUTPUT)


def test_cli_fnumexception():
    runner = CliRunner()
    test_files = ["1.txt", "1.text"]

    with temp_dir(test_files) as dirpath:
        result = runner.invoke(cli, [".txt,.text", str(dirpath)])
        assert result.exit_code == 1
        assert result.output != ""
