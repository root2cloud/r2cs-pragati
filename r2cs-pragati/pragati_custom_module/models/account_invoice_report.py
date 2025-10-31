from odoo import models, fields, api, _
import re
# adding file to statging
class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"


    gstin_number = fields.Char(string='GSTIN NO', related='partner_id.vat')
    sale_price_product = fields.Float(string='Sale Price', related='product_id.list_price')
    l10n_in_hsn_code = fields.Char(string='HSN Code', related='product_id.l10n_in_hsn_code')
    l10n_in_gst_treatment = fields.Selection([
            ('regular', 'Registered Business - Regular'),
            ('composition', 'Registered Business - Composition'),
            ('unregistered', 'Unregistered Business'),
            ('consumer', 'Consumer'),
            ('overseas', 'Overseas'),
            ('special_economic_zone', 'Special Economic Zone'),
            ('deemed_export', 'Deemed Export'),
            ('uin_holders', 'UIN Holders'),
        ], string="GST Treatment", related='partner_id.l10n_in_gst_treatment')

    sgst_tax = fields.Float(string='SGST OUTPUT', compute='_compute_tax_values')
    cgst_tax = fields.Float(string='CGST OUTPUT', compute='_compute_tax_values')
    igst_tax = fields.Float(string='IGST OUTPUT', compute='_compute_tax_values')
    remaining_tax = fields.Float(string='Other Tax Amount', compute='_compute_tax_values')
    sgst_tax_char = fields.Float(string='SGST Tax Rate', compute='_compute_tax_values')
    cgst_tax_char = fields.Float(string='CGST Tax Rate', compute='_compute_tax_values')
    igst_tax_char = fields.Float(string='IGST Tax Rate', compute='_compute_tax_values')
    rem_tax_char = fields.Float(string='Other Tax Input', compute='_compute_tax_values')

    @api.depends('move_id.invoice_line_ids', 'move_id.invoice_line_ids.tax_ids', 'move_id.invoice_line_ids.price_subtotal')
    def _compute_tax_values(self):
        for record in self:
            sgst_tax = cgst_tax = igst_tax = remaining_tax = 0.0
            sgst_tax_char = cgst_tax_char = igst_tax_char = rem_tax_char = 0.0
            gst = 0.0  # Initialize gst here

            move_type = "out_refund" and "in_refund"
            move_type = record.move_id.move_type
            is_refund = move_type in ['out_refund', 'in_refund']

            for line in record.move_id.invoice_line_ids.filtered(lambda x: x.product_id == record.product_id):
                for tax in line.tax_ids.children_tax_ids:
                    print("=====================tax name ============",tax.name)
                    # Use regular expression to extract numeric value
                    match = re.search(r'(\d+(\.\d+)?)%', tax.name)
                    if match:
                        tax_amount = float(match.group(1))
                    else:
                        tax_amount = 0.0

                    # tax_amount = float(match.group(1)) if match else 0.0

                    if 'IGST' in tax.name.upper():
                        igst_tax += line.price_subtotal * tax.amount / 100
                        igst_tax_char += tax_amount
                    elif 'CGST' in tax.name.upper():
                        cgst_tax = line.price_subtotal * tax.amount / 100

                        print("=====================CGST name ============",cgst_tax)
                        print("=====================CGST name ============",line.price_subtotal)
                        print("=====================CGST name ============",tax.amount)

                        cgst_tax_char += tax_amount
                    elif 'SGST' in tax.name.upper():
                        sgst_tax += line.price_subtotal * tax.amount / 100
                        sgst_tax_char += tax_amount
                    elif 'GST' in tax.name.upper():
                        gst += line.price_subtotal * tax.amount / 100
                        sgst_tax_char += tax_amount / 2
                        cgst_tax_char += tax_amount / 2
                    else:
                        # Handle remaining taxes here
                        remaining_tax += line.price_subtotal * tax.amount / 100
                        rem_tax_char += tax_amount
                print("=====================IGST name ============",igst_tax)
                print("=====================CGST name ============",cgst_tax)
                print("====================SGST name ============",sgst_tax)
                print("=====================GST name ============",gst)
                if is_refund:
                    sgst_tax = -sgst_tax
                    cgst_tax = -cgst_tax
                    igst_tax = -igst_tax
                    sgst_tax_char = -sgst_tax_char
                    cgst_tax_char = -cgst_tax_char
                    igst_tax_char = -igst_tax_char
                    remaining_tax = -remaining_tax
        
            # Split the GST into CGST and SGST after the loop
            # if gst > 0:
            #     gst_split = gst / 2
            #     cgst_tax += gst_split
            #     sgst_tax += gst_split

            record.igst_tax = igst_tax
            record.cgst_tax = cgst_tax
            record.sgst_tax = sgst_tax
            record.sgst_tax_char = sgst_tax_char
            record.cgst_tax_char = cgst_tax_char
            record.igst_tax_char = igst_tax_char
            record.rem_tax_char = rem_tax_char
            record.remaining_tax = remaining_tax
