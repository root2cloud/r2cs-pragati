# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json


class BankReconciliationConsole(models.Model):
    _name = 'bank.reconciliation.console'
    _description = 'Bank Reconciliation Screen'
    _rec_name = 'bank_journal_id'

    # --- Configuration ---
    bank_journal_id = fields.Many2one('account.journal', string='Select Bank', domain=[('type', '=', 'bank')],
                                      required=True)
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    search_text = fields.Char(string="Search")

    # --- Filters ---
    transaction_type = fields.Selection([
        ('all', 'All Transactions'),
        ('debit', 'Debits Only (Receipts)'),
        ('credit', 'Credits Only (Payments)')
    ], string='Show Type', default='all', required=True)

    status_filter = fields.Selection([
        ('pending', 'Pending Only'),
        ('cleared', 'Cleared Only'),
        ('all', 'Show All (History)')
    ], string='Status', default='pending', required=True)

    # --- Data Lines ---
    line_ids = fields.Many2many(
        'account.move.line',
        string='Transactions',
        relation='bank_console_line_rel',
        column1='console_id',
        column2='line_id'
    )

    # --- SUMMARY FIELDS ---

    # Group 1: Book
    book_balance = fields.Monetary(string='Book Balance', readonly=True)
    opening_balance = fields.Monetary(string='Opening Balance', readonly=True)

    # Group 2: Uncleared Receipts (Money we have in Books, but not in Bank yet)
    uncleared_debit_amount = fields.Monetary(string='Receipts', readonly=True)
    uncleared_debit_count = fields.Integer(string='Debits Count', readonly=True)

    # Group 3: Unpresented Payments (Money we spent in Books, but Bank hasn't paid yet)
    uncleared_credit_amount = fields.Monetary(string='Payments', readonly=True)
    uncleared_credit_count = fields.Integer(string='Credits Count', readonly=True)

    # Group 4: Totals
    cleared_balance = fields.Monetary(string='Cleared Balance', readonly=True,
                                      help="Book Balance - Uncleared Receipts + Unpresented Payments")

    balance_end_real = fields.Monetary(string='Bank Balance')

    # Difference (Computed always)
    unreconciled_variance = fields.Monetary(string='Difference', compute='_compute_diff')

    @api.onchange('transaction_type', 'status_filter', 'bank_journal_id', 'date_from', 'date_to', 'search_text')
    def _onchange_clear_list(self):
        """ Reset fields when filters change """
        self.line_ids = [(5, 0, 0)]
        self.book_balance = 0
        self.opening_balance = 0
        self.uncleared_debit_amount = 0
        self.uncleared_debit_count = 0
        self.uncleared_credit_amount = 0
        self.uncleared_credit_count = 0
        self.cleared_balance = 0
        # Do not reset balance_end_real so user doesn't lose their input

    def action_load_transactions(self):
        self.ensure_one()
        # 1. IDENTIFY ACCOUNT (Only Default Bank Account)
        target_account = self.bank_journal_id.default_account_id
        if not target_account:
            raise UserError(f"Journal '{self.bank_journal_id.name}' has no Bank Account set.")

        self.currency_id = self.bank_journal_id.currency_id or self.env.company.currency_id

        # ---------------------------------------------------------
        # 1. CALCULATE OPENING BALANCE (Cumulative < Date From)
        # ---------------------------------------------------------
        # Sum of all posted moves BEFORE the start date
        opening_lines = self.env['account.move.line'].search([
            ('account_id', '=', target_account.id),
            ('date', '<', self.date_from),
            ('parent_state', '=', 'posted')
        ])
        self.opening_balance = sum(opening_lines.mapped('balance'))

        # ---------------------------------------------------------
        # 2. GET RANGE LINES (Date From <= Date <= Date To)
        # ---------------------------------------------------------
        range_lines = self.env['account.move.line'].search([
            ('account_id', '=', target_account.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted')
        ])

        # ---------------------------------------------------------
        # 3. CALCULATE BOOK BALANCE (Opening + Range Activity)
        # ---------------------------------------------------------
        # This matches the GL "Closing Balance" as of 'date_to'
        activity_in_range = sum(range_lines.mapped('balance'))
        self.book_balance = self.opening_balance + activity_in_range

        # ---------------------------------------------------------
        # 4. CALCULATE "OUT" ITEMS (Uncleared/Pending in Range)
        # ---------------------------------------------------------
        u_debits = range_lines.filtered(lambda r: r.debit > 0)
        u_credits = range_lines.filtered(lambda r: r.credit > 0)

        self.uncleared_debit_amount = sum(u_debits.mapped('debit'))
        self.uncleared_debit_count = len(u_debits)

        self.uncleared_credit_amount = sum(u_credits.mapped('credit'))
        self.uncleared_credit_count = len(u_credits)

        # ---------------------------------------------------------
        # 5. CALCULATE CLEARED BALANCE (Logic Adjustment)
        # ---------------------------------------------------------
        # Cleared Balance = Opening Balance + (Cleared Debits - Cleared Credits in Range)
        cleared_in_range = range_lines.filtered(lambda r: r.is_brs_cleared)
        cleared_debits = sum(cleared_in_range.mapped('debit'))
        cleared_credits = sum(cleared_in_range.mapped('credit'))

        self.cleared_balance = self.opening_balance + (cleared_debits - cleared_credits)

        # ---------------------------------------------------------
        # 6. LOAD VISUAL LIST
        # ---------------------------------------------------------
        domain = [
            ('account_id', '=', target_account.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
        ]

        if self.transaction_type == 'debit':
            domain.append(('debit', '>', 0))
        elif self.transaction_type == 'credit':
            domain.append(('credit', '>', 0))

        if self.status_filter == 'pending':
            domain.append(('is_brs_cleared', '=', False))
        elif self.status_filter == 'cleared':
            domain.append(('is_brs_cleared', '=', True))

        if self.search_text:
            domain += ['|', '|', '|',
                       ('cheque_number', 'ilike', self.search_text),
                       ('name', 'ilike', self.search_text),
                       ('ref', 'ilike', self.search_text),
                       ('partner_id.name', 'ilike', self.search_text)]

        transactions = self.env['account.move.line'].search(domain).sorted(key=lambda r: r.date)

        # Update Serial Numbers via SQL (Single Account ID)
        if transactions:
            self.env.cr.execute("UPDATE account_move_line SET brs_serial_no=0 WHERE account_id=%s",
                                (target_account.id,))

            for i, line_id in enumerate(transactions.ids, start=1):
                self.env.cr.execute("UPDATE account_move_line SET brs_serial_no=%s WHERE id=%s", (i, line_id))

        self.line_ids = [(6, 0, transactions.ids)]
        return True

    def action_recalculate_balances(self):
        return self.action_load_transactions()

    @api.depends('cleared_balance', 'balance_end_real')
    def _compute_diff(self):
        for rec in self:
            rec.unreconciled_variance = rec.balance_end_real - rec.cleared_balance

    def action_print_pdf(self):
        """ Triggers the QWeb PDF Report """
        self.ensure_one()
        # This reference must match the ID in your XML file (step 4 below)
        return self.env.ref('focus_bank_reconciliation.action_report_bank_reconciliation').report_action(self)

    def action_print_excel(self):
        """ Triggers the Excel Report logic """
        self.ensure_one()
        # This calls the abstract model we will create in Step 3
        return self.env['report.focus_bank_reconciliation.report_bank_xlsx'].create_xlsx_report(self)
