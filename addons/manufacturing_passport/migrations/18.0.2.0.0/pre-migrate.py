import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    _logger.info(
        "Renaming check_type -> parameter_type"
    )

    openupgrade.rename_columns(cr, {
        'mrp_qc_template_line': [('check_type', 'parameter_type')],
        'mrp_qc_inspection_line': [('check_type', 'parameter_type')],
    })

    _logger.info("Column rename completed")
