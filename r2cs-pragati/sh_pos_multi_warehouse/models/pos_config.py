# Copyright (C) Softhealer Technologies.
from odoo import fields, models

class PosConfig(models.Model):
    _inherit = 'pos.config'

    sh_enable_multi_warehouse = fields.Boolean(string="Enable Multi Warehouse")
    sh_picking_sate = fields.Boolean("Ready State")
    sh_negative_selling = fields.Boolean("Enable Negative Selling")
    sh_warehouse_tags = fields.Many2many(
        'stock.warehouse', string="Choose Related Warehouse")
    sh_stock_type = fields.Selection([('available_quantity', 'Available Quantity'), ('available_quantity_unreserved',
                                                                                     'Available Quantity Unreserved')], string="Stock Type", default='available_quantity', required=True)
