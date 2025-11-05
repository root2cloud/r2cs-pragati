from email.policy import default

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RCMVoucher(models.Model):
    _name = "rcm.voucher"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "RCM Voucher"

    # Setting the rec_name to document_number
    _rec_name = 'document_number'

    document_number = fields.Char(
        string="Document Number",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _('New')
    )

    READONLYSTATES = {
        'complete': [('readonly' , True)]
    }
    purchase_account_id = fields.Many2one('account.account', string="Purchase Account", required=True)
    update_stock = fields.Boolean(string="Update Stock")
    due_date = fields.Date(string="Due Date")
    cost_centre_id = fields.Many2one('stock.location', "Cost Center", tracking=True, states=READONLYSTATES,  ondelete='cascade')
    narration = fields.Text(string="Narration")
    date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    partner_id = fields.Many2one('res.partner', string="Vendor", domain="[('supplier_rank', '>', 0)]", required=True)
    tds_vno = fields.Char(string="TDS/VNO")
    tds_amount = fields.Float(string="TDS Amount", compute="_compute_tds_amount", store=True)
    bill_date = fields.Date(string="Bill Date")
    igst_amount = fields.Float(string="IGST")
    delivery_terms = fields.Char(string="Delivery Terms")
    field_date = fields.Date(string="Field Date")
    tds_bill_account_id = fields.Many2one('account.account', string="TDS Bill Account")
    bill_number = fields.Char(string="Bill Number")
    place_of_supply = fields.Char(string="Place of Supply")
    payment_terms_id = fields.Many2one('account.payment.term', string="Payment Terms")
    attachment = fields.Binary(string="Attachment")
    attachment_filename = fields.Char(string="Attachment Filename")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted')
    ], default='draft', string="Status", tracking=True)
    order_line_ids = fields.One2many('rcm.voucher.line', 'voucher_id', string="Order Lines")

    @api.model
    def create(self, vals):
        if vals.get('document_number', _('New')) == _('New'):
            vals['document_number'] = self.env['ir.sequence'].next_by_code('rcm.voucher') or _('New')
        return super(RCMVoucher, self).create(vals)

    @api.onchange('xxxxx')
    def _onchange_partner_id(self):
        if self.partner_id:
            # Ensure the vendor name matches exactly
            if self.partner_id.name == 'VANGUARD SECURITY & FACILITY SERVICES':
                # Fetch service completion details for the specific vendor
                service_completions = self.env['service.completion'].search([('partner_id', '=', self.partner_id.id)])

                # Check if service completions are found
                if not service_completions:
                    raise UserError(_("No service completion details found for the selected vendor."))

                lines = []
                # Loop through each service completion and add it to the order line
                for service in service_completions:
                    # Fetch related lines directly if `service_line_ids` doesn't exist
                    related_lines = self.env['service.completion.line'].search([('service_id', '=', service.id)])
                    for services in related_lines:
                        vals = {
                            'service_order_id': service.id,
                            'product_id': services.product_id.id,
                            'description': services.description,
                            'last_purchase_cost': services.last_purchase_cost,
                            'price_subtotal' : services.price_subtotal,
                            'quantity': services.quantity,
                            'price_unit': services.price_unit,
                            'cgst': services.cgst_tax,
                            'sgst': services.sgst_tax,
                            'taxes_id': services.taxes_id,
                            'product_uom_id': services.product_uom_id.id,
                            'discount_type': services.discount_type,
                            'discount_amount': services.discount_amount,
                            'discounted_amount' : services.discounted_amount,
                            'price_tax_subtotal' : services.price_tax_subtotal,
                        }
                        lines.append((0, 0, vals))
                    # raise UserError(_("Invalid service completion record found."))
                self.order_line_ids = lines
            else:
                raise UserError(_("Vendor name does not match the expected name."))
        # else:
        #     raise UserError(_("Please select a vendor first."))

    # @api.depends('order_line_ids.amount')
    # def _compute_tds_amount(self):
    #     for record in self:
    #         record.tds_amount = sum(line.amount * 0.1 for line in record.order_line_ids)  # Example 10% TDS calculation

    def action_post(self):
        self.write({'state': 'posted'})

    def open_pdf_viewer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=rcm.voucher&id={}&field=attachment'.format(self.id),
            'target': 'new',
        }



class RCMVoucherLine(models.Model):
    _name = "rcm.voucher.line"
    _description = "RCM Voucher Line"

    voucher_id = fields.Many2one('rcm.voucher', string="RCM Voucher", ondelete="cascade")
    service_order_id = fields.Many2one('service.completion', string="Service Completion",domain="[('partner_id','=',parent.partner_id)]")
    product_id = fields.Many2one('product.product', string="Product")
    description = fields.Text(string="Description") #newly added
    last_purchase_cost = fields.Float(string="Last Purchase Cost") #newly added
    price_subtotal = fields.Float(string='SubTotal') #newly added
    price_unit = fields.Float(string="Unit Price")
    taxes_id = fields.Many2many('account.tax', string="Taxes")
    product_uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    discount_type = fields.Selection([
        ('percent', 'Percent'),
        ('fixed', 'Fixed')
    ], string="Discount Type",default="percent")
    discount_amount = fields.Float(string="Discount Amount")
    discounted_amount = fields.Float(string="Total Discount") #newly added

    item = fields.Char(string="Item")
    specifications = fields.Text(string="Specifications")
    unit = fields.Char(string="Unit")
    quantity = fields.Float(string="Quantity")
    l_service_completion = fields.Char(string="L-Service Completion")
    gross = fields.Float(string="Gross")
    discount = fields.Float(string="Discount")
    other_discount = fields.Float(string="Other Discount")
    freight = fields.Float(string="Freight")
    cgst = fields.Float(string="CGST")
    sgst = fields.Float(string="SGST")
    igst = fields.Float(string="IGST")
    rfq_no = fields.Char(string="RFQ No.")
    rfq_date = fields.Date(string="RFQ Date")
    pq_no = fields.Char(string="PQ No.")
    pq_date = fields.Date(string="PQ Date")
    po_no = fields.Char(string="PO No.")
    po_date = fields.Date(string="PO Date")
    mrn_no = fields.Char(string="MRN No.")
    mrn_date = fields.Date(string="MRN Date")
    type_of_purchase = fields.Selection([
        ('local', 'Local'),
        ('import', 'Import')
    ], string="Type of Purchase")
    price_tax_subtotal = fields.Float(string='Subtotal (with Taxes)',  store=True)

    @api.onchange('service_order_id')
    def onchange_service_order(self):
        for rec in self:
            if rec.service_order_id.service_completion_line_ids:
                services = rec.service_order_id.service_completion_line_ids[0]
                rec.product_id = services.product_id.id
                rec.description = services.description
                rec.last_purchase_cost = services.last_purchase_cost
                rec.price_subtotal = services.price_subtotal
                rec.quantity = services.quantity
                rec.price_unit = services.price_unit
                rec.cgst = services.cgst_tax
                rec.sgst = services.sgst_tax
                rec.taxes_id = services.taxes_id
                rec.product_uom_id = services.product_uom_id.id
                rec.discount_type = services.discount_type
                rec.discount_amount = services.discount_amount
                rec.discounted_amount = services.discounted_amount
                rec.price_tax_subtotal = services.price_tax_subtotal
                rec.gross = rec.service_order_id.total_wo_tax
