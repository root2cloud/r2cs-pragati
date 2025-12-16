from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        compute='_compute_location_id',
        store=False
    )

    # ============= NEW GST VALUE FIELDS =============
    sgst_value = fields.Float(
        string='SGST',
        compute='_compute_gst_values',
        store=True,
        digits=(16, 2),
        help='State Goods and Services Tax value'
    )
    cgst_value = fields.Float(
        string='CGST',
        compute='_compute_gst_values',
        store=True,
        digits=(16, 2),
        help='Central Goods and Services Tax value'
    )
    igst_value = fields.Float(
        string='IGST',
        compute='_compute_gst_values',
        store=True,
        digits=(16, 2),
        help='Integrated Goods and Services Tax value'
    )
    total_tax_value = fields.Float(
        string='Total Tax',
        compute='_compute_gst_values',
        store=True,
        digits=(16, 2),
        help='Total tax value in rupees'
    )

    # ================================================

    def _compute_location_id(self):
        """Compute location from first stock quant"""
        for product in self:
            quant = self.env['stock.quant'].search(
                [('product_id', '=', product.id)],
                limit=1
            )
            product.location_id = quant.location_id

    @api.depends('taxes_id', 'list_price')
    def _compute_gst_values(self):
        """
        Calculate actual GST values in rupees.
        Case-insensitive tax name matching (handles sgst, SGST, Sgst, etc.)

        Handles:
        1. Group taxes: "GST 5%(SGST 2.5%+CGST 2.5%)"
        2. Individual taxes: "SGST Sale 2.5%" or "sgst sale 2.5%"
        3. IGST taxes: "IGST Sale 5%" or "igst sale 5%"

        Formula: Tax Value = (Price × Tax Rate) / 100
        """
        for product in self:
            sgst_rate = 0.0
            cgst_rate = 0.0
            igst_rate = 0.0

            # Extract tax rates from taxes_id
            for tax in product.taxes_id:
                # Normalize to uppercase for comparison (handles lowercase, UPPERCASE, MixedCase)
                tax_name = (tax.name or '').strip().upper()

                # If tax has child taxes (group tax)
                if tax.children_tax_ids:
                    for child_tax in tax.children_tax_ids:
                        child_name = (child_tax.name or '').strip().upper()

                        if 'SGST' in child_name:
                            sgst_rate = child_tax.amount
                        elif 'CGST' in child_name:
                            cgst_rate = child_tax.amount
                        elif 'IGST' in child_name:
                            igst_rate = child_tax.amount

                # Direct individual taxes (no parent)
                elif 'SGST' in tax_name:
                    sgst_rate = tax.amount
                elif 'CGST' in tax_name:
                    cgst_rate = tax.amount
                elif 'IGST' in tax_name:
                    igst_rate = tax.amount

            # Use list_price as base for calculation
            base_price = product.list_price or 0.0

            # Calculate tax values: (Base × Rate) / 100
            product.sgst_value = (base_price * sgst_rate) / 100.0
            product.cgst_value = (base_price * cgst_rate) / 100.0
            product.igst_value = (base_price * igst_rate) / 100.0
            product.total_tax_value = product.sgst_value + product.cgst_value + product.igst_value
