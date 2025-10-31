# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    location_id = fields.Many2one('stock.location', string="Location")
    
    @api.model
    def _order_line_fields(self, line, session_id=None):
        res = super(PosOrderLine, self)._order_line_fields(line,session_id)
        line[2]['location_id'] = line[2]['location_id']
        if line[2].get('refunded_orderline_id'):
            orderline = self.search([('id','=',line[2].get('refunded_orderline_id'))])
            if orderline and orderline.location_id:
                res[2]['location_id'] = orderline.location_id.id
        return res
