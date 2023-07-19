import logging

from ._orchestrator import _NumberOrchestrator
from .metadata import FnumMetadata, FnumMax


__version__ = "1.6.0"

_log = logging.getLogger(__name__)


def number_files(
    dirpath, suffixes, write_metadata=False, write_max=False, include_imeta=False
):
    _log.info("Analyzing files...")
    orchestrator = _NumberOrchestrator(
        dirpath, suffixes, write_metadata, write_max, include_imeta
    )
    orchestrator.find_ordered()
    orchestrator.find_movable()

    _log.info("Processing files...")
    orchestrator.move_numbered()
    orchestrator.move_new()

    orchestrator.maybe_write_metadata()
