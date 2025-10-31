from odoo import models, fields, api


class SlotsDescription(models.Model):
    _name = 'slots.description'
    _rec_name = 'slot_name'

    slot_name = fields.Char(string="Slot Name")
    plan_id = fields.Many2one("membership.planning",string="Plan Name")

    family_membership_id = fields.Many2one("member.ship",string="Family Membership")
    total_amount = fields.Float(string='Total',compute='_compute_total',)
    product_line_ids = fields.One2many('product.line', 'slots_description_id', string='Slot Details',copy=True)

    @api.depends('product_line_ids.price_subtotal')
    def _compute_total(self):
        for slots_description in self:
            total_amount = sum(slots_description.product_line_ids.mapped('price_subtotal'))
            slots_description.total_amount = total_amount


class ProductLine(models.Model):
    _name = 'product.line'

    product_id = fields.Many2one("product.product", string="Products",copy=True)
    quantity = fields.Float(string="Quantity",copy=True)
    uom = fields.Many2one('uom.uom', string='UOM')
    uom_name = fields.Char(string='UOMs', related='uom.name')
    price_unit = fields.Float(string="Unit price",copy=True)
    price_subtotal = fields.Float(string='SubTotal',compute='_compute_price_subtotal', store=True,copy=True)
    slots_description_id = fields.Many2one('slots.description', string='Slots Description') 
    editable = fields.Boolean(string="Editable", default=False)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.uom_name = self.product_id.uom_id.id
            self.price_unit = self.product_id.list_price

    @api.depends('quantity','price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity*line.price_unit

    


