import logging

from ._orchestrator import _NumberOrchestrator
from .metadata import FnumMetadata, FnumMax


__version__ = "1.4.0"

_log = logging.getLogger(__name__)


def number_files(
    dirpath, suffixes, write_metadata=False, write_max=False, include_imeta=False
):
    _log.info("Analyzing files...")
    orchestrator = _NumberOrchestrator(
        dirpath, suffixes, write_metadata, write_max, include_imeta
    )
    orchestrator.find_ordered()
    orchestrator.downshift_numbered()
    _log.info("Processing files...")
    orchestrator.number_new_files()
    orchestrator.maybe_write_metadata()
    return orchestrator.metadata
