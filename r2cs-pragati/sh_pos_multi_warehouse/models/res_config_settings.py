# Copyright (C) Softhealer Technologies.
from odoo import fields, models

class ResConfigSettingInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_sh_enable_multi_warehouse = fields.Boolean(related="pos_config_id.sh_enable_multi_warehouse", string="Enable Multi Warehouse", readonly=False)
    pos_sh_picking_sate = fields.Boolean(related="pos_config_id.sh_picking_sate", string="Ready State", readonly=False)
    pos_sh_negative_selling = fields.Boolean(related="pos_config_id.sh_negative_selling", string="Enable Negative Selling", readonly=False)
    pos_sh_warehouse_tags = fields.Many2many(
        'stock.warehouse', related="pos_config_id.sh_warehouse_tags", string="Choose Related Warehouse", readonly=False)
    pos_sh_stock_type = fields.Selection([('available_quantity', 'Available Quantity'), ('available_quantity_unreserved',
                                                                                     'Available Quantity Unreserved')],related="pos_config_id.sh_stock_type", string="Stock Type", default='available_quantity', required=True, readonly=False)
