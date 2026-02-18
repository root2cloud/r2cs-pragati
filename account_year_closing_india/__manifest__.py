# -*- coding: utf-8 -*-
{
    'name': 'Indian Accounting: Year-End Closing',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Automated Transfer of P&L to Reserves & Surplus',
    'description': """
        Professional Year-End Closing Wizard for Indian Accounting Standards.

        Features:
        - Auto-fetches balances for custom P&L account types (Direct/Indirect Expenses, Revenue, etc.).
        - Generates a preview of the closing entry.
        - Posts a single Journal Entry to zero out Income/Expense.
        - Transfers Net Profit/Loss to the selected Reserves & Surplus account.
        - Tracks history via Chatter.
    """,
    'author': 'Your Organization',
    'website': '',
    'depends': ['account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',  # NEW: Sequence file
        'views/account_year_closing_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
