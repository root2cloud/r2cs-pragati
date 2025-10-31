from odoo import fields, models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    original_bills = fields.Binary(string="Attachment", attachment=True,tracking=True)
    original_bills_filename = fields.Char(string="File Name",tracking=True)

    def open_pdf_viewer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=stock.picking&id={}&field=original_bills'.format(self.id),
            'target': 'new',

        }