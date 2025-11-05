from odoo import models, fields

class MrpWorkcenterCapacity(models.Model):
    _name = 'mrp.workcenter.capacity'
    _description = 'Workcenter Product Capacity'

    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Work Center',
        ondelete='cascade',
        required=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure'
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='UoM',
        required=True
    )
    time_start = fields.Float(string='Start Time')
    time_stop = fields.Float(string='Stop Time')
    capacity = fields.Float(string="Capacity per Hour")
