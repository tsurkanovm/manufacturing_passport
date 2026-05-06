from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class MrpQcInspection(models.Model):
    _name = 'mrp.qc.inspection'
    _description = 'Акт випробувань'
    _order = 'inspection_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Номер', readonly=True, default='/', copy=False)
    state = fields.Selection(
        selection=[
            ('draft', 'Чернетка'),
            ('in_review', 'В процесі'),
            ('done', 'Завершено'),
            ('approved', 'Затверджено'),
            ('rejected', 'Відхилено'),
        ],
        string='Статус',
        default='draft',
        required=True,
        tracking=True,
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Виробниче замовлення',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Продукт',
        related='production_id.product_id',
        store=True,
        readonly=True,
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Серійний номер / партія',
        domain="[('product_id', '=', product_id)]",
    )
    template_id = fields.Many2one('mrp.qc.template', string='Шаблон перевірки')
    line_ids = fields.One2many(
        'mrp.qc.inspection.line', 'inspection_id', string='Результати перевірки',
    )
    inspector_id = fields.Many2one(
        'res.users',
        string='Інспектор',
        default=lambda self: self.env.user,
        tracking=True,
    )
    inspection_date = fields.Date(
        string='Дата перевірки',
        default=fields.Date.today,
    )
    approved_by = fields.Many2one(
        'res.users', string='Затверджено', readonly=True, tracking=True,
    )
    approved_date = fields.Datetime(string='Дата затвердження', readonly=True)
    result = fields.Selection(
        selection=[
            ('pass', 'Придатний'),
            ('fail', 'Непридатний'),
            ('conditional', 'Умовно придатний'),
        ],
        string='Результат',
        tracking=True,
    )
    note = fields.Text(string='Висновок')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'mrp_qc_inspection_attachment_rel',
        'inspection_id',
        'attachment_id',
        string='Вкладення',
    )

    completion_rate = fields.Float(
        string='Відсоток виконання',
        default=0.0,
        compute='_compute_completion_rate',
        store=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('mrp.qc.inspection') or '/'
                )
        return super().create(vals_list)

    def action_start(self):
        self.write({'state': 'in_progress'})
        return True

    def action_done(self):
        for record in self:
            if not record.result:
                raise UserError(_('Будь ласка, вкажіть загальний результат перевірки перед завершенням.'))
        self.write({'state': 'done'})
        return True

    def action_approve(self):
        for record in self:
            if not record.result:
                raise UserError(_('Неможливо затвердити акт без вказаного результату.'))
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })
        return True

    def action_reject(self):
        self.write({'state': 'rejected'})
        return True

    def action_reset_draft(self):
        self.write({'state': 'draft', 'approved_by': False, 'approved_date': False})
        return True

    def action_print_inspection(self):
        self.ensure_one()
        return self.env.ref('manufacturing_passport.action_report_qc_inspection').report_action(self)

    @api.depends('line_ids', 'line_ids.line_result')
    def _compute_completion_rate(self):
        for record in self:
            total = len(record.line_ids)
            not_checked = len(record.line_ids.filtered(
                lambda line: line.line_result == 'not_checked')
            )

            record.completion_rate = (total - not_checked) / total if total else 0.0


    @api.onchange('template_id')
    def _onchange_template_id(self):
        if not self.template_id or self.line_ids:
            return
        self.line_ids = [
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
            for tmpl_line in self.template_id.line_ids
        ]

    @api.onchange('line_ids')
    def _onchange_line_ids(self): #todo - now it set pass if some rows not checked, but it should be fail
        checked = [
            line.line_result
            for line in self.line_ids
            if line.line_result != 'not_checked'
        ]
        if not checked:
            return
        if all(r == 'pass' for r in checked):
            self.result = 'pass'
        elif any(r == 'fail' for r in checked):
            self.result = 'fail'


class MrpQcInspectionLine(models.Model):
    _name = 'mrp.qc.inspection.line'
    _description = 'Рядок акту випробувань'
    _order = 'sequence, id'

    inspection_id = fields.Many2one(
        'mrp.qc.inspection',
        string='Акт перевірки',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Порядок', default=10)
    name = fields.Char(string='Параметр', required=True)
    parameter_type = fields.Selection(
        selection=[('quantitative', 'Кількісний'), ('qualitative', 'Якісний')],
        string='Тип перевірки',
        default='quantitative',
        required=True,
    )
    method = fields.Char(string='Метод вимірювання')
    uom = fields.Char(string='Одиниця виміру')
    min_value = fields.Float(string='Мін. норма', digits=(16, 4))
    max_value = fields.Float(string='Макс. норма', digits=(16, 4))
    actual_value = fields.Float(string='Фактичне значення', digits=(16, 4))
    qualitative_result = fields.Text(string='Результат (якісний)')
    line_result = fields.Selection(
        selection=[
            ('pass', 'Придатний'),
            ('fail', 'Непридатний'),
            ('not_checked', 'Не перевірено'),
        ],
        string='Результат',
        default='not_checked',
    )
    note = fields.Text(string='Примітка інспектора')

    @api.onchange('actual_value', 'min_value', 'max_value')
    def _onchange_actual_value(self):
        if self.parameter_type != 'quantitative':
            return
        # Skip auto-determination when range is unconfigured (both defaults at 0)
        if self.min_value == 0.0 and self.max_value == 0.0:
            return
        if self.min_value <= self.actual_value <= self.max_value:
            self.line_result = 'pass'
        else:
            self.line_result = 'fail'
