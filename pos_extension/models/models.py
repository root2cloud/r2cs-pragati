# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools import format_amount


class PosOrder(models.Model):
    _inherit = "pos.order"

    sub_total = fields.Float(string='Sub Total')
    

    def write(self, values):
        # Check to prevent recursion
       
           
        if 'sub_total' not in values:
            # Compute the sub_total; replace with your actual logic
            sub_total = sum(line.price_subtotal for line in self.lines)

            
            values.update({'sub_total': sub_total})
        
        # Call the parent class's write method
        return super(PosOrder, self).write(values)

    # def write(self, values):
    #     res = super().write(values)
    #     if not values.get('sub_total'):
    #         sub_total = 0.0
    #         for line in self.lines:
    #             if self.session_id.config_id.discount_product_id.id != line.product_id.id:
    #                 sub_total += line.price_unit * line.qty
    #         self.write({'sub_total':sub_total})
    #     return res

class PosConfig(models.Model):
    _inherit = 'pos.config'

    discount_product_id = fields.Many2one('product.product', string='Dis Product')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'



    mrp_price = fields.Float(string='M.R.P',compute="_get_mrp_price",store=True,readonly=True)

    @api.depends('product_id','product_id.taxes_id','product_id.list_price')
    def _get_mrp_price(self):
        for record in self:
            record.mrp_price = record._construct_tax_string_mrp(record.product_id.list_price)

    def _construct_tax_string_mrp(self, price):
        # Ensure we pass the product record, not the ID
        product = self.product_id
        partner = self.env['res.partner']
        res = product.taxes_id.compute_all(price, product=product, partner=partner)
        included = res['total_included']
        print("pppppppppppppppppppp", res, included)
        return included





