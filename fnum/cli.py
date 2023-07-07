import sys
import click

from . import __version__, number_files
from .exceptions import FnumException


@click.command(
    help="""
Renames files in a directory to be named using sequential integers starting with 1.\n
Suffixes is a comma separated list of file extensions to rename (eg. .jpg,.gif).\n
Dirpath is a directory to rename files in.
""",
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.argument("suffixes", nargs=1)
@click.argument("dirpath", nargs=1)
@click.version_option(version=__version__)
@click.option(
    "--write-max/--no-write-max",
    default=False,
    help="""
Write a file named fnum.max.txt containing the highest number used in a filename.\n
This is useful for being able to list or paginate numbered files when listing the files is not otherwise possible (such as on a static website).
    """,
)
@click.option(
    "--write-metadata/--no-write-metadata",
    default=False,
    help="""
Writes a file named fnum.metadata.yaml containing data about what was changed.\n
Max is the highest number used in a filename.\n
Order contains a list of filenames in the order they were added. Newly added files are added to the end of the list when the command is run multiple times.\n
Originals maps the original filenames to what they were renamed to.
    """,
)
def cli(**kwargs):
    dirpath = kwargs["dirpath"]
    suffixes = kwargs["suffixes"].split(",")
    try:
        metadata = number_files(
            dirpath=dirpath, suffixes=suffixes, progressbar=click.progressbar
        )
    except FnumException as e:
        click.echo(str(e))
        sys.exit(1)

    if kwargs["write_max"]:
        metadata.get_max().to_file(dirpath)
    if kwargs["write_metadata"]:
        metadata.to_file(dirpath)
