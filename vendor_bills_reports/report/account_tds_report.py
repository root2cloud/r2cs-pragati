from odoo import models, fields, api, _
import re
from odoo.addons.account.models.account_move import PAYMENT_STATE_SELECTION


class AccountTDSReport(models.Model):
    _name = "account.tds.report"

    _description = "Account TDS Reports"
    _auto = False
    _rec_name = 'invoice_date'
    _order = 'invoice_date desc'

    # ==== Invoice fields ====
    move_id = fields.Many2one('account.move', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    company_currency_id = fields.Many2one('res.currency', string='Company Currency', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', string='Main Partner')
    country_id = fields.Many2one('res.country', string="Country")
    invoice_user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    move_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
    ], readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Open'),
        ('cancel', 'Cancelled')
    ], string='Invoice Status', readonly=True)
    payment_state = fields.Selection(selection=PAYMENT_STATE_SELECTION, string='Payment Status', readonly=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', readonly=True)
    invoice_date = fields.Date(readonly=True, string="Invoice Date")

    # ==== Invoice line fields ====
    line_id = fields.Many2one('account.move.line', string="Move Line ID", compute="_compute_tds_values")
    quantity = fields.Float(string='Product Quantity', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    product_categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    invoice_date_due = fields.Date(string='Due Date', readonly=True)
    account_id = fields.Many2one('account.account', string='Revenue/Expense Account', readonly=True,
                                 domain=[('deprecated', '=', False)])
    price_subtotal = fields.Float(string='Untaxed Total', readonly=True)
    price_total = fields.Float(string='Total in Currency', readonly=True)
    price_average = fields.Float(string='Average Price', readonly=True, group_operator="avg")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)

    is_tds_line = fields.Boolean(store=True)
    tds_percentage = fields.Float(string='TDS %', compute="_compute_tds_values")
    tds_amount = fields.Float(string='TDS Amount', compute="_compute_tds_values")
    net_tds = fields.Float(string='Net TDS', compute="_compute_tds_values")
    account_name = fields.Char(string='Name of Account/TDS Ledger Name', compute="_compute_tds_values")
    section_code = fields.Char(string='Section Code', compute="_compute_tds_values")
    # tds_type = fields.Char(string='TDS Type')
    pan_status = fields.Char(string="Pan Status",compute="_compute_tds_values")
    pan_no = fields.Char(string='PAN No.',compute="_compute_tds_values")
    date = fields.Date(readonly=True, string='Accounting Date')

    _depends = {
        'account.move': [
            'name', 'state', 'move_type', 'partner_id', 'invoice_user_id', 'fiscal_position_id',
            'invoice_date', 'invoice_date_due','date', 'invoice_payment_term_id', 'partner_bank_id',
        ],
        'account.move.line': [
            'quantity', 'price_subtotal', 'price_total', 'amount_residual', 'balance', 'amount_currency',
            'move_id', 'product_id', 'product_uom_id', 'account_id', 'id',
            'journal_id', 'company_id', 'currency_id', 'partner_id',
        ],
        'product.product': ['product_tmpl_id'],
        'product.template': ['categ_id'],
        'uom.uom': ['category_id', 'factor', 'name', 'uom_type'],
        'res.currency.rate': ['currency_id', 'name'],
        'res.partner': ['country_id'],
    }

    def _compute_tds_values(self):
        tds_tax_ids = self.env['account.tax'].search([]).filtered(
            lambda x: 'TDS' in x.name or 'tds' in x.name or 'Tds' in x.name)

        for rec in self:
            rec.line_id = rec.id
            tds_amount = 0
            tds_percentage = 0
            section_code = ''
            account_name = False
            rec.line_id.filtered(lambda x: x.tax_ids in tds_tax_ids)
            line_tds_tax = rec.line_id.tax_ids.filtered(lambda x: x.id in tds_tax_ids.ids)
            if line_tds_tax:
                tds_amount += rec.line_id.price_subtotal * line_tds_tax.amount / 100
                tds_percentage += line_tds_tax.amount
                section_code = line_tds_tax.name.split(' ')[-1]
                account_name = line_tds_tax.mapped('invoice_repartition_line_ids.account_id')
            rec.pan_status = 'Available' if rec.line_id.move_id.partner_id.l10n_in_pan else 'Applied',
            rec.pan_no = rec.line_id.move_id.partner_id.l10n_in_pan
            rec.tds_percentage = tds_percentage
            rec.section_code = section_code
            rec.account_name = account_name[0].name if account_name else '',
            rec.net_tds = tds_amount
            rec.tds_amount = tds_amount
            rec.line_id.is_tds_line = True if tds_amount != 0.0 else False

    @property
    def _table_query(self):
        return '%s %s %s' % (self._select(), self._from(), self._where())

    @api.model
    def _select(self):
        return '''
            SELECT
                line.id,
                line.move_id,
                line.is_tds_line,
                line.product_id,
                line.account_id,
                line.journal_id,
                line.company_id,
                line.company_currency_id,
                line.partner_id AS commercial_partner_id,
                account.account_type AS user_type,
                move.state,
                move.move_type,
                move.partner_id,
                move.invoice_user_id,
                move.fiscal_position_id,
                move.payment_state,
                move.invoice_date,
                move.date,
                move.invoice_date_due,
                uom_template.id                                             AS product_uom_id,
                template.categ_id                                           AS product_categ_id,
                line.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0) * (CASE WHEN move.move_type IN ('in_invoice','out_refund','in_receipt') THEN -1 ELSE 1 END)
                                                                            AS quantity,
                -line.balance * currency_table.rate                         AS price_subtotal,
                line.price_total * (CASE WHEN move.move_type IN ('in_invoice','out_refund','in_receipt') THEN -1 ELSE 1 END)
                                                                            AS price_total,
                -COALESCE(
                   -- Average line price
                   (line.balance / NULLIF(line.quantity, 0.0)) * (CASE WHEN move.move_type IN ('in_invoice','out_refund','in_receipt') THEN -1 ELSE 1 END)
                   -- convert to template uom
                   * (NULLIF(COALESCE(uom_line.factor, 1), 0.0) / NULLIF(COALESCE(uom_template.factor, 1), 0.0)),
                   0.0) * currency_table.rate                               AS price_average,
                COALESCE(partner.country_id, commercial_partner.country_id) AS country_id,
                line.currency_id                                            AS currency_id
        '''

    @api.model
    def _from(self):
        return '''
            FROM account_move_line line
                LEFT JOIN res_partner partner ON partner.id = line.partner_id
                LEFT JOIN product_product product ON product.id = line.product_id
                LEFT JOIN account_account account ON account.id = line.account_id
                LEFT JOIN product_template template ON template.id = product.product_tmpl_id
                LEFT JOIN uom_uom uom_line ON uom_line.id = line.product_uom_id
                LEFT JOIN uom_uom uom_template ON uom_template.id = template.uom_id
                INNER JOIN account_move move ON move.id = line.move_id
                LEFT JOIN res_partner commercial_partner ON commercial_partner.id = move.commercial_partner_id
                JOIN {currency_table} ON currency_table.company_id = line.company_id
        '''.format(
            currency_table=self.env['res.currency']._get_query_currency_table(
                {'multi_company': True, 'date': {'date_to': fields.Date.today()}}),
        )

    @api.model
    def _where(self):
        return '''
            WHERE move.move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')
                AND line.account_id IS NOT NULL
                AND line.display_type = 'product'
                AND line.is_tds_line = 't'
        '''
