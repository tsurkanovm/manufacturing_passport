import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    _logger.info("Current version is %s. Start renaming state from %s to %s", version, 'in_progress', 'in_review')

    openupgrade.logged_query(
        cr,
        "UPDATE mrp_qc_inspection SET state = 'in_review' WHERE state = 'in_progress'",
    )

    _logger.info("Renaming state completed")
