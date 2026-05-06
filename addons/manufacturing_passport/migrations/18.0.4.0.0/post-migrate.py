import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info(
        "Start adding new 'completion_rate' field to 'mrp.qc.inspection'"
    )

    # do not use direct SQL query, this way more precise and safer,
    # and we have only a few inspection records
    records = env['mrp.qc.inspection'].search([])
    field = env['mrp.qc.inspection']._fields['completion_rate']
    env.add_to_compute(field, records)
    records._recompute_field(field)

_logger.info(
        "Field 'completion_rate' added to 'mrp.qc.inspection'"
    )
