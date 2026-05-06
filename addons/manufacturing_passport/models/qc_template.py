from odoo import fields, models


class MrpQcTemplate(models.Model):
    _name = 'mrp.qc.template'
    _description = 'Шаблон перевірки якості'
    _order = 'name'

    name = fields.Char(string='Назва шаблону', required=True)
    active = fields.Boolean(string='Активний', default=True)
    product_id = fields.Many2one('product.product', string='Продукт')
    bom_id = fields.Many2one('mrp.bom', string='Специфікація')
    line_ids = fields.One2many('mrp.qc.template.line', 'template_id', string='Параметри перевірки')
    note = fields.Html(string='Нотатки')


class MrpQcTemplateLine(models.Model):
    _name = 'mrp.qc.template.line'
    _description = 'Рядок шаблону перевірки якості'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'mrp.qc.template', string='Шаблон', required=True, ondelete='cascade',
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
    min_value = fields.Float(string='Мін. значення')
    max_value = fields.Float(string='Макс. значення')
    note = fields.Text(string='Інструкції інспектору')
