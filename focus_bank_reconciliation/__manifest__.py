# -*- coding: utf-8 -*-
{
    'name': 'Focus Style Bank Reconciliation',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Custom Bank Receipts, Payments, and Manual Reconciliation Console',
    'description': """
        This module implements a professional, high-UI bank reconciliation workflow 
        similar to Focus ERP software.

        Key Features:
        1. Dedicated Customer Bank Receipts Screen.
        2. Dedicated Vendor Bank Payments Screen.
        3. "Focus-Style" Reconciliation Console with Tick-and-Tie logic.
        4. Real-time Book vs. Bank Balance calculation.
        5. Professional Reconciliation Reports.
    """,
    'author': 'Your Company Name',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',

        # 'views/customer_receipt_view.xml',
        'views/bank_reconciliation_console_view.xml',
        # 'report/bank_reconciliation_report.xml'
        'views/bank_reconciliation_statement_view.xml',
        'views/account_move_view.xml',
        # 'views/account_payment_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # We will add custom CSS here later for the "High UI" look
            'focus_bank_reconciliation/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
