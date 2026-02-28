# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

# --- DEFINE CUSTOM TYPES FOR MANUAL VALIDATION ---
CUSTOM_ACCOUNT_TYPES = [
    ("asset_receivable", "Receivable"),
    ("asset_cash", "Bank and Cash"),
    ("asset_current", "Current Assets"),
    ("asset_other_current", "Other Current Asset"),
    ("asset_non_current", "Non-current Assets"),
    ("asset_prepayments", "Prepayments"),
    ("asset_fixed", "Fixed Assets"),
    ("asset_prepaid_expenses", "Prepaid Expenses"),
    ("asset_control", "Control Account"),
    ("liability_payable", "Payable"),
    ("liability_credit_card", "Credit Card"),
    ("liability_current", "Current Liabilities"),
    ("liability_non_current", "Non-current Liabilities"),
    ("liability_loans_borrowings", "Loans & Borrowings"),
    ("liability_short_term_provision", "Short Term Provision"),
    ("equity", "Equity"),
    ("equity_capital_accounts", "Capital Accounts"),
    ("equity_unaffected", "Current Year Earnings"),
    ("income", "Revenue From Operations"),
    ("income_other", "Non - Operating Revenue"),
    ("expense", "Expenses"),
    ("expense_direct", "Direct Expense"),
    ("expense_indirect", "Indirect Expense"),
    ("expense_changes_inventory", "Changes In Inventory"),
    ("expense_depreciation", "Depreciation"),
    ("expense_direct_cost", "Cost of Revenue"),
    ("off_balance", "Off-Balance Sheet"),
]


class AccountYearClosing(models.Model):
    _name = 'account.year.closing'
    _description = 'Automated Fiscal Year Closing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_end desc, id desc'

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default='Draft')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Ready to Post'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company,
                                 readonly=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    fiscal_year_label = fields.Char(string="Fiscal Year Label", required=True, states={'posted': [('readonly', True)]},
                                    tracking=True)
    date_start = fields.Date(string='Start Date', required=True, states={'posted': [('readonly', True)]}, tracking=True)
    date_end = fields.Date(string='Closing Date', required=True, default=fields.Date.context_today,
                           states={'posted': [('readonly', True)]}, tracking=True)

    journal_id = fields.Many2one('account.journal', string='Closing Journal',
                                 default=lambda self: self.env['account.journal'].search(
                                     [('type', '=', 'general'), ('company_id', '=', self.env.company.id)], limit=1),
                                 required=True, readonly=True, states={'draft': [('readonly', False)]})

    retained_earnings_account_id = fields.Many2one('account.account', string='Reserves (Control A/c)',
                                                   domain="[('account_type', '=', 'asset_control'), ('company_id', '=', company_id)]",
                                                   required=True, states={'posted': [('readonly', True)]},
                                                   tracking=True)
    payment_narration = fields.Text(string="Narration", required=True,
                                    states={'posted': [('readonly', True)]}, tracking=True)

    # --- Financial Summary (Net Only) ---
    net_pl_amount = fields.Monetary(string="Net P&L", compute="_compute_financial_summary", store=True,
                                    currency_field='currency_id')
    net_pl_type = fields.Selection([('profit', 'Net Profit'), ('loss', 'Net Loss')], string="Result",
                                   compute="_compute_financial_summary", store=True)

    closing_line_ids = fields.One2many('account.year.closing.line', 'closing_id', string='Accounts to Close',
                                       states={'posted': [('readonly', True)]})
    move_id = fields.Many2one('account.move', string='Closing Entry', readonly=True, tracking=True)

    @api.depends('closing_line_ids.period_balance')
    def _compute_financial_summary(self):
        for record in self:
            net_balance = 0.0

            # Simple summation: Credits are negative, Debits are positive.
            # Summing them up automatically gives the Net Result.
            for line in record.closing_line_ids:
                net_balance += line.period_balance

            # If sum is Negative, it means Credits > Debits (Profit)
            # If sum is Positive, it means Debits > Credits (Loss)
            record.net_pl_amount = abs(net_balance)
            record.net_pl_type = 'profit' if net_balance <= 0 else 'loss'

    @api.model
    def default_get(self, fields_list):
        res = super(AccountYearClosing, self).default_get(fields_list)
        today = fields.Date.context_today(self)
        year = today.year
        if today.month < 4:
            res.update({'date_start': '%s-04-01' % (year - 1), 'date_end': '%s-03-31' % year,
                        'fiscal_year_label': 'FY %s-%s' % (year - 1, year)})
        else:
            res.update({'date_start': '%s-04-01' % year, 'date_end': '%s-03-31' % (year + 1),
                        'fiscal_year_label': 'FY %s-%s' % (year, year + 1)})
        return res

    @api.model
    def create(self, vals):
        if vals.get('name', 'Draft') == 'Draft':
            vals['name'] = self.env['ir.sequence'].next_by_code('account.year.closing') or 'FY-CLOSE/001'
        return super(AccountYearClosing, self).create(vals)

    def action_calculate_balances(self):
        self.ensure_one()
        self.closing_line_ids.unlink()

        pl_account_types = [
            "income", "income_other",
            "expense", "expense_direct", "expense_indirect",
            "expense_changes_inventory", "expense_depreciation", "expense_direct_cost"
        ]

        accounts = self.env['account.account'].search([
            ('company_id', '=', self.company_id.id),
            ('account_type', 'in', pl_account_types)
        ])

        if not accounts:
            raise UserError(_("No accounts found with the specified P&L types."))

        lines_to_create = []
        for account in accounts:
            domain = [
                ('account_id', '=', account.id),
                ('parent_state', '=', 'posted'),
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
                ('company_id', '=', self.company_id.id)
            ]

            result = self.env['account.move.line'].read_group(domain, ['balance'], ['account_id'])
            balance = result[0]['balance'] if result else 0.0
            count_result = self.env['account.move.line'].search_count(domain)

            if not float_is_zero(balance, precision_digits=self.currency_id.decimal_places):
                lines_to_create.append({
                    'closing_id': self.id,
                    'account_id': account.id,
                    'period_balance': balance,
                    'transaction_count': count_result
                })

        if not lines_to_create:
            raise UserError(_("No P&L movements found between %s and %s.") % (self.date_start, self.date_end))

        self.env['account.year.closing.line'].create(lines_to_create)
        self.state = 'calculated'

    def action_post_closing_entry(self):
        self.ensure_one()
        if not self.closing_line_ids:
            raise UserError(_("Please calculate balances first."))

        move_lines = []
        total_debit_created = 0
        total_credit_created = 0

        for line in self.closing_line_ids:
            balance = line.period_balance
            if float_is_zero(balance, precision_digits=self.currency_id.decimal_places):
                continue

            if balance > 0:
                vals = {'debit': 0.0, 'credit': balance}
                total_credit_created += balance
            else:
                vals = {'debit': abs(balance), 'credit': 0.0}
                total_debit_created += abs(balance)

            vals.update({
                'account_id': line.account_id.id,
                'name': _("Closing: %s") % line.account_id.name,
            })
            move_lines.append((0, 0, vals))

        net_diff = total_debit_created - total_credit_created
        if not float_is_zero(net_diff, precision_digits=self.currency_id.decimal_places):
            res_vals = {
                'account_id': self.retained_earnings_account_id.id,
                'name': _("Net Profit/Loss Transfer: %s") % self.fiscal_year_label,
            }
            if net_diff > 0:
                res_vals.update({'debit': 0.0, 'credit': net_diff})
            else:
                res_vals.update({'debit': abs(net_diff), 'credit': 0.0})
            move_lines.append((0, 0, res_vals))

        ref_val = f"{self.name} - {self.payment_narration}" if self.payment_narration else self.name

        move = self.env['account.move'].create({
            'name':self.name,
            'ref': self.name,
            'date': self.date_end,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'move_type': 'entry',
            'is_closing_entry': True,  # <--- ADD THIS LINE
            'payment_narration': self.payment_narration,
            'line_ids': move_lines,
        })
        move.action_post()
        self.move_id = move.id
        self.state = 'posted'

    def action_reset_draft(self):
        self.ensure_one()
        if self.move_id and self.move_id.state == 'posted':
            try:
                self.move_id.button_draft()
            except UserError as e:
                raise UserError(_("Cannot reset to draft: The linked Journal Entry is locked.\n%s") % str(e))
        self.state = 'draft'

    def action_view_move(self):
        self.ensure_one()
        return {
            'name': _('Closing Entry'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'type': 'ir.actions.act_window',
        }


class AccountYearClosingLine(models.Model):
    _name = 'account.year.closing.line'
    _description = 'Year Closing Preview Line'
    _order = 'account_type, account_id'

    closing_id = fields.Many2one('account.year.closing', string='Closing Reference', ondelete='cascade')
    account_id = fields.Many2one('account.account', string='Account', required=True)

    account_type = fields.Selection(selection=CUSTOM_ACCOUNT_TYPES, string="Type", compute='_compute_account_type',
                                    store=True, readonly=True)

    transaction_count = fields.Integer(string="Trans. Count", readonly=True)
    period_balance = fields.Monetary(string='Net Balance (Signed)', currency_field='currency_id')
    amount_display = fields.Monetary(string='Balance Amount', compute='_compute_display', currency_field='currency_id')
    dr_cr_display = fields.Selection([('dr', 'Dr'), ('cr', 'Cr')], string='Dr/Cr', compute='_compute_display')
    currency_id = fields.Many2one('res.currency', related='closing_id.company_id.currency_id')

    @api.depends('account_id')
    def _compute_account_type(self):
        for line in self:
            line.account_type = line.account_id.account_type

    @api.depends('period_balance')
    def _compute_display(self):
        for line in self:
            if line.period_balance >= 0:
                line.amount_display = line.period_balance
                line.dr_cr_display = 'dr'
            else:
                line.amount_display = abs(line.period_balance)
                line.dr_cr_display = 'cr'


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_closing_entry = fields.Boolean(string='Is Year Closing Entry', default=False, copy=False)
