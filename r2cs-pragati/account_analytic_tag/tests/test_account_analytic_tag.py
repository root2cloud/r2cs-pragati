# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.tests import Form, tagged
from odoo.tests.common import users

from .common import TestAccountAnalyticTagBase


@tagged("post_install", "-at_install")
class TestAccountAnalyticTag(TestAccountAnalyticTagBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env.company.chart_template_id:
            # Load a CoA if there's none in current company
            coa = cls.env.ref("l10n_generic_coa.configurable_chart_template", False)
            if not coa:
                # Load the first available CoA
                coa = cls.env["account.chart.template"].search(
                    [("visible", "=", True)], limit=1
                )
            coa.try_loading(company=cls.env.company, install_demo=False)
        invoice_form = Form(
            cls.env["account.move"]
            .with_user(cls.user)
            .with_context(default_move_type="out_invoice")
        )
        invoice_form.partner_id = cls.partner_a
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.analytic_tag_ids.add(cls.account_analytic_tag_a)
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.product_b
            line_form.analytic_tag_ids.add(cls.account_analytic_tag_a)
            line_form.analytic_tag_ids.add(cls.account_analytic_tag_b)
        cls.invoice = invoice_form.save()
        cls.line_a = cls.invoice.invoice_line_ids.filtered(
            lambda x: x.product_id == cls.product_a
        )
        cls.line_b = cls.invoice.invoice_line_ids.filtered(
            lambda x: x.product_id == cls.product_b
        )

    @users("test-analytic-tag-user")
    def test_action_post_analytic_lines_01(self):
        self.invoice.action_post()
        self.assertFalse(self.line_a.analytic_line_ids)
        self.assertFalse(self.line_b.analytic_line_ids)

    @users("test-analytic-tag-user")
    def test_action_post_analytic_lines_02(self):
        self.line_a.analytic_distribution = {self.analytic_account_a.id: 100}
        self.line_b.analytic_distribution = {self.analytic_account_a.id: 100}
        self.invoice.action_post()
        self.assertIn(
            self.account_analytic_tag_a, self.line_a.analytic_line_ids.tag_ids
        )
        self.assertNotIn(
            self.account_analytic_tag_b, self.line_a.analytic_line_ids.tag_ids
        )
        self.assertIn(
            self.account_analytic_tag_a, self.line_b.analytic_line_ids.tag_ids
        )
        self.assertIn(
            self.account_analytic_tag_b, self.line_b.analytic_line_ids.tag_ids
        )

    @users("test-analytic-tag-user")
    def test_action_post_analytic_lines_03(self):
        self.account_analytic_tag_b.account_analytic_id = False
        self.line_a.analytic_distribution = {self.analytic_account_a.id: 100}
        self.line_b.analytic_distribution = {self.analytic_account_a.id: 100}
        self.invoice.action_post()
        self.assertIn(
            self.account_analytic_tag_a, self.line_a.analytic_line_ids.tag_ids
        )
        self.assertNotIn(
            self.account_analytic_tag_b, self.line_a.analytic_line_ids.tag_ids
        )
        self.assertIn(
            self.account_analytic_tag_a, self.line_b.analytic_line_ids.tag_ids
        )
        self.assertIn(
            self.account_analytic_tag_b, self.line_b.analytic_line_ids.tag_ids
        )

    @users("test-analytic-tag-user")
    def test_action_post_analytic_lines_04(self):
        self.account_analytic_tag_a.account_analytic_id = self.analytic_account_b
        self.line_a.analytic_distribution = {self.analytic_account_a.id: 100}
        self.invoice.action_post()
        self.assertNotIn(
            self.account_analytic_tag_a, self.line_a.analytic_line_ids.tag_ids
        )
        self.assertNotIn(
            self.account_analytic_tag_b, self.line_a.analytic_line_ids.tag_ids
        )

    @users("test-analytic-tag-user")
    def test_action_post_analytic_lines_05(self):
        self.account_analytic_tag_a.account_analytic_id = self.analytic_account_b
        self.line_a.analytic_distribution = {
            self.analytic_account_a.id: 50,
            self.analytic_account_b.id: 50,
        }
        self.invoice.action_post()
        self.assertIn(
            self.account_analytic_tag_a, self.line_a.analytic_line_ids.tag_ids
        )
        self.assertNotIn(
            self.account_analytic_tag_b, self.line_a.analytic_line_ids.tag_ids
        )

    def test_analytic_tags_in_tax(self):
        tax = self.env["account.tax"].create(
            {
                "name": "account_analytic_tag tax example",
                "amount_type": "percent",
                "type_tax_use": "sale",
                "amount": 10,
                "analytic": True,
            }
        )
        self.line_a.tax_ids = [(4, tax.id)]
        tax_line = self.invoice.line_ids.filtered(lambda x, t=tax: x.tax_line_id == t)
        self.assertEqual(self.account_analytic_tag_a, tax_line.analytic_tag_ids)
