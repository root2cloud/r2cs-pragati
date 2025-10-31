from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    move_location_id = fields.Many2one(
        'stock.location',
        string='From Location',
        compute='_compute_move_location_id',
        store=False
    )

    location_id = fields.Many2one(
        'stock.location', "To Location",
        compute="_compute_location_id", store=True, precompute=True, readonly=False,
        check_company=True, required=True,
        states={'done': [('readonly', True)]})

    date_done = fields.Datetime(
        'Date of Transfer',
        copy=False,
        readonly=True,
        help="Date at which the transfer has been processed or cancelled.",
        compute='_compute_date_done',
        store=False  # Set to store=True if you need to store it in the database
    )

    @api.depends('location_id', 'product_id')
    def _compute_move_location_id(self):
        for quant in self:
            move_line = self.env['stock.move.line'].search(
                [
                    ('location_dest_id', '=', quant.location_id.id),
                    ('product_id', '=', quant.product_id.id)
                ],
                limit=1,
                order='id desc'
            )
            quant.move_location_id = move_line.location_id if move_line else False

    @api.depends('location_id', 'product_id')
    def _compute_date_done(self):
        for quant in self:
            move_line = self.env['stock.move.line'].search(
                [
                    ('location_dest_id', '=', quant.location_id.id),
                    ('product_id', '=', quant.product_id.id),
                    ('state', '=', 'done'),
                ],
                limit=1,
                order='date desc'
            )
            quant.date_done = move_line.date if move_line else False