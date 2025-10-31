# -*- coding: utf-8 -*-

import calendar
import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, api, tools
from odoo.http import request


class DashBoard(models.Model):
    _inherit = 'account.move'

    def get_current_company_value(self):
        """Optimized company retrieval with caching"""
        cookies_cids = [int(r) for r in request.httprequest.cookies.get('cids').split(",")] \
            if request.httprequest.cookies.get('cids') \
            else [request.env.user.company_id.id]

        for company_id in cookies_cids:
            if company_id not in self.env.user.company_ids.ids:
                cookies_cids.remove(company_id)
        if not cookies_cids:
            cookies_cids = [self.env.company.id]
        if len(cookies_cids) == 1:
            cookies_cids.append(0)
        return cookies_cids

    @api.model
    def get_income_this_year(self, *post):
        """Optimized income data retrieval for current year"""
        company_id = self.get_current_company_value()

        # Generate month list once
        month_list = []
        for i in range(11, -1, -1):
            l_month = datetime.now() - relativedelta(months=i)
            text = format(l_month, '%B')
            month_list.append(text)

        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        # Single optimized query using JOIN and CASE statements
        query = """
            SELECT 
                TO_CHAR(aml.date, 'Month') as month,
                SUM(CASE WHEN aa.internal_group = 'income' THEN aml.debit - aml.credit ELSE 0 END) as income,
                SUM(CASE WHEN aa.internal_group = 'expense' THEN aml.debit - aml.credit ELSE 0 END) as expense
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group IN ('income', 'expense')
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
                AND {}
            GROUP BY TO_CHAR(aml.date, 'Month')
            ORDER BY MIN(aml.date)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        results = {row['month'].strip(): row for row in self._cr.dictfetchall()}

        # Process results efficiently
        records = []
        for month in month_list:
            row = results.get(month, {'income': 0.0, 'expense': 0.0})
            income_val = abs(row['income']) if row['income'] else 0.0
            expense_val = abs(row['expense']) if row['expense'] else 0.0

            records.append({
                'month': month,
                'income': income_val,
                'expense': expense_val,
                'profit': income_val - expense_val
            })

        # Extract arrays efficiently
        return {
            'income': [r['income'] for r in records],
            'expense': [r['expense'] for r in records],
            'month': [r['month'] for r in records],
            'profit': [r['profit'] for r in records]
        }

    @api.model
    def get_income_last_year(self, *post):
        """Optimized income data retrieval for last year"""
        company_id = self.get_current_company_value()

        month_list = []
        for i in range(11, -1, -1):
            l_month = datetime.now() - relativedelta(months=i)
            text = format(l_month, '%B')
            month_list.append(text)

        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT 
                TO_CHAR(aml.date, 'Month') as month,
                SUM(CASE WHEN aa.internal_group = 'income' THEN aml.debit - aml.credit ELSE 0 END) as income,
                SUM(CASE WHEN aa.internal_group = 'expense' THEN aml.debit - aml.credit ELSE 0 END) as expense
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group IN ('income', 'expense')
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
                AND aml.company_id = ANY(%s)
                AND {}
            GROUP BY TO_CHAR(aml.date, 'Month')
            ORDER BY MIN(aml.date)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        results = {row['month'].strip(): row for row in self._cr.dictfetchall()}

        records = []
        for month in month_list:
            row = results.get(month, {'income': 0.0, 'expense': 0.0})
            income_val = abs(row['income']) if row['income'] else 0.0
            expense_val = abs(row['expense']) if row['expense'] else 0.0

            records.append({
                'month': month,
                'income': income_val,
                'expense': expense_val,
                'profit': income_val - expense_val
            })

        return {
            'income': [r['income'] for r in records],
            'expense': [r['expense'] for r in records],
            'month': [r['month'] for r in records],
            'profit': [r['profit'] for r in records]
        }

    @api.model
    def get_income_last_month(self, *post):
        """Optimized daily income data for last month"""
        company_id = self.get_current_company_value()
        now = datetime.now()
        last_month = now - relativedelta(months=1)
        days_in_month = calendar.monthrange(last_month.year, last_month.month)[1]
        day_list = list(range(1, days_in_month + 1))

        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT 
                EXTRACT(DAY FROM aml.date)::int as date,
                SUM(CASE WHEN aa.internal_group = 'income' THEN aml.debit - aml.credit ELSE 0 END) as income,
                SUM(CASE WHEN aa.internal_group = 'expense' THEN aml.debit - aml.credit ELSE 0 END) as expense
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group IN ('income', 'expense')
                AND EXTRACT(MONTH FROM aml.date) = %s
                AND EXTRACT(YEAR FROM aml.date) = %s
                AND aml.company_id = ANY(%s)
                AND {}
            GROUP BY EXTRACT(DAY FROM aml.date)
        """.format(states_condition)

        self._cr.execute(query, (last_month.month, last_month.year, company_id))
        results = {int(row['date']): row for row in self._cr.dictfetchall()}

        records = []
        for date in day_list:
            row = results.get(date, {'income': 0.0, 'expense': 0.0})
            income_val = abs(row['income']) if row['income'] else 0.0
            expense_val = abs(row['expense']) if row['expense'] else 0.0

            records.append({
                'date': date,
                'income': income_val,
                'expense': expense_val,
                'profit': income_val - expense_val
            })

        return {
            'income': [r['income'] for r in records],
            'expense': [r['expense'] for r in records],
            'date': [r['date'] for r in records],
            'profit': [r['profit'] for r in records]
        }

    @api.model
    def get_income_this_month(self, *post):
        """Optimized daily income data for current month"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        # Get days in current month
        now = datetime.now()
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        day_list = list(range(1, days_in_month + 1))

        query = """
            SELECT 
                EXTRACT(DAY FROM aml.date)::int as date,
                SUM(CASE WHEN aa.internal_group = 'income' THEN aml.debit - aml.credit ELSE 0 END) as income,
                SUM(CASE WHEN aa.internal_group = 'expense' THEN aml.debit - aml.credit ELSE 0 END) as expense
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group IN ('income', 'expense')
                AND EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
                AND {}
            GROUP BY EXTRACT(DAY FROM aml.date)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        results = {int(row['date']): row for row in self._cr.dictfetchall()}

        records = []
        for date in day_list:
            row = results.get(date, {'income': 0.0, 'expense': 0.0})
            income_val = abs(row['income']) if row['income'] else 0.0
            expense_val = abs(row['expense']) if row['expense'] else 0.0

            records.append({
                'date': date,
                'income': income_val,
                'expense': expense_val,
                'profit': income_val - expense_val
            })

        return {
            'income': [r['income'] for r in records],
            'expense': [r['expense'] for r in records],
            'date': [r['date'] for r in records],
            'profit': [r['profit'] for r in records]
        }

    @api.model
    def get_latebills(self, *post):
        """Optimized late bills retrieval with LIMIT"""
        company_id = self.get_current_company_value()
        states_condition = "am.state = 'posted'" if post == ('posted',) else "am.state IN ('posted', 'draft')"

        query = """
            SELECT 
                rp.name as partner,
                SUM(am.amount_total) as amount
            FROM account_move am
            JOIN res_partner rp ON am.partner_id = rp.id
            WHERE am.move_type = 'in_invoice'
                AND am.payment_state = 'not_paid'
                AND am.company_id = ANY(%s)
                AND {}
                AND am.commercial_partner_id = rp.commercial_partner_id
            GROUP BY rp.name, am.commercial_partner_id
            ORDER BY amount DESC
            LIMIT 10
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        record = self._cr.dictfetchall()

        bill_partner = [item['partner'] for item in record]
        bill_amount = [item['amount'] for item in record]

        if len(record) > 9:
            amounts = sum(bill_amount[9:])
            bill_amount = bill_amount[:9]
            bill_amount.append(amounts)
            bill_partner = bill_partner[:9]
            bill_partner.append("Others")

        return {
            'bill_partner': bill_partner,
            'bill_amount': bill_amount,
            'result': []
        }

    @api.model
    def get_overdues(self, *post):
        """Optimized overdue amounts retrieval"""
        company_id = self.get_current_company_value()
        states_condition = "am.state = 'posted'" if post == ('posted',) else "am.state IN ('posted', 'draft')"

        query = """
            SELECT 
                rp.name as partner,
                SUM(am.amount_total) as amount
            FROM account_move am
            JOIN res_partner rp ON am.partner_id = rp.id
            WHERE am.move_type = 'out_invoice'
                AND am.payment_state = 'not_paid'
                AND am.company_id = ANY(%s)
                AND {}
                AND am.commercial_partner_id = rp.commercial_partner_id
            GROUP BY rp.name, am.commercial_partner_id
            ORDER BY amount DESC
            LIMIT 10
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        record = self._cr.dictfetchall()

        due_partner = [item['partner'] for item in record]
        due_amount = [item['amount'] for item in record]

        if len(record) > 9:
            amounts = sum(due_amount[9:])
            due_amount = due_amount[:9]
            due_amount.append(amounts)
            due_partner = due_partner[:9]
            due_partner.append("Others")

        return {
            'due_partner': due_partner,
            'due_amount': due_amount,
            'result': []
        }

    @api.model
    def get_overdues_this_month_and_year(self, *post):
        """Optimized overdue amounts for specific periods"""
        company_id = self.get_current_company_value()
        states_condition = "am.state = 'posted'" if post[0] == 'posted' else "am.state IN ('posted', 'draft')"

        if post[1] == 'this_month':
            date_condition = """
                AND EXTRACT(MONTH FROM am.invoice_date_due) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM am.invoice_date_due) = EXTRACT(YEAR FROM CURRENT_DATE)
            """
        else:
            date_condition = "AND EXTRACT(YEAR FROM am.invoice_date_due) = EXTRACT(YEAR FROM CURRENT_DATE)"

        query = """
            SELECT 
                rp.name as due_partner,
                SUM(am.amount_total) as amount
            FROM account_move am
            JOIN res_partner rp ON am.partner_id = rp.id
            WHERE am.move_type = 'out_invoice'
                AND am.payment_state = 'not_paid'
                AND {}
                AND am.company_id = ANY(%s)
                AND am.partner_id = rp.commercial_partner_id
                {}
            GROUP BY rp.name, am.partner_id
            ORDER BY amount DESC
            LIMIT 10
        """.format(states_condition, date_condition)

        self._cr.execute(query, (company_id,))
        record = self._cr.dictfetchall()

        due_partner = [item['due_partner'] for item in record]
        due_amount = [item['amount'] for item in record]

        if len(record) > 9:
            amounts = sum(due_amount[9:])
            due_amount = due_amount[:9]
            due_amount.append(amounts)
            due_partner = due_partner[:9]
            due_partner.append("Others")

        return {
            'due_partner': due_partner,
            'due_amount': due_amount,
            'result': []
        }

    @api.model
    def get_latebillss(self, *post):
        """Optimized late bills for specific periods"""
        company_id = self.get_current_company_value()
        states_condition = "am.state = 'posted'" if post[0] == 'posted' else "am.state IN ('posted', 'draft')"

        if post[1] == 'this_month':
            date_condition = """
                AND EXTRACT(MONTH FROM am.invoice_date_due) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM am.invoice_date_due) = EXTRACT(YEAR FROM CURRENT_DATE)
            """
        else:
            date_condition = "AND EXTRACT(YEAR FROM am.invoice_date_due) = EXTRACT(YEAR FROM CURRENT_DATE)"

        query = """
            SELECT 
                rp.name as bill_partner,
                SUM(am.amount_total) as amount
            FROM account_move am
            JOIN res_partner rp ON am.partner_id = rp.id
            WHERE am.move_type = 'in_invoice'
                AND am.payment_state = 'not_paid'
                AND {}
                AND am.company_id = ANY(%s)
                AND am.partner_id = rp.commercial_partner_id
                {}
            GROUP BY rp.name, am.partner_id
            ORDER BY amount DESC
            LIMIT 10
        """.format(states_condition, date_condition)

        self._cr.execute(query, (company_id,))
        record = self._cr.dictfetchall()

        bill_partner = [item['bill_partner'] for item in record]
        bill_amount = [item['amount'] for item in record]

        if len(record) > 9:
            amounts = sum(bill_amount[9:])
            bill_amount = bill_amount[:9]
            bill_amount.append(amounts)
            bill_partner = bill_partner[:9]
            bill_partner.append("Others")

        return {
            'bill_partner': bill_partner,
            'bill_amount': bill_amount,
            'result': []
        }

    @api.model
    def get_top_10_customers_month(self, *post):
        """Optimized top customers retrieval"""
        company_id = self.get_current_company_value()
        states_condition = "am.state = 'posted'" if post[0] == 'posted' else "am.state IN ('posted', 'draft')"

        if post[1] == 'this_month':
            date_condition = """
                AND EXTRACT(MONTH FROM am.invoice_date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM am.invoice_date) = EXTRACT(YEAR FROM CURRENT_DATE)
            """
        else:
            one_month_ago = (datetime.now() - relativedelta(months=1)).month
            date_condition = f"AND EXTRACT(MONTH FROM am.invoice_date) = {one_month_ago}"

        # Single query for both invoice and refund data
        query = """
            SELECT 
                rp.name as customers,
                am.commercial_partner_id as parent,
                SUM(CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE 0 END) as invoice_amount,
                SUM(CASE WHEN am.move_type = 'out_refund' THEN am.amount_total ELSE 0 END) as refund_amount
            FROM account_move am
            JOIN res_partner rp ON am.commercial_partner_id = rp.id
            WHERE am.move_type IN ('out_invoice', 'out_refund')
                AND am.company_id = ANY(%s)
                AND {}
                {}
            GROUP BY rp.name, am.commercial_partner_id
            HAVING SUM(CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE 0 END) > 0
            ORDER BY (SUM(CASE WHEN am.move_type = 'out_invoice' THEN am.amount_total ELSE 0 END) - 
                      SUM(CASE WHEN am.move_type = 'out_refund' THEN am.amount_total ELSE 0 END)) DESC
            LIMIT 10
        """.format(states_condition, date_condition)

        self._cr.execute(query, (company_id,))
        results = self._cr.dictfetchall()

        summed = []
        for row in results:
            amount = row['invoice_amount'] - row['refund_amount']
            summed.append({
                'customers': row['customers'],
                'amount': amount,
                'parent': row['parent']
            })

        return summed

    @api.model
    def get_total_invoice(self, *post):
        """Optimized total invoice retrieval"""
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT 
                SUM(CASE WHEN move_type = 'out_invoice' THEN amount_total ELSE 0 END) as customer_invoice,
                SUM(CASE WHEN move_type = 'in_invoice' THEN amount_total ELSE 0 END) as supplier_invoice,
                SUM(CASE WHEN move_type = 'out_refund' THEN amount_total ELSE 0 END) as credit_note,
                SUM(CASE WHEN move_type = 'in_refund' THEN amount_total ELSE 0 END) as refund
            FROM account_move
            WHERE move_type IN ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')
                AND company_id = ANY(%s)
                AND {}
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        result = self._cr.dictfetchone() or {}

        return (
            [result.get('customer_invoice', 0.0)],
            [result.get('credit_note', 0.0)],
            [result.get('supplier_invoice', 0.0)],
            [result.get('refund', 0.0)]
        )

    @api.model
    def get_total_invoice_current_year(self, *post):
        """Optimized invoice totals for current year"""
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT 
                SUM(CASE WHEN move_type = 'out_invoice' THEN amount_total_signed ELSE 0 END) as customer_invoice,
                SUM(CASE WHEN move_type = 'in_invoice' THEN -amount_total_signed ELSE 0 END) as supplier_invoice,
                SUM(CASE WHEN move_type = 'out_invoice' AND payment_state = 'paid' 
                     THEN amount_total_signed - amount_residual_signed ELSE 0 END) as customer_paid,
                SUM(CASE WHEN move_type = 'in_invoice' AND payment_state = 'paid' 
                     THEN -(amount_total_signed - amount_residual_signed) ELSE 0 END) as supplier_paid
            FROM account_move
            WHERE move_type IN ('out_invoice', 'in_invoice')
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
                AND {}
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        result = self._cr.dictfetchone() or {}

        return (
            [result.get('customer_invoice', 0.0)],
            [0.0],  # credit_note
            [result.get('supplier_invoice', 0.0)],
            [0.0],  # refund
            [result.get('customer_paid', 0.0)],
            [result.get('supplier_paid', 0.0)],
            [0.0],  # customer_credit_paid
            [0.0]  # supplier_refund_paid
        )

    @api.model
    def get_total_invoice_current_month(self, *post):
        """Optimized invoice totals for current month"""
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT 
                SUM(CASE WHEN move_type = 'out_invoice' THEN amount_total_signed ELSE 0 END) as customer_invoice,
                SUM(CASE WHEN move_type = 'in_invoice' THEN -amount_total_signed ELSE 0 END) as supplier_invoice,
                SUM(CASE WHEN move_type = 'out_invoice' AND payment_state = 'paid' 
                     THEN amount_total_signed - amount_residual_signed ELSE 0 END) as customer_paid,
                SUM(CASE WHEN move_type = 'in_invoice' AND payment_state = 'paid' 
                     THEN -(amount_total_signed - amount_residual_signed) ELSE 0 END) as supplier_paid
            FROM account_move
            WHERE move_type IN ('out_invoice', 'in_invoice')
                AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
                AND {}
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        result = self._cr.dictfetchone() or {}

        currency = self.get_currency()

        return (
            [result.get('customer_invoice', 0.0)],
            [0.0],  # credit_note
            [result.get('supplier_invoice', 0.0)],
            [0.0],  # refund
            [result.get('customer_paid', 0.0)],
            [result.get('supplier_paid', 0.0)],
            [0.0],  # customer_credit_paid
            [0.0],  # supplier_refund_paid
            currency
        )

    @api.model
    def get_total_invoice_this_month(self, *post):
        """Optimized invoice total for this month"""
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT SUM(amount_total) as total
            FROM account_move
            WHERE move_type = 'out_invoice'
                AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
                AND {}
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return self._cr.dictfetchall()

    @api.model
    def get_total_invoice_last_month(self):
        """Optimized invoice total for last month"""
        one_month_ago = (datetime.now() - relativedelta(months=1))

        query = """
            SELECT SUM(amount_total) as total
            FROM account_move
            WHERE move_type = 'out_invoice'
                AND state = 'posted'
                AND EXTRACT(MONTH FROM date) = %s
                AND EXTRACT(YEAR FROM date) = %s
        """

        self._cr.execute(query, (one_month_ago.month, one_month_ago.year))
        return self._cr.dictfetchall()

    @api.model
    def get_total_invoice_last_year(self):
        """Optimized invoice total for last year"""
        query = """
            SELECT SUM(amount_total) as total
            FROM account_move
            WHERE move_type = 'out_invoice'
                AND state = 'posted'
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
        """

        self._cr.execute(query)
        return self._cr.dictfetchall()

    @api.model
    def get_total_invoice_this_year(self):
        """Optimized invoice total for this year"""
        company_id = self.get_current_company_value()

        query = """
            SELECT SUM(amount_total) as total
            FROM account_move
            WHERE move_type = 'out_invoice'
                AND state = 'posted'
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
        """

        self._cr.execute(query, (company_id,))
        return self._cr.dictfetchall()

    @api.model
    def unreconcile_items(self):
        """Optimized unreconciled items count"""
        query = """
            SELECT COUNT(*)
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aml.full_reconcile_id IS NULL
                AND aml.balance != 0
                AND aa.reconcile IS TRUE
        """

        self._cr.execute(query)
        return self._cr.dictfetchall()

    @api.model
    def unreconcile_items_this_month(self, *post):
        """Optimized unreconciled items for this month"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT COUNT(*)
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.full_reconcile_id IS NULL
                AND aml.product_id IS NULL
                AND aml.balance != 0
                AND aa.reconcile IS TRUE
                AND {}
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return self._cr.dictfetchall()

    @api.model
    def unreconcile_items_last_month(self):
        """Optimized unreconciled items for last month"""
        one_month_ago = (datetime.now() - relativedelta(months=1))

        query = """
            SELECT COUNT(*)
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE EXTRACT(MONTH FROM aml.date) = %s
                AND EXTRACT(YEAR FROM aml.date) = %s
                AND aml.full_reconcile_id IS NULL
                AND aml.balance != 0
                AND aa.reconcile IS TRUE
        """

        self._cr.execute(query, (one_month_ago.month, one_month_ago.year))
        return self._cr.dictfetchall()

    @api.model
    def unreconcile_items_this_year(self, *post):
        """Optimized unreconciled items for this year"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT COUNT(*)
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.full_reconcile_id IS NULL
                AND aml.product_id IS NULL
                AND aml.balance != 0
                AND aa.reconcile IS TRUE
                AND {}
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return self._cr.dictfetchall()

    @api.model
    def unreconcile_items_last_year(self):
        """Optimized unreconciled items for last year"""
        query = """
            SELECT COUNT(*)
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
                AND aml.full_reconcile_id IS NULL
                AND aml.balance != 0
                AND aa.reconcile IS TRUE
        """

        self._cr.execute(query)
        return self._cr.dictfetchall()

    @api.model
    def click_expense_month(self, *post):
        """Optimized expense click handler for month"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'expense'
                AND {}
                AND EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_expense_year(self, *post):
        """Optimized expense click handler for year"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'expense'
                AND {}
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_total_income_month(self, *post):
        """Optimized income click handler for month"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'income'
                AND {}
                AND EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_total_income_year(self, *post):
        """Optimized income click handler for year"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'income'
                AND {}
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_profit_income_month(self, *post):
        """Optimized profit click handler for month"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group IN ('income', 'expense')
                AND {}
                AND EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_profit_income_year(self, *post):
        """Optimized profit click handler for year"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group IN ('income', 'expense')
                AND {}
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    # Continue with remaining click handlers and other methods...
    @api.model
    def click_bill_year(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT id FROM account_move
            WHERE move_type = 'in_invoice'
                AND {}
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_bill_year_paid(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT id FROM account_move
            WHERE move_type = 'in_invoice'
                AND {}
                AND payment_state = 'paid'
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_invoice_year_paid(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT id FROM account_move
            WHERE move_type = 'out_invoice'
                AND {}
                AND payment_state = 'paid'
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_invoice_year(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT id FROM account_move
            WHERE move_type = 'out_invoice'
                AND {}
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_bill_month(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT id FROM account_move
            WHERE move_type = 'in_invoice'
                AND {}
                AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_bill_month_paid(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT id FROM account_move
            WHERE move_type = 'in_invoice'
                AND {}
                AND payment_state = 'paid'
                AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_invoice_month_paid(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT id FROM account_move
            WHERE move_type = 'out_invoice'
                AND {}
                AND payment_state = 'paid'
                AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_invoice_month(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "state = 'posted'" if post == ('posted',) else "state IN ('posted', 'draft')"

        query = """
            SELECT id FROM account_move
            WHERE move_type = 'out_invoice'
                AND {}
                AND EXTRACT(MONTH FROM date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_unreconcile_month(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.full_reconcile_id IS NULL
                AND aml.product_id IS NULL
                AND aml.balance != 0
                AND aa.reconcile IS TRUE
                AND {}
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def click_unreconcile_year(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT aml.id
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.full_reconcile_id IS NULL
                AND aml.product_id IS NULL
                AND aml.balance != 0
                AND aa.reconcile IS TRUE
                AND {}
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return [row[0] for row in self._cr.fetchall()]

    @api.model
    def month_income(self):
        query = """
            SELECT SUM(aml.debit) as debit, SUM(aml.credit) as credit
            FROM account_move am
            JOIN account_move_line aml ON am.id = aml.move_id
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE am.move_type = 'entry'
                AND am.state = 'posted'
                AND aa.internal_group = 'income'
                AND EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
        """
        self._cr.execute(query)
        return self._cr.dictfetchall()

    @api.model
    def month_income_this_month(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT SUM(aml.debit) as debit, SUM(aml.credit) as credit
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'income'
                AND {}
                AND EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return self._cr.dictfetchall()

    @api.model
    def profit_income_this_month(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT 
                SUM(aml.debit) - SUM(aml.credit) as profit,
                aa.internal_group
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group IN ('income', 'expense')
                AND {}
                AND EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
            GROUP BY aa.internal_group
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        income = self._cr.dictfetchall()
        return [item['profit'] for item in income]

    @api.model
    def profit_income_this_year(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT 
                SUM(aml.debit) - SUM(aml.credit) as profit,
                aa.internal_group
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group IN ('income', 'expense')
                AND {}
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
            GROUP BY aa.internal_group
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        income = self._cr.dictfetchall()
        return [item['profit'] for item in income]

    @api.model
    def month_income_last_month(self):
        one_month_ago = (datetime.now() - relativedelta(months=1))

        query = """
            SELECT SUM(aml.debit) as debit, SUM(aml.credit) as credit
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'income'
                AND aml.parent_state = 'posted'
                AND EXTRACT(MONTH FROM aml.date) = %s
                AND EXTRACT(YEAR FROM aml.date) = %s
        """

        self._cr.execute(query, (one_month_ago.month, one_month_ago.year))
        return self._cr.dictfetchall()

    @api.model
    def month_income_this_year(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT SUM(aml.debit) as debit, SUM(aml.credit) as credit
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'income'
                AND {}
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return self._cr.dictfetchall()

    @api.model
    def month_income_last_year(self):
        query = """
            SELECT SUM(aml.debit) as debit, SUM(aml.credit) as credit
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'income'
                AND aml.parent_state = 'posted'
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
        """

        self._cr.execute(query)
        return self._cr.dictfetchall()

    @api.model
    def get_currency(self):
        """Optimized currency retrieval"""
        company_ids = self.get_current_company_value()
        if 0 in company_ids:
            company_ids.remove(0)

        current_company_id = company_ids[0] if company_ids else self.env.company.id
        current_company = self.env['res.company'].browse(current_company_id)
        default = current_company.currency_id or self.env.ref('base.main_company').currency_id

        lang = self.env.user.lang or 'en_US'
        lang = lang.replace("_", '-')

        return {
            'position': default.position,
            'symbol': default.symbol,
            'language': lang
        }

    @api.model
    def month_expense(self):
        query = """
            SELECT SUM(aml.debit) as debit, SUM(aml.credit) as credit
            FROM account_move am
            JOIN account_move_line aml ON am.id = aml.move_id
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE am.move_type = 'entry'
                AND am.state = 'posted'
                AND aa.internal_group = 'expense'
                AND EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
        """
        self._cr.execute(query)
        return self._cr.dictfetchall()

    @api.model
    def month_expense_this_month(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT SUM(aml.debit) as debit, SUM(aml.credit) as credit
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'expense'
                AND {}
                AND EXTRACT(MONTH FROM aml.date) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return self._cr.dictfetchall()

    @api.model
    def month_expense_this_year(self, *post):
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post == (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT SUM(aml.debit) as debit, SUM(aml.credit) as credit
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            WHERE aa.internal_group = 'expense'
                AND {}
                AND EXTRACT(YEAR FROM aml.date) = EXTRACT(YEAR FROM CURRENT_DATE)
                AND aml.company_id = ANY(%s)
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        return self._cr.dictfetchall()

    @api.model
    def bank_balance(self, *post):
        """Optimized bank balance retrieval"""
        company_id = self.get_current_company_value()
        states_condition = "aml.parent_state = 'posted'" if post != (
            'posted',) else "aml.parent_state IN ('posted', 'draft')"

        query = """
            SELECT 
                aa.name,
                SUM(aml.balance) as balance,
                MIN(aa.id) as id
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE aa.account_type = 'asset_cash'
                AND aml.company_id = ANY(%s)
                AND {}
            GROUP BY aa.name
            ORDER BY balance DESC
        """.format(states_condition)

        self._cr.execute(query, (company_id,))
        record = self._cr.dictfetchall()

        banks = [item['name'] for item in record]
        user_lang = self.env.user.lang
        banks_list = [
            rec.get(user_lang, rec.get('en_US', rec)) if isinstance(rec, dict) else rec
            for rec in banks
        ]
        banking = [item['balance'] for item in record]
        bank_ids = [item['id'] for item in record]

        return {
            'banks': banks_list,
            'banking': banking,
            'bank_ids': bank_ids
        }
