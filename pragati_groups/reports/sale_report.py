# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class LoyaltySaleReport(models.Model):
    _name = "loyalty.sale.report"
    _description = 'Loyalty Sale Report'

    loyalty_program_id = fields.Many2one('loyalty.program', string="Program Name", readonly=True)
    product_id = fields.Many2one('product.product',string="Product", readonly=True)
    order_id = fields.Many2one('sale.order', string='Order', readonly=True)
    partner_id = fields.Many2one('res.partner', string='User', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    qty = fields.Float(string='Qty', readonly=True)
    mobile = fields.Char(string='Mobile', readonly=True)
    location = fields.Char(string='Location', readonly=True)
    used_coupon_code = fields.Char(string='Used Coupon Code', readonly=True)
    salesperson_id = fields.Many2one('res.users', 'Salesperson', readonly=True)

