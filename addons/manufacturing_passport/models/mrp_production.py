from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    inspection_ids = fields.One2many(
        'mrp.qc.inspection', 'production_id', string='Акти перевірки',
    )
    inspection_count = fields.Integer(
        string='Кількість актів перевірки',
        compute='_compute_inspection_count',
    )
    passport_ids = fields.One2many(
        'mrp.product.passport', 'production_id', string='Паспорти',
    )
    passport_count = fields.Integer(
        string='Кількість паспортів',
        compute='_compute_passport_count',
    )
    has_approved_inspection = fields.Boolean(
        compute='_compute_has_approved_inspection',
    )
    has_issued_passport = fields.Boolean(
        compute='_compute_has_issued_passport',
    )

    @api.depends('inspection_ids')
    def _compute_inspection_count(self):
        for record in self:
            record.inspection_count = len(record.inspection_ids)

    @api.depends('passport_ids')
    def _compute_passport_count(self):
        for record in self:
            record.passport_count = len(record.passport_ids)

    @api.depends('inspection_ids.state')
    def _compute_has_approved_inspection(self):
        for record in self:
            record.has_approved_inspection = any(
                i.state == 'approved' for i in record.inspection_ids
            )

    @api.depends('passport_ids.state')
    def _compute_has_issued_passport(self):
        for record in self:
            record.has_issued_passport = any(
                p.state == 'issued' for p in record.passport_ids
            )

    def action_view_inspections(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Акти перевірки'),
            'res_model': 'mrp.qc.inspection',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {'default_production_id': self.id},
        }

    def action_view_passports(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Паспорти виробів'),
            'res_model': 'mrp.product.passport',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {'default_production_id': self.id},
        }

    def action_create_inspection(self):
        self.ensure_one()
        if self.has_approved_inspection:
            raise UserError(
                _('Для цього замовлення вже є затверджений акт перевірки.')
            )
        template = self.env['mrp.qc.template'].search(
            [('product_id', '=', self.product_id.id), ('active', '=', True)],
            limit=1,
        )
        lot_id = self.lot_producing_id.id if self.lot_producing_id else False

        lines = []
        if template:
            lines = [
                fields.Command.create({
                    'sequence': tmpl_line.sequence,
                    'name': tmpl_line.name,
                    'method': tmpl_line.method,
                    'uom': tmpl_line.uom,
                    'min_value': tmpl_line.min_value,
                    'max_value': tmpl_line.max_value,
                    'parameter_type': tmpl_line.parameter_type,
                    'note': tmpl_line.note,
                })
                for tmpl_line in template.line_ids
            ]

        inspection = self.env['mrp.qc.inspection'].create({
            'production_id': self.id,
            'lot_id': lot_id,
            'template_id': template.id if template else False,
            'line_ids': lines,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Акт перевірки'),
            'res_model': 'mrp.qc.inspection',
            'view_mode': 'form',
            'res_id': inspection.id,
        }

    def action_create_passport(self):
        self.ensure_one()
        if self.has_issued_passport:
            raise UserError(
                _('Для цього замовлення вже видано паспорт виробу.')
            )
        approved_inspection = self.inspection_ids.filtered(
            lambda i: i.state == 'approved'
        )
        if not approved_inspection:
            raise UserError(
                _('Неможливо створити паспорт: немає затвердженого акту перевірки для цього замовлення.')
            )

        component_lines = []
        for move in self.move_raw_ids.filtered(lambda m: m.state == 'done'):
            for move_line in move.move_line_ids:
                component_lines.append(fields.Command.create({
                    'product_id': move_line.product_id.id,
                    'lot_id': move_line.lot_id.id if move_line.lot_id else False,
                    'quantity': move_line.quantity,
                    'uom_id': move_line.product_uom_id.id,
                }))

        date_manufactured = (
            self.date_finished.date() if self.date_finished else fields.Date.today()
        )

        passport = self.env['mrp.product.passport'].create({
            'production_id': self.id,
            'product_id': self.product_id.id,
            'lot_id': self.lot_producing_id.id if self.lot_producing_id else False,
            'inspection_id': approved_inspection[0].id,
            'date_manufactured': date_manufactured,
            'component_line_ids': component_lines,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Паспорт виробу'),
            'res_model': 'mrp.product.passport',
            'view_mode': 'form',
            'res_id': passport.id,
        }
