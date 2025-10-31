from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class DiseaseDetails(models.Model):
    _name = "disease.details"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Menure Request'


    name = fields.Char(string="Disease Name")
    request_date = fields.Date(string='Request Date',
                               default=fields.Date.context_today, required=True,
                               tracking=True)
    crop_id = fields.Many2one('crop.requests', string='Crop', required=True,
                              tracking=True)
    farmer_emp = fields.Many2one("res.partner", string="Farmer", related='location_dest_id.farmer_emp_id')
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location", store=True, readonly=False, required=True,)
    note = fields.Text(string='Note', tracking=True)
    disease_image = fields.Binary(string='Image', tracking=True)

    @api.onchange('crop_id')
    def _onchange_crop_id(self):
        if self.crop_id:
            location_dest_id = self.crop_id.location_dest_id.id
            self.location_dest_id = location_dest_id
            farmer_emp = self.crop_id.farmer_emp.id
            self.farmer_emp = farmer_emp

