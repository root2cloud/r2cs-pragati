from odoo import models, fields, api
# from babel.numbers import format_currency


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

    qty_done = fields.Float(
        string='Total Quantity Done',
        compute='_compute_qty_done',
        store=False,
        readonly=True
    )

    date_done = fields.Text(  # Show only move dates
        'Move History (Date)',
        copy=False,
        readonly=True,
        help="All transfer dates for this product and location.",
        compute='_compute_date_done',
        store=False
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
    def _compute_qty_done(self):
        for quant in self:
            move_lines = self.env['stock.move.line'].search(
                [
                    ('location_dest_id', '=', quant.location_id.id),
                    ('product_id', '=', quant.product_id.id),
                    ('state', '=', 'done'),
                ]
            )
            quant.qty_done = sum(move_lines.mapped('qty_done'))

    @api.depends('location_id', 'product_id')
    def _compute_date_done(self):
        for quant in self:
            move_lines = self.env['stock.move.line'].search(
                [
                    ('location_dest_id', '=', quant.location_id.id),
                    ('product_id', '=', quant.product_id.id),
                    ('state', '=', 'done'),
                ],
                order='date asc'
            )

            if not move_lines:
                quant.date_done = "No move history found."
                continue

            result = "Move Dates:\n"
            result += "-" * 20 + "\n"

            for ml in move_lines:
                date_str = ml.date.strftime('%Y-%m-%d %H:%M') if ml.date else ''
                result += f"{date_str}\n"

            quant.date_done = result


# class StockQuant(models.Model):
#     _inherit = 'stock.quant'
#
#     move_location_id = fields.Many2one(
#         'stock.location',
#         string='From Location',
#         compute='_compute_move_location_id',
#         store=False
#     )
#
#     location_id = fields.Many2one(
#         'stock.location', "To Location",
#         compute="_compute_location_id", store=True, precompute=True, readonly=False,
#         check_company=True, required=True,
#         states={'done': [('readonly', True)]})
#
#     qty_done = fields.Float(
#         string='Total Quantity Done',
#         compute='_compute_qty_done',
#         store=False,
#         readonly=True
#     )
#
#     date_done = fields.Text(  # Show full move history
#         'Move History (Date, Price, Qty)',
#         copy=False,
#         readonly=True,
#         help="All transfer dates with unit price and quantity done.",
#         compute='_compute_date_done',
#         store=False
#     )
#
#     @api.depends('location_id', 'product_id')
#     def _compute_move_location_id(self):
#         for quant in self:
#             move_line = self.env['stock.move.line'].search(
#                 [
#                     ('location_dest_id', '=', quant.location_id.id),
#                     ('product_id', '=', quant.product_id.id)
#                 ],
#                 limit=1,
#                 order='id desc'
#             )
#             quant.move_location_id = move_line.location_id if move_line else False
#
#     @api.depends('location_id', 'product_id')
#     def _compute_qty_done(self):
#         for quant in self:
#             move_lines = self.env['stock.move.line'].search(
#                 [
#                     ('location_dest_id', '=', quant.location_id.id),
#                     ('product_id', '=', quant.product_id.id),
#                     ('state', '=', 'done'),
#                 ]
#             )
#             quant.qty_done = sum(move_lines.mapped('qty_done'))
#
#     @api.depends('location_id', 'product_id')
#     def _compute_date_done(self):
#         for quant in self:
#             move_lines = self.env['stock.move.line'].search(
#                 [
#                     ('location_dest_id', '=', quant.location_id.id),
#                     ('product_id', '=', quant.product_id.id),
#                     ('state', '=', 'done'),
#                 ],
#                 order='date asc'
#             )
#
#             if not move_lines:
#                 quant.date_done = "No move history found."
#                 continue
#
#             result = "Date                | Unit Price | Quantity\n"
#             result += "-" * 20 + "\n"
#
#             for ml in move_lines:
#                 date_str = ml.date.strftime('%Y-%m-%d %H:%M') if ml.date else ''
#                 unit_price = format_currency(ml.unit_price or 0.0, 'INR', locale='en_IN')
#                 qty = ml.qty_done
#                 result += f"{date_str:<20} | {unit_price:<12} | {qty:.2f}\n"
#
#             quant.date_done = result
