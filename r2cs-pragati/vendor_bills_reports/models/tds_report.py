from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pan_number = fields.Char(string="PAN Number")


class TdsReport(models.Model):
    _name = 'tds.report'

    name = fields.Char(string="Name")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    line_ids = fields.One2many('tds.report.line', 'tds_report_id')

    def generate_report(self):
        self.line_ids.unlink()
        tds_tax_ids = self.env['account.tax'].search([]).filtered(
            lambda x: 'TDS' in x.name or 'tds' in x.name or 'Tds' in x.name)
        tds_lines = self.env['account.move.line'].search([('tax_ids', 'in', tds_tax_ids.ids),('date','>=',self.start_date),('date','<=',self.end_date)])
        tds_invoice = tds_lines.mapped('move_id').sudo()

        for invoice in tds_invoice:
            vals = {'tds_report_id': self.id,
                    'date': invoice.invoice_date,
                    'vendor_id': invoice.partner_id.id,
                    'invoice_number': invoice.name,
                    'voucher_amount':invoice.amount_untaxed,
                    'interest': '0',
                    'status': '',
                    'narration': 'Ok',
                    'pan_status': 'Available' if invoice.partner_id.l10n_in_pan else 'Applied',
                    'pan_no': invoice.partner_id.l10n_in_pan,
                    'tds_type': '',
                    'tds_type_alias': '',
                    'transaction': '',
                    'transaction_date': False,
                    'certificate_no': '',
                    'tag_name': '',
                    'remarks': '',
                    }
            tds_amount = 0
            tds_percentage = 0
            section_code = ''
            account_name = False
            inv_lines = invoice.invoice_line_ids.filtered(lambda x: x in tds_lines)
            for l in inv_lines:
                line_tds_tax = l.tax_ids.filtered(lambda x: x.id in tds_tax_ids.ids)
                tds_amount += l.price_subtotal * line_tds_tax.amount / 100
                tds_percentage += line_tds_tax.amount
                section_code = line_tds_tax.name.split(' ')[-1]
                account_name =line_tds_tax.mapped('invoice_repartition_line_ids.account_id')

            vals.update({'tds_amount': tds_amount,
                         'net_tds': tds_amount,
                         'tds_percentage': tds_percentage,
                         'section_code': section_code,
                         'account_name': account_name[0].name if account_name else '',

                         })
            self.line_ids.create(vals)


class TdsReportLine(models.Model):
    _name = 'tds.report.line'
    _description = 'Tds Report Line'

    name = fields.Char(string="Name")
    tds_report_id = fields.Many2one('tds.report')
    vendor_id = fields.Many2one('res.partner', string='Party Name')
    date = fields.Date(string='Date')
    invoice_number = fields.Char(string="Voucher Number")
    voucher_amount = fields.Float(string='Voucher Amount')
    tds_percentage = fields.Float(string='TDS %')
    tds_amount = fields.Float(string='TDS Amount')
    net_tds = fields.Float(string='Net TDS')
    interest = fields.Float(string='Interest')
    status = fields.Char(string="Status")
    narration = fields.Text(string='Narration')
    pan_status = fields.Char(string="Pan Status")
    pan_no = fields.Char(string='PAN No.')
    account_name = fields.Char(string='Name of Account/TDS Ledger Name')
    tds_type = fields.Char(string='TDS Type')
    tds_type_alias = fields.Char(string='TDS Type Alias')
    section_code = fields.Char(string='Section Code')
    transaction = fields.Char(string='Transaction Serial No')
    transaction_date = fields.Date(string='Transaction Date')
    certificate_no = fields.Char(string='Certificate No')
    tag_name = fields.Char(string='Tag Name')
    remarks = fields.Text(string='Remarks')

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_tds_line = fields.Boolean(compute="_compute_line_tds_values",store=True)

    @api.depends('price_subtotal','price_subtotal')
    def _compute_line_tds_values(self):
        tds_tax_ids = self.env['account.tax'].search([]).filtered(
            lambda x: 'TDS' in x.name or 'tds' in x.name or 'Tds' in x.name)

        for rec in self:
            tds_amount = 0
            rec.filtered(lambda x: x.tax_ids in tds_tax_ids)
            line_tds_tax = rec.tax_ids.filtered(lambda x: x.id in tds_tax_ids.ids)
            print(line_tds_tax,rec.id)
            if line_tds_tax:
                tds_amount += rec.price_subtotal * line_tds_tax.amount / 100
            rec.is_tds_line = True if tds_amount != 0.0 else False