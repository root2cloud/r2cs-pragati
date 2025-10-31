# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class PosOrder(models.Model):
    _inherit = 'pos.order'

    total_qty = fields.Float(
        string='Total Quantity',
        compute='_compute_total_qty',
        store=True,
        readonly=True
    )

    @api.depends('lines.qty')
    def _compute_total_qty(self):
        for order in self:
            order.total_qty = sum(line.qty for line in order.lines)

    def _generate_pos_order_invoice(self):
        moves = self.env['account.move']

        for order in self:
            # Force company for all SUPERUSER_ID action
            if order.account_move:
                moves += order.account_move
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            move_vals = order._prepare_invoice_vals()
            new_move = order._create_invoice(move_vals)

            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            new_move.sudo().with_company(order.company_id).with_context(skip_invoice_sync=True)._post()
            moves += new_move

            if 'Bill to Company' not in self.payment_ids.mapped('payment_method_id.name'):

                payment_moves = order._apply_invoice_payments()

                if order.session_id.state == 'closed':  # If the session isn't closed this isn't needed.
                    # If a client requires the invoice later, we need to revers the amount from the closing entry, by making a new entry for that.
                    order._create_misc_reversal_move(payment_moves)

        if not moves:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': moves and moves.ids[0] or False,
        }
