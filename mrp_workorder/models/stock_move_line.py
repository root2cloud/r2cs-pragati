# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    quality_check_ids = fields.One2many('quality.check', 'move_line_id', string='Check')

    def _without_quality_checks(self):
        self.ensure_one()
        return not self.quality_check_ids

    historical_cost_price = fields.Float(
        string='Cost Price',
        compute='_compute_historical_prices',
        store=True,
        digits='Product Price'
    )

    historical_sale_price = fields.Float(
        string='Sale Price',
        compute='_compute_historical_prices',
        store=True,
        digits='Product Price'
    )

    # @api.depends('state', 'move_id.state')
    # def _compute_historical_prices(self):
    #     for line in self:
    #         if line.state == 'done' or line.move_id.state == 'done':
    #
    #             # 1. COST PRICE LOGIC
    #             if not line.historical_cost_price:
    #                 # FIRST PRIORITY: Check for a Valuation Layer (unit_cost)
    #                 val_layer = line.move_id.stock_valuation_layer_ids
    #                 if val_layer and val_layer[0].unit_cost != 0:
    #                     line.historical_cost_price = abs(val_layer[0].unit_cost)
    #                 else:
    #                     # SECOND PRIORITY: Fallback to the 'Cost' field on the product card
    #                     # This is what captures the value for Internal Transfers
    #                     line.historical_cost_price = line.product_id.unit_cost
    #
    #             # 2. SALE PRICE LOGIC (Already working)
    #             if not line.historical_sale_price:
    #                 sale_line = line.move_id.sale_line_id
    #                 line.historical_sale_price = sale_line.price_unit if sale_line else line.product_id.lst_price
