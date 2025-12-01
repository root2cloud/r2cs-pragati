from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    location_id = fields.Many2one('stock.location', string='Location', compute='_compute_location_id', store=False)

    # NEW: Add computed fields for GST values
    sgst_value = fields.Float(
        string='SGST (%)',
        compute='_compute_gst_values',
        store=False,
        help='State Goods and Services Tax percentage'
    )
    cgst_value = fields.Float(
        string='CGST (%)',
        compute='_compute_gst_values',
        store=False,
        help='Central Goods and Services Tax percentage'
    )

    def _compute_location_id(self):
        for product in self:
            quant = self.env['stock.quant'].search([('product_id', '=', product.id)], limit=1)
            product.location_id = quant.location_id

    # Add GST computation method
    @api.depends('taxes_id')
    def _compute_gst_values(self):
        """
        Extract SGST and CGST percentages from Customer Taxes.

        Handles:
        1. Group taxes (e.g., "GST 5%(SGST 2.5%+CGST 2.5%)")
        2. Individual taxes (e.g., "SGST Sale 2.5%")
        """
        for product in self:
            sgst = 0.0
            cgst = 0.0

            for tax in product.taxes_id:
                tax_name = (tax.name or '').upper()

                # Case 1: Check if it's a group tax with child taxes
                if tax.children_tax_ids:
                    for child_tax in tax.children_tax_ids:
                        child_name = (child_tax.name or '').upper()

                        # Extract SGST from child tax
                        if 'SGST' in child_name:
                            sgst = child_tax.amount

                        # Extract CGST from child tax
                        elif 'CGST' in child_name:
                            cgst = child_tax.amount

                # Case 2: Check parent tax itself (for direct SGST/CGST taxes)
                if 'SGST' in tax_name and not tax.children_tax_ids:
                    sgst = tax.amount
                elif 'CGST' in tax_name and not tax.children_tax_ids:
                    cgst = tax.amount

            product.sgst_value = sgst
            product.cgst_value = cgst
