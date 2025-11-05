from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    account_type = fields.Selection(
                selection=[
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

            # ("income", "Income"),
            # ("income_other", "Other Income"),
            ("income", "Revenue From Operations"),
            ("income_other", "Non - Operating Revenue"),

            ("expense", "Expenses"),
            ("expense_direct", "Direct Expense"),
            ("expense_indirect", "Indirect Expense"),
            ("expense_changes_inventory", "Changes In Inventory"),
            ("expense_depreciation", "Depreciation"),
            ("expense_direct_cost", "Cost of Revenue"),

            ("off_balance", "Off-Balance Sheet"),
        ],
        string='Type',
        required=True,
        help='Account type used for reports and fiscal year closure'
    )

