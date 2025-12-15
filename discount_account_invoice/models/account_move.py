# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

import logging

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError
from odoo.tools import frozendict, formatLang, format_date, float_is_zero, float_compare
import functools
from contextlib import ExitStack, contextmanager
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _compute_taxes_for_single_line(self, base_line, handle_price_include=True, include_caba_tags=False,
                                       early_pay_discount_computation=None, early_pay_discount_percentage=None):
        line = base_line['record']
        if line and line._name == "account.move.line":
            orig_price_unit_after_discount = base_line['price_unit'] * (1 - (base_line['discount'] / 100.0))
            if line.discount_type and line.discount_type == 'fixed':
                orig_price_unit_after_discount = base_line['price_unit'] - base_line['discount'] / base_line['quantity']
            if line.global_discount_percent:
                if line.global_discount_amount:
                    orig_price_unit_after_discount = orig_price_unit_after_discount - line.global_discount_amount / \
                                                     base_line['quantity']
                else:
                    orig_price_unit_after_discount = orig_price_unit_after_discount * (
                                1 - float(line.global_discount_percent))
            price_unit_after_discount = orig_price_unit_after_discount
            taxes = base_line['taxes']._origin
            currency = base_line['currency'] or self.env.company.currency_id
            rate = base_line['rate']

            if early_pay_discount_computation in ('included', 'excluded'):
                remaining_part_to_consider = (100 - early_pay_discount_percentage) / 100.0
                price_unit_after_discount = remaining_part_to_consider * price_unit_after_discount

            if taxes:

                if handle_price_include is None:
                    manage_price_include = bool(base_line['handle_price_include'])
                else:
                    manage_price_include = handle_price_include

                taxes_res = taxes.with_context(**base_line['extra_context']).compute_all(
                    price_unit_after_discount,
                    currency=currency,
                    quantity=base_line['quantity'],
                    product=base_line['product'],
                    partner=base_line['partner'],
                    is_refund=base_line['is_refund'],
                    handle_price_include=manage_price_include,
                    include_caba_tags=include_caba_tags,
                )

                to_update_vals = {
                    'tax_tag_ids': [Command.set(taxes_res['base_tags'])],
                    'price_subtotal': taxes_res['total_excluded'],
                    'price_total': taxes_res['total_included'],
                }

                if early_pay_discount_computation == 'excluded':
                    new_taxes_res = taxes.with_context(**base_line['extra_context']).compute_all(
                        orig_price_unit_after_discount,
                        currency=currency,
                        quantity=base_line['quantity'],
                        product=base_line['product'],
                        partner=base_line['partner'],
                        is_refund=base_line['is_refund'],
                        handle_price_include=manage_price_include,
                        include_caba_tags=include_caba_tags,
                    )
                    for tax_res, new_taxes_res in zip(taxes_res['taxes'], new_taxes_res['taxes']):
                        delta_tax = new_taxes_res['amount'] - tax_res['amount']
                        tax_res['amount'] += delta_tax
                        to_update_vals['price_total'] += delta_tax

                tax_values_list = []
                for tax_res in taxes_res['taxes']:
                    tax_amount = tax_res['amount'] / rate
                    if self.company_id.tax_calculation_rounding_method == 'round_per_line':
                        tax_amount = currency.round(tax_amount)
                    tax_rep = self.env['account.tax.repartition.line'].browse(tax_res['tax_repartition_line_id'])
                    tax_values_list.append({
                        **tax_res,
                        'tax_repartition_line': tax_rep,
                        'base_amount_currency': tax_res['base'],
                        'base_amount': currency.round(tax_res['base'] / rate),
                        'tax_amount_currency': tax_res['amount'],
                        'tax_amount': tax_amount,
                    })

            else:
                price_subtotal = currency.round(price_unit_after_discount * base_line['quantity'])
                to_update_vals = {
                    'tax_tag_ids': [Command.clear()],
                    'price_subtotal': price_subtotal,
                    'price_total': price_subtotal,
                }
                tax_values_list = []

            return to_update_vals, tax_values_list
        return super(AccountTax, self)._compute_taxes_for_single_line(base_line, handle_price_include=True,
                                                                      include_caba_tags=False,
                                                                      early_pay_discount_computation=None,
                                                                      early_pay_discount_percentage=None)


class AccountMove(models.Model):
    _inherit = "account.move"

    master_total_amount = fields.Monetary("Total Invoice Amount", compute="_compute_master_total")

    def _compute_master_total(self):
        for rec in self:
            rec.master_total_amount = rec.total_discount + rec.amount_untaxed

    def remove_global_discount(self):
        if self.invoice_line_ids:
            self.invoice_line_ids.write({
                'global_discount_percent': '',
                'global_discount_amount': 0
            })
            self.is_global_discount_applied = False
            self.global_order_discount = 0
            self.invoice_line_ids._compute_totals()
            self._compute_amount()

    def action_update_discount(self):

        if self.invoice_line_ids:
            if not self.global_order_discount:
                self.invoice_line_ids.write({
                    'global_discount_percent': '',
                    'global_discount_amount': 0
                })
                self.is_global_discount_applied = False
            elif self.global_discount_type == 'percent':
                if self.global_order_discount > 100 or self.global_order_discount < 0:
                    raise ValidationError("Please enter the valid discount")
                self.invoice_line_ids.write({
                    'global_discount_percent': str(self.global_order_discount / 100),
                    'global_discount_amount': 0

                })
                self.is_global_discount_applied = True

            else:

                total_amount = 0
                for line in self.invoice_line_ids:
                    discount_type = ''
                    discount_type = line.discount_type
                    quantity = line.quantity
                    if discount_type == 'fixed':
                        line_discount_price_unit = line.price_unit * line.quantity - line.discount
                        quantity = 1.0
                    else:
                        line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
                    total_amount += line_discount_price_unit * quantity
                if total_amount < self.global_order_discount:
                    raise ValidationError("Discount can't be greater than the invoice total amount")
                self.is_global_discount_applied = True
                self.invoice_line_ids.write({
                    'global_discount_percent': str(self.global_order_discount / total_amount),
                    'global_discount_amount': 0
                })
            self.invoice_line_ids._compute_totals()
            self._compute_amount()
            self._compute_tax_totals()
            self._recompute_cash_rounding_lines()

    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
        'currency_id',
    )
    def _compute_tax_totals(self):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        for move in self:
            # move.tax_totals = None
            if move.is_invoice(include_receipts=True):
                base_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
                base_line_values_list = [line._convert_to_tax_base_line_dict() for line in base_lines]
                if move.id:
                    # The invoice is stored so we can add the early payment discount lines directly to reduce the
                    # tax amount without touching the untaxed amount.
                    sign = -1 if move.is_inbound(include_receipts=True) else 1
                    base_line_values_list += [
                        {
                            **line._convert_to_tax_base_line_dict(),
                            'handle_price_include': False,
                            'quantity': 1.0,
                            'price_unit': sign * line.amount_currency,
                        }
                        for line in move.line_ids.filtered(lambda line: line.display_type == 'epd')
                    ]

                kwargs = {
                    'base_lines': base_line_values_list,
                    'currency': move.currency_id,
                }

                if move.id:
                    kwargs['tax_lines'] = [
                        line._convert_to_tax_line_dict()
                        for line in move.line_ids.filtered(lambda line: line.display_type == 'tax')
                    ]
                else:
                    # In case the invoice isn't yet stored, the early payment discount lines are not there. Then,
                    # we need to simulate them.
                    epd_aggregated_values = {}
                    for base_line in base_lines:
                        if not base_line.epd_needed:
                            continue
                        for grouping_dict, values in base_line.epd_needed.items():
                            epd_values = epd_aggregated_values.setdefault(grouping_dict, {'price_subtotal': 0.0})
                            epd_values['price_subtotal'] += values['price_subtotal']

                    for grouping_dict, values in epd_aggregated_values.items():
                        taxes = None
                        if grouping_dict.get('tax_ids'):
                            taxes = self.env['account.tax'].browse(grouping_dict['tax_ids'][0][2])

                        kwargs['base_lines'].append(self.env['account.tax']._convert_to_tax_base_line_dict(
                            None,
                            partner=move.partner_id,
                            currency=move.currency_id,
                            taxes=taxes,
                            price_unit=values['price_subtotal'],
                            quantity=1.0,
                            account=self.env['account.account'].browse(grouping_dict['account_id']),
                            analytic_distribution=values.get('analytic_distribution'),
                            price_subtotal=values['price_subtotal'],
                            is_refund=move.move_type in ('out_refund', 'in_refund'),
                            handle_price_include=False,
                        ))
                move.tax_totals = self.env['account.tax']._prepare_tax_totals(**kwargs)
                move._recompute_cash_rounding_lines()
            else:
                # Non-invoice moves don't support that field (because of multicurrency: all lines of the invoice share the same currency)
                move.tax_totals = None

    @api.depends('line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
                 'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
                 'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
                 'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
                 'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
                 'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
                 'line_ids.debit',
                 'line_ids.credit',
                 'line_ids.currency_id',
                 'line_ids.amount_currency',
                 'line_ids.amount_residual',
                 'line_ids.amount_residual_currency',
                 'line_ids.payment_id.state',
                 'line_ids.full_reconcile_id', )
    def _compute_amount(self):
        res = super(AccountMove, self)._compute_amount()
        for move in self:
            total_global_discount = 0.0
            total_discount = 0.0
            global_discount = 0.0
            global_discount_currency = 0.0
            currencies = move._get_lines_onchange_currency().currency_id

            for line in move.line_ids:
                if move.is_invoice(True):
                    if line.global_discount_amount:
                        global_discount += line.global_discount_amount
                        global_discount_currency += line.global_discount_amount
                    if line.display_type in ('product', 'rounding'):
                        total_discount += line.discount if line.discount_type == 'fixed' else line.quantity * line.price_unit * line.discount / 100.0

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            total_global_discount = -1 * sign * (global_discount_currency if len(
                currencies) == 1 else global_discount)
            total_discount += abs(total_global_discount)
            move.total_global_discount = total_global_discount
            move.total_discount = total_discount
        return res

    total_global_discount = fields.Monetary(string='Total Global Discount',
                                            store=True, default=0, compute='_compute_amount')
    total_discount = fields.Monetary(string='Total Discount', store=True,
                                     default=0, compute='_compute_amount', tracking=True)
    global_discount_type = fields.Selection([('fixed', 'Fixed'),
                                             ('percent', 'Percent')],
                                            string="Discount Type", default="percent", tracking=True)
    global_order_discount = fields.Float(string='Global Discount', store=True, tracking=True)
    is_global_discount_applied = fields.Boolean("Is Global Discount Appliend", default=False)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    global_discount_percent = fields.Char("Global Discount Percentage")
    global_discount_amount = fields.Float("Global Discount Amount")
    discount_type = fields.Selection([('fixed', 'Fixed'),
                                      ('percent', 'Percent')],
                                     string="Discount Type", default="percent")
    is_global_line = fields.Boolean(string='Global Discount Line',
                                    help="This field is used to separate global discount line.")

    display_type = fields.Selection(
        selection_add=[('gd', 'Global Discount')],
        ondelete={'gd': lambda records: records.write({'display_type': 'product'})},
    )

    @api.onchange('discount_type', 'discount')
    def onchange_discount_validation(self):
        for line in self:
            if line.discount_type and line.discount:
                if line.discount_type == 'percent' and line.discount > 100:
                    raise ValidationError("Discount can be greater than 100 percent")
                elif line.discount_type == 'fixed' and line.discount > line.price_subtotal:
                    raise ValidationError("Discount can be greater than line subtotal price")

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        for line in self:
            if line.display_type != 'product':
                line.price_total = line.price_subtotal = False
            # Compute 'price_subtotal'.
            # line.global_discount_amount = 0
            line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            if line.discount_type and line.discount_type == 'fixed':
                line_discount_price_unit = line.price_unit - line.discount / line.quantity
            if line.global_discount_percent:
                if line.global_discount_amount:
                    line_discount_price_unit = line_discount_price_unit - line.global_discount_amount / line.quantity
                else:
                    line.global_discount_amount = line_discount_price_unit * float(
                        line.global_discount_percent) * line.quantity
                    line_discount_price_unit = line_discount_price_unit * (1 - float(line.global_discount_percent))
            subtotal = line.quantity * line_discount_price_unit

            # Compute 'price_total'.
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )
                line.price_subtotal = taxes_res['total_excluded']
                line.price_total = taxes_res['total_included']
            else:
                line.price_total = line.price_subtotal = subtotal

    @api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id',
                 'move_id.partner_id', 'price_unit')
    def _compute_all_tax(self):
        for line in self:
            sign = line.move_id.direction_sign
            if line.display_type == 'tax':
                line.compute_all_tax = {}
                line.compute_all_tax_dirty = False
                continue
            if line.display_type == 'product' and line.move_id.is_invoice(True):
                amount_currency = line.price_unit * (1 - line.discount / 100)
                if line.discount_type and line.discount_type == 'fixed':
                    amount_currency = (line.price_unit - line.discount / line.quantity)
                if line.global_discount_percent:
                    if line.global_discount_amount:
                        amount_currency = amount_currency - line.global_discount_amount / line.quantity
                    else:
                        amount_currency = amount_currency * (1 - float(line.global_discount_percent))
                amount_currency = sign * amount_currency
                handle_price_include = True
                quantity = line.quantity
            else:
                amount_currency = line.amount_currency
                handle_price_include = False
                quantity = 1
            compute_all_currency = line.tax_ids.compute_all(
                amount_currency,
                currency=line.currency_id,
                quantity=quantity,
                product=line.product_id,
                partner=line.move_id.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=line.move_id.always_tax_exigible,
                fixed_multiplicator=sign,
            )
            rate = line.amount_currency / line.balance if line.balance else 1
            line.compute_all_tax_dirty = True
            line.compute_all_tax = {
                frozendict({
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'group_tax_id': tax['group'] and tax['group'].id or False,
                    'account_id': tax['account_id'] or line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'analytic_distribution': (tax['analytic'] or not tax[
                        'use_in_tax_closing']) and line.analytic_distribution,
                    'tax_ids': [(6, 0, tax['tax_ids'])],
                    'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                    'partner_id': line.move_id.partner_id.id or line.partner_id.id,
                    'move_id': line.move_id.id,
                }): {
                    'name': tax['name'],
                    'balance': tax['amount'] / rate,
                    'amount_currency': tax['amount'],
                    'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
                }
                for tax in compute_all_currency['taxes']
                if tax['amount']
            }
            if not line.tax_repartition_line_id:
                line.compute_all_tax[frozendict({'id': line.id})] = {
                    'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
                }
