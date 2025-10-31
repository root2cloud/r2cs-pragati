from odoo import fields, models, api, _


class CancelCropWizard(models.TransientModel):
    _name = 'cancel.crop.wizard'
    _description = "This wizard cancel the crop and create a record in the damage loss menu"

    name = fields.Char(string='Short Name', required=True)
    crop_id = fields.Many2one('crop.requests', string='Crop', required=True)
    damage_loss_type = fields.Selection(
        [('damage', 'Damage'), ('loss', 'Loss'),('not_germ','Not_Germinated')], string='Damage/Loss Type',
        required=True)
    location_dest_id = fields.Many2one(
        'stock.location', "Damage Location",
        store=True, readonly=False,required=True,)
    damage_loss_date = fields.Date(string='Damage/Loss Date',
                                   default=fields.Date.context_today,
                                   required=True)
    note = fields.Text(string='Damage/Loss Description',required=True)
    damage_loss_image = fields.Binary(string='Image')
    farmer_emp = fields.Many2one("res.partner", string="Farmer")
    crop_request_id = fields.Many2one('crop.requests', string='Crop Request')

    def action_confirm_damage(self):

        crop_record = self.env['damage.loss'].create({
        'name': self.name,
        'crop_id': self.crop_id.id,
        'location_dest_id':self.location_dest_id.id,
        'damage_loss_type': self.damage_loss_type,
        'damage_loss_date': self.damage_loss_date,
        'damage_loss_image': self.damage_loss_image,
        'note': self.note,
        })
        self.cancel_crop_note()

        active_ids = self.env.context.get('active_ids')
        crop = self.env['crop.requests'].browse(active_ids)
        for crops in crop:
            crops.damage_crop_record()
            crops.crop_plan_id.cancel_planning()

    @api.model
    def default_get(self, fields):
        res = super(CancelCropWizard, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        crop = self.env['crop.requests'].browse(active_id)
        res['crop_id'] = crop.id
        res['location_dest_id'] = crop.location_dest_id.id
        res['farmer_emp'] = crop.farmer_emp.id
        return res
    
    def cancel_crop_note(self):
        for record in self:
            if record.crop_id:
                record.crop_id.write({'note_reason': record.note})


    