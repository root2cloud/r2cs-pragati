import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api
import io

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    qr_code = fields.Binary(string='QR Code', readonly=True, copy=False)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        # Generate QR code upon order confirmation
        qr_code_data = self.generate_qr_code()

        # Encode the QR code data as base64 before saving
        qr_code_base64 = base64.b64encode(qr_code_data.getvalue())
        self.write({'qr_code': qr_code_base64})

        for record in self:
            if record.picking_ids:
                record.picking_ids.write({'qr_code_label':self.qr_code})
            else:
                record.picking_ids.qr_code_label = False

        return res

    def generate_qr_code(self):
        # Generate QR code based on order details
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        products_data = ', '.join(record.product_id.name for record in self.order_line if record.product_id)
        order_info = f"Order ID: {self.id}, Customer: {self.partner_id.name}, Total: {self.amount_total}, Products: {products_data}"
        qr.add_data(order_info)
        qr.make(fit=True)

        # Create an in-memory buffer to store the QR code image
        qr_code_image = io.BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_code_image, format='PNG')

        # Reset the buffer to read from the start before returning it
        qr_code_image.seek(0)

        return qr_code_image

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_delivery_status(self):
        super(SaleOrder, self)._compute_delivery_status()  # Call super method to retain original functionality
        for order in self:
            if not order.picking_ids or all(p.state == 'cancel' for p in order.picking_ids):
                order.delivery_status = False
            elif all(p.state in ['done', 'sign', 'cancel'] for p in order.picking_ids):
                order.delivery_status = 'full'
            elif any(p.state in ['done', 'sign'] for p in order.picking_ids):
                order.delivery_status = 'partial'
            else:
                order.delivery_status = 'pending'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        domain="[('category_id', '=', product_uom_category_id)]")

    @api.depends('product_template_id')
    def _compute_product_uom(self):
        # Call the original method
        super(SaleOrderLine, self)._compute_product_uom()

        # Add your custom logic
        kg_uom = self.env['uom.uom'].search([('name', '=', 'kg')], limit=1)
        uom_leafy = self.env['uom.uom'].search([('name', '=', '100grams')], limit=1)
        uom_normal = self.env['uom.uom'].search([('name', '=', '250grams')], limit=1)

        for rec in self:
            if (
                rec.product_template_id
                and rec.product_template_id.uom_id
                and rec.product_template_id.uom_id == kg_uom
                and rec.product_template_id.radio_field == 'leafy'
            ):
                rec.product_uom = uom_leafy.id
            elif (
                rec.product_template_id
                and rec.product_template_id.uom_id
                and rec.product_template_id.uom_id == kg_uom
                and rec.product_template_id.radio_field == 'normal'
            ):
                rec.product_uom = uom_normal.id
            else:
                rec.product_uom = rec.product_uom.id

