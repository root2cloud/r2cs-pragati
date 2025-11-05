from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # Computed fields for stock.quant model
    total_without_tax_value = fields.Float('Total Value without Tax', compute='_compute_total_value_and_mrp',
                                           store=False)

    unit_price = fields.Float('Unit Price', compute='_compute_unit_price', store=True)
    unit_price_without_tax = fields.Float('Unit Price without Tax', compute='_compute_unit_price_without_tax',
                                          store=True)


    def _compute_total_value_and_mrp(self):
        for quant in self:
            if quant.product_id:
                # Calculate total value without tax (Sales price * on-hand quantity)
                quant.total_without_tax_value = quant.product_id.lst_price * quant.inventory_quantity_auto_apply



    @api.depends('product_id.lst_price', 'product_id.taxes_id')
    def _compute_unit_price_without_tax(self):
        for quant in self:
            if quant.product_id:
                quant.unit_price_without_tax = quant.product_id.lst_price

    @api.depends('product_id.lst_price', 'product_id.taxes_id')
    def _compute_unit_price(self):
        for quant in self:
            if quant.product_id:
                unit_price_without_tax = quant.product_id.lst_price
                total_tax = sum(unit_price_without_tax * (tax.amount / 100) for tax in quant.product_id.taxes_id)
                quant.unit_price = unit_price_without_tax + total_tax