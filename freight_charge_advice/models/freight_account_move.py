from odoo import models, api, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _create_freight_charge_advice(self):
        # Fetch the Transport Charges product once
        transport_product = self.env['product.product'].search([
            ('name', '=', 'Transport Charges')  # Replace with product ID or config parameter if needed
        ], limit=1)

        if not transport_product:
            self.env['ir.logging'].create({
                'name': 'Freight Advice',
                'type': 'server',
                'level': 'WARNING',
                'message': "Transport Charges product not found.",
                'func': '_create_freight_charge_advice',
            })
            return

        # Filter invoices with Transport Charges product
        valid_invoices = self.filtered(lambda inv: inv.is_sale_document() and
                                                   inv.pos_order_ids and
                                                   inv.state == 'posted' and
                                                   any(line.product_id.id == transport_product.id
                                                       for line in inv.invoice_line_ids))

        for invoice in valid_invoices:
            # Avoid duplicate advice
            if self.env['freight.charge.advice'].search_count([('invoice_id', '=', invoice.id)]):
                continue

            # Get transport charge lines
            transport_lines = invoice.invoice_line_ids.filtered(
                lambda line: line.product_id.id == transport_product.id
            )
            if not transport_lines:
                continue  # Skip if no transport lines (redundant but safe)
            # Default fallback vendor and journal
            default_vendor = self.env['res.partner'].search([
                ('supplier_rank', '>', 0)
            ], limit=1) or invoice.partner_id



            default_journal = self.env['account.journal'].search([
                ('company_id', '=', invoice.company_id.id)
            ], limit=1)

            # Build freight advice order lines only for transport products
            order_lines = [(0, 0, {
                'product_id': transport_product.id,
                'account_id': default_vendor.id,
                'amount': sum(invoice.invoice_line_ids.filtered(
                    lambda line: line.product_id == transport_product
                ).mapped('price_subtotal')),
                'remarks': f"Freight charge for {transport_product.name} from POS invoice {invoice.name}"
            })]

            # Create freight charge advice
            self.env['freight.charge.advice'].create({
                'invoice_id': invoice.id,
                'account_id': default_vendor.id,
                'journal_id': default_journal.id if default_journal else False,
                'vehicle_number': 'UNKNOWN',  # You can replace or update this dynamically
                'order_line_ids': order_lines,
                'narration': f"Auto-generated from POS invoice {invoice.name}",
            })


    @api.model_create_multi
    def create(self, vals_list):
        invoices = super().create(vals_list)
        for invoice in invoices:
            if invoice.is_sale_document() and invoice.pos_order_ids:
                invoice._create_freight_charge_advice()
        return invoices

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        # Only trigger advice creation on posting
        if vals.get('state') == 'posted':
            self._create_freight_charge_advice()
        return res
