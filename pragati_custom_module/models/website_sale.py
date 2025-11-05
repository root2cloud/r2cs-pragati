from odoo import models, fields, api,tools, _

class Website(models.Model):
    _inherit = 'website'

    def _get_combination_info(self, product_template_id, product_id, combination, add_qty, pricelist):
        res = super(WebsiteSale, self)._get_combination_info(
            product_template_id, product_id, combination, add_qty, pricelist)

        product = self.env['product.product'].browse(product_id) if product_id else None
        if product:
            res.update({
                'unit_cost': product.unit_cost,
                'unit_name_value': product.unit_name_value,
                'product_uom_name': product.product_uom_name,
            })

        return res