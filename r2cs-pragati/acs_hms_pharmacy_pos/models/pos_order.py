# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero


class PosOrder(models.Model):
    _inherit = 'pos.order' 

    pos_order_line_ids = fields.One2many('pos.order.line', 'prescription_order_origin_id', string="Order lines Transfered to Point of Sale", readonly=True, groups="point_of_sale.group_pos_user")
    currency_rate = fields.Float(compute='_compute_currency_rate', store=True, digits=0, readonly=True)
    prescription_order_count = fields.Integer(string='Prescription Order Count', compute='_count_prescription_order', readonly=True, groups="point_of_sale.group_pos_user")

    def _count_prescription_order(self):
        for order in self:
            order.prescription_order_count = len(order.lines.mapped('prescription_order_origin_id'))

    @api.depends('pricelist_id.currency_id', 'date_order', 'company_id')
    def _compute_currency_rate(self):
        for order in self:
            date_order = order.date_order or fields.Datetime.now()
            order.currency_rate = self.env['res.currency']._get_conversion_rate(order.company_id.currency_id, order.pricelist_id.currency_id, order.company_id, date_order)

    def _prepare_invoice_vals(self):
        invoice_vals = super(PosOrder, self)._prepare_invoice_vals()
        addr = self.partner_id.address_get(['delivery'])
        invoice_vals['partner_shipping_id'] = addr['delivery']
        return invoice_vals

    @api.model
    def create_from_ui(self, orders, draft=False):
        order_ids = super(PosOrder, self).create_from_ui(orders, draft)
        for order in self.sudo().browse([o['id'] for o in order_ids]):
            so_lines = order.lines.mapped('prescription_order_line_id')

            # update the demand qty in the stock moves related to the prescription order line
            # flush the qty_delivered to make sure the updated qty_delivered is used when
            # updating the demand value
            so_lines.flush_recordset(['qty_delivered'])
            # track the waiting pickings
            waiting_picking_ids = set()
            for so_line in so_lines:
                for stock_move in so_line.move_ids:
                    picking = stock_move.picking_id
                    if not picking.state in ['waiting', 'confirmed', 'assigned']:
                        continue
                    new_qty = so_line.product_uom_qty - so_line.qty_delivered
                    if float_compare(new_qty, 0, precision_rounding=stock_move.product_uom.rounding) <= 0:
                        new_qty = 0
                    stock_move.product_uom_qty = so_line.product_uom._compute_quantity(new_qty, stock_move.product_uom, False)
                    waiting_picking_ids.add(picking.id)

            def is_product_uom_qty_zero(move):
                return float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding)

            # cancel the waiting pickings if each product_uom_qty of move is zero
            for picking in self.env['stock.picking'].browse(waiting_picking_ids):
                if all(is_product_uom_qty_zero(move) for move in picking.move_ids):
                    picking.action_cancel()

        return order_ids

    def action_view_prescription_order(self):
        self.ensure_one()
        linked_orders = self.lines.mapped('prescription_order_origin_id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Linked Prescription Orders'),
            'res_model': 'prescription.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', linked_orders.ids)],
        }

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    prescription_order_origin_id = fields.Many2one('prescription.order', string="Linked Prescription Order")
    prescription_order_line_id = fields.Many2one('prescription.line', string="Source Prescription Order Line")
    acs_kit_details = fields.Text(string="Kit Details")

    def _export_for_ui(self, orderline):
        result = super()._export_for_ui(orderline)
        # NOTE We are not exporting 'prescription_order_line_id' because it is being used in any views in the POS App.
        result['acs_kit_details'] = bool(orderline.acs_kit_details) and orderline.acs_kit_details
        result['prescription_order_origin_id'] = bool(orderline.prescription_order_origin_id) and orderline.prescription_order_origin_id.read(fields=['name'])[0]
        return result

    def _order_line_fields(self, line, session_id):
        result = super()._order_line_fields(line, session_id)
        vals = result[2]
        if vals.get('prescription_order_origin_id', False):
            vals['prescription_order_origin_id'] = vals['prescription_order_origin_id']['id']
        if vals.get('prescription_order_line_id', False):
            vals['prescription_order_line_id'] = vals['prescription_order_line_id']['id']
        return result
