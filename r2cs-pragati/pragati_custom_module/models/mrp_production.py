from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging
# logger = logging.getLogger(name_)Product Quantity Loss
_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    total_quantity = fields.Float(string="Final Product Quantity")
    product_quantity_loss = fields.Float(string="Product Quantity Loss", compute="_compute_product_quantity_loss", store=True)

    @api.depends('product_qty', 'total_quantity')
    def _compute_product_quantity_loss(self):
        for record in self:
            _logger.info(f"Computing product_quantity_loss for MO {record.id}: product_qty={record.product_qty}, total_quantity={record.total_quantity}")
            if record.product_qty and record.total_quantity:
                record.product_quantity_loss = record.product_qty - record.total_quantity
            else:
                record.product_quantity_loss = 0.0

    @api.constrains('total_quantity')
    def _check_final_product_quantity(self):
        for record in self:
            if record.total_quantity < 0:
                raise ValidationError("Final Product Quantity cannot be negative.")

    def _update_stock_quant(self):
        """
        Updates the stock.quant model's quantity field to reflect the total_quantity (Final Product Quantity).
        Also updates the stock.move's quantity_done for consistency.
        """
        for record in self:
            if record.state in ['progress', 'done'] and record.total_quantity >= 0:
                move = record.move_finished_ids.filtered(
                    lambda m: m.product_id == record.product_id and m.state not in ['cancel', 'done']
                )[:1]
                if move:
                    move.write({'quantity_done': record.total_quantity})
                else:
                    move = self.env['stock.move'].create({
                        'name': record.name or _('New Move for %s') % record.product_id.name,
                        'product_id': record.product_id.id,
                        'product_uom_qty': record.product_qty,
                        'quantity_done': record.total_quantity,
                        'product_uom': record.product_uom_id.id,
                        'location_id': record.location_src_id.id or self.env.ref('stock.stock_location_stock').id,
                        'location_dest_id': record.location_dest_id.id or self.env.ref('stock.stock_location_stock').id,
                        'production_id': record.id,
                        'state': 'draft',
                    })

                location = record.location_dest_id or self.env.ref('stock.stock_location_stock')
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', record.product_id.id),
                    ('location_id', '=', location.id),
                ], limit=1)
                if quant:
                    quant.write({'quantity': record.total_quantity})
                else:
                    self.env['stock.quant'].create({
                        'product_id': record.product_id.id,
                        'location_id': location.id,
                        'quantity': record.total_quantity,
                        'in_date': fields.Datetime.now(),
                    })

    @api.model
    def create(self, values):
        if 'total_quantity' not in values:
            values['total_quantity'] = 0.0
        record = super(MrpProduction, self).create(values)
        record._update_stock_quant()
        return record

    def write(self, values):
        _logger.info(f"Write called with values: {values}")
        result = super(MrpProduction, self).write(values)
        if 'total_quantity' in values:
            _logger.info(f"Updating stock and product_quantity_loss for total_quantity: {values['total_quantity']}")
            self._update_stock_quant()
            self._compute_product_quantity_loss()
        return result



from odoo import fields, models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    product_quantity_loss = fields.Float(
        string="Product Quantity Loss",
        related="move_id.production_id.product_quantity_loss",
        store=False,
        readonly=True,
        help="Product Quantity Loss from the associated Manufacturing Order"
    )