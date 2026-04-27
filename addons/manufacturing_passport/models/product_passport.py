from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class MrpProductPassport(models.Model):
    _name = 'mrp.product.passport'
    _description = 'Паспорт виробу'
    _order = 'date_issued desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Номер', readonly=True, default='/', copy=False)
    company_id = fields.Many2one(
        'res.company',
        string='Компанія',
        default=lambda self: self.env.company,
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Чернетка'),
            ('issued', 'Видано'),
            ('cancelled', 'Анульовано'),
        ],
        string='Статус',
        default='draft',
        required=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Продукт',
        required=True,
        tracking=True,
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Серійний номер',
        domain="[('product_id', '=', product_id)]",
        tracking=True,
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Виробниче замовлення',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    inspection_id = fields.Many2one(
        'mrp.qc.inspection',
        string='Акт перевірки',
        domain="[('production_id', '=', production_id), ('state', '=', 'approved')]",
    )
    date_manufactured = fields.Date(string='Дата виготовлення')
    date_issued = fields.Date(string='Дата видачі паспорта', default=fields.Date.today)
    warranty_months = fields.Integer(string='Гарантійний термін (місяці)', default=12)
    warranty_end = fields.Date(
        string='Гарантія до',
        compute='_compute_warranty_end',
        store=True,
    )
    issued_by = fields.Many2one(
        'res.users',
        string='Видав',
        default=lambda self: self.env.user,
    )
    component_line_ids = fields.One2many(
        'mrp.passport.component.line',
        'passport_id',
        string='Комплектуючі',
    )
    note = fields.Text(string='Примітки')

    @api.depends('date_manufactured', 'warranty_months')
    def _compute_warranty_end(self):
        for record in self:
            if record.date_manufactured and record.warranty_months:
                record.warranty_end = record.date_manufactured + relativedelta(
                    months=record.warranty_months
                )
            else:
                record.warranty_end = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('mrp.product.passport') or '/'
                )
        return super().create(vals_list)

    def action_issue(self):
        for record in self:
            if not record.lot_id:
                raise UserError(
                    _('Необхідно вказати серійний номер перед видачею паспорта.')
                )
        self.write({'state': 'issued', 'date_issued': fields.Date.today()})
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True

    def action_print_passport(self):
        self.ensure_one()
        return self.env.ref(
            'manufacturing_passport.action_report_product_passport'
        ).report_action(self)


class MrpPassportComponentLine(models.Model):
    _name = 'mrp.passport.component.line'
    _description = 'Рядок комплектуючих паспорта'
    _order = 'id'

    passport_id = fields.Many2one(
        'mrp.product.passport',
        string='Паспорт',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one('product.product', string='Комплектуюча', required=True)
    lot_id = fields.Many2one('stock.lot', string='Серійний номер / партія')
    quantity = fields.Float(string='Кількість', digits=(16, 4))
    uom_id = fields.Many2one('uom.uom', string='Одиниця виміру')
