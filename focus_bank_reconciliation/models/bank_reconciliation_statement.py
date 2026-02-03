# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class BankReconciliationStatementView(models.TransientModel):
    _name = 'bank.reconciliation.statement.view'
    _description = 'Bank Reconciliation Statement Console'
    _rec_name = 'bank_journal_id'

    # --- Inputs ---
    bank_journal_id = fields.Many2one('account.journal', string='Bank Account', domain=[('type', '=', 'bank')],
                                      required=True)
    # NEW: Date Range Selection
    date_range_option = fields.Selection([
        ('custom', 'Date Range'),
        ('as_on_date', 'As on Date'),
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'Current Week'),
        ('prev_week', 'Previous Week'),
        ('this_month', 'Current Month'),
        ('prev_month', 'Previous Month'),
        ('this_quarter', 'Current Quarter'),
        ('prev_quarter', 'Previous Quarter'),
        ('this_year', 'Current Year'),
        ('prev_year', 'Previous Year'),
        ('this_fy', 'Current Financial Year'),
        ('prev_fy', 'Previous Financial Year'),
    ], string='Date Range', default='this_month', required=True)

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.context_today)

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='bank_journal_id.currency_id')

    # --- Table Data ---
    line_ids = fields.One2many('bank.reconciliation.statement.line', 'statement_id', string='Statement Lines')
    book_balance = fields.Monetary(string='Book Balance', readonly=True)
    bank_balance = fields.Monetary(string='Bank Balance', readonly=True)

    # --- LOGIC TO AUTO-FILL DATES ---
    @api.onchange('date_range_option')
    def _onchange_date_range_option(self):
        today = date.today()

        # 1. AS ON DATE (From Beginning -> Today)
        if self.date_range_option == 'as_on_date':
            self.date_from = False
            self.date_to = today

        # 2. CUSTOM (User decides)
        elif self.date_range_option == 'custom':
            pass  # Do nothing

        # 3. PRESETS (Fill both dates)
        elif self.date_range_option == 'today':
            self.date_from = today
            self.date_to = today

        elif self.date_range_option == 'yesterday':
            yesterday = today - timedelta(days=1)
            self.date_from = yesterday
            self.date_to = yesterday

        elif self.date_range_option == 'this_week':
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            self.date_from = start
            self.date_to = end

        elif self.date_range_option == 'prev_week':
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            self.date_from = start
            self.date_to = end

        elif self.date_range_option == 'this_month':
            self.date_from = today.replace(day=1)
            self.date_to = today.replace(day=1) + relativedelta(months=1, days=-1)

        elif self.date_range_option == 'prev_month':
            end = today.replace(day=1) - timedelta(days=1)
            start = end.replace(day=1)
            self.date_from = start
            self.date_to = end

        elif self.date_range_option == 'this_quarter':
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            self.date_from = today.replace(month=start_month, day=1)
            self.date_to = self.date_from + relativedelta(months=3, days=-1)

        elif self.date_range_option == 'prev_quarter':
            quarter = (today.month - 1) // 3 + 1
            prev_q_end = today.replace(month=((quarter - 1) * 3 + 1), day=1) - timedelta(days=1)
            self.date_from = prev_q_end.replace(day=1) - relativedelta(months=2)
            self.date_to = prev_q_end

        elif self.date_range_option == 'this_year':
            self.date_from = today.replace(month=1, day=1)
            self.date_to = today.replace(month=12, day=31)

        elif self.date_range_option == 'prev_year':
            self.date_from = today.replace(year=today.year - 1, month=1, day=1)
            self.date_to = today.replace(year=today.year - 1, month=12, day=31)

        elif self.date_range_option == 'this_fy':
            if today.month < 4:
                start = date(today.year - 1, 4, 1)
                end = date(today.year, 3, 31)
            else:
                start = date(today.year, 4, 1)
                end = date(today.year + 1, 3, 31)
            self.date_from = start
            self.date_to = end

        elif self.date_range_option == 'prev_fy':
            if today.month < 4:
                start = date(today.year - 2, 4, 1)
                end = date(today.year - 1, 3, 31)
            else:
                start = date(today.year - 1, 4, 1)
                end = date(today.year, 3, 31)
            self.date_from = start
            self.date_to = end

    def _populate_lines(self):
        """ Core logic to calculate and create lines (Reusable) """
        self.ensure_one()
        target_account = self.bank_journal_id.default_account_id
        if not target_account:
            raise UserError(_("Please configure a Default Account on the selected Journal."))

        # 1. Calculate Book Balance (As of End Date)
        closing_lines = self.env['account.move.line'].search([
            ('account_id', '=', target_account.id),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted')
        ])
        start_balance = sum(closing_lines.mapped('balance'))
        self.book_balance = start_balance

        # 2. Find Pending Items (Uncleared)
        domain = [
            ('account_id', '=', target_account.id),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
            '|',
            ('is_brs_cleared', '=', False),
            ('brs_clearance_date', '>', self.date_to)
        ]
        if self.date_from:
            domain.append(('date', '>=', self.date_from))

        uncleared_items = self.env['account.move.line'].search(domain).sorted(key=lambda r: r.date)

        # 3. BUILD TABLE
        lines_to_create = []

        # Start with Book Balance
        running_bal = start_balance

        total_debit = 0.0
        total_credit = 0.0
        row_num = 1

        # A. HEADER ROW
        lines_to_create.append({
            'statement_id': self.id,
            'sequence': 0,
            'serial_no': row_num,
            'move_name': 'Balance as per Books',
            'debit': 0,
            'credit': 0,
            'running_balance': running_bal,
            'is_bold': True,
            'is_balance_row': True,
        })
        row_num += 1

        # B. TRANSACTION ROWS
        seq = 1
        for move in uncleared_items:
            # --- FIX 1: REVERSED LOGIC (Book -> Bank) ---
            # Uncleared Debit (Receipt): Deduct because it's in Book but not Bank.
            # Uncleared Credit (Payment): Add because it's deducted from Book but still in Bank.
            running_bal = running_bal - move.debit + move.credit

            total_debit += move.debit
            total_credit += move.credit

            # Note: We DO NOT sum running_bal into a 'total_balance_sum' anymore.

            narration_text = move.narration or move.ref or move.name
            if narration_text == '/':
                narration_text = move.move_id.name

            lines_to_create.append({
                'statement_id': self.id,
                'sequence': seq,
                'serial_no': row_num,
                'date': move.date,
                'move_name': move.move_id.name or move.name,
                'account_name': move.brs_counterpart_account or move.partner_id.name,
                'debit': move.debit,
                'credit': move.credit,
                'running_balance': running_bal,
                'narration': narration_text,
                'reconciled_str': str(move.is_brs_cleared),
                'is_bold': False,
            })
            seq += 1
            row_num += 1

        # C. FOOTER ROW
        self.bank_balance = running_bal  # Final result
        lines_to_create.append({
            'statement_id': self.id,
            'sequence': seq + 1,
            'serial_no': row_num,
            'move_name': 'Balance as per Bank',
            'debit': 0,
            'credit': 0,
            'running_balance': running_bal,
            'is_bold': True,
            'is_balance_row': True,
        })
        row_num += 1

        # D. GRAND TOTAL ROW
        lines_to_create.append({
            'statement_id': self.id,
            'sequence': seq + 2,
            'serial_no': row_num,
            'move_name': 'Grand Total',
            'debit': total_debit,
            'credit': total_credit,
            'running_balance': 0,  # --- FIX 2: Set to 0 (or empty) ---
            'narration': '',
            'reconciled_str': '',
            'is_bold': True,
            'is_balance_row': False,
        })

        # Clear old and create new
        self.line_ids.unlink()
        self.env['bank.reconciliation.statement.line'].create(lines_to_create)

    def action_load_statement(self):
        """ Opens the new window """
        self._populate_lines()
        return {
            'name': _('Reconciliation Statement'),
            'type': 'ir.actions.act_window',
            'res_model': 'bank.reconciliation.statement.view',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('focus_bank_reconciliation.view_bank_reconciliation_statement_result').id,
            'target': 'current',
        }

    def action_reload(self):
        """ Refreshes the data instantly """
        self._populate_lines()
        # This tag tells Odoo to simply reload the form data without closing/opening windows
        return True


class BankReconciliationStatementLine(models.TransientModel):
    _name = 'bank.reconciliation.statement.line'
    _description = 'BRS Report Line'
    _order = 'sequence, id'

    statement_id = fields.Many2one('bank.reconciliation.statement.view', ondelete='cascade')
    sequence = fields.Integer()
    serial_no = fields.Integer(string='#')
    date = fields.Date(string='Date')
    move_name = fields.Char(string='Voucher')
    account_name = fields.Char(string='Account')

    debit = fields.Monetary(string='Debit')
    credit = fields.Monetary(string='Credit')

    running_balance = fields.Monetary(string='Balance')

    narration = fields.Char(string='Narration')
    reconciled_str = fields.Char(string='Reconciled')

    is_bold = fields.Boolean(default=False)
    is_balance_row = fields.Boolean(default=False)

    currency_id = fields.Many2one('res.currency', related='statement_id.currency_id')
