# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError


class DamageLossDetails(models.Model):
    _name = 'damage.loss'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Agriculture Management"

    name = fields.Char(string='Name', required=True, tracking=True)
    crop_id = fields.Many2one('crop.requests', string='Crop', required=True,
                              tracking=True)
    location_dest_id = fields.Many2one(
        'stock.location', "Damage Location",
        store=True, readonly=False,required=True,)
    damage_loss_type = fields.Selection(
        [('damage', 'Damage'), ('loss', 'Loss'),('not_germ','Not_Germinated')], string='Damage/Loss Type',
        required=True, tracking=True)
    damage_loss_date = fields.Date(string='Damage/Loss Date',
                                   default=fields.Date.context_today,
                                   required=True, tracking=True)
    note = fields.Text(string='Damage/Loss Description',tracking=True)
    damage_loss_image = fields.Binary(string='Image', tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible user',
                              default=lambda self: self.env.user)
    
    def cancel_crop_damage(self):
            """
            Cancels crop damage if crop state is "draft,sowing and confirm".
            """
            for record in self:
                if record.crop_id and record.crop_id.state == "draft" or record.crop_id.state == "confirm" or record.crop_id.state == "growing" :
                    record.crop_id.write({'note_reason': record.note})
                    record.crop_id.write({'state': 'cancel'})

    @api.onchange('crop_id')
    def _onchange_crop_id(self):
        if self.crop_id:
            if self.crop_id.state in ["yeild","harvest","cancel"]:
                raise ValidationError(_("You cannot cancel this crop as it is in Harvesting/Yeild stage or it has been already Cancelled"))
            else:
                location_dest_id = self.crop_id.location_dest_id.id
                self.location_dest_id = location_dest_id





    




