from odoo import fields,models,api

class ResZip(models.Model):
    _name = 'res.zip'
    _description = 'Adding Zip Codes and Locations'
    _rec_name = 'zip_field'

    location_field = fields.Char(string="location")
    zip_field = fields.Char(string="Zip_code")


class Partner(models.Model):
    _inherit = 'res.partner'

    zip_id = fields.Many2one('res.zip', string='ZIP Code', help='Select ZIP Code')

    # Other existing fields and methods...

