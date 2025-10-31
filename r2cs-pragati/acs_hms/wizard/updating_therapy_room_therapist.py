from odoo import models, api, fields
from datetime import date, datetime, timedelta
from pytz import timezone
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import pytz


class AcsTherapistRoomWizard(models.TransientModel):
    _name = 'acs.therapist.room.wizard'
    _description = 'Therapist and Room Selection Wizard'

    product_id = fields.Many2one('product.product', string='Procedure', 
        change_default=True, ondelete='restrict',  required=True)
 
    therapist_id = fields.Many2one('hms.therapist', string='Therapist')
    therapy_room_id = fields.Many2one('therapy.rooms', string='Therapy Room')
    date = fields.Datetime("Date",)
    date_stop = fields.Datetime("End Date",)
   


    @api.onchange('product_id','date')
    def onchange_date_and_product(self):
        if self.product_id and self.product_id.procedure_time and self.date:
            self.date_stop = self.date + timedelta(hours=self.product_id.procedure_time)



    @api.onchange('date','date_stop')
    def _onchange_appointment_date_time(self):
        if self.date and self.date_stop:
            requested_start_time = self.date
            utc = pytz.utc
            ist = pytz.timezone('Asia/Kolkata')

            utc_start_datetime = self.date  
            requested_start_time = utc_start_datetime.astimezone(ist)
            utc_end_datetime = self.date_stop  
            requested_end_time = utc_end_datetime.astimezone(ist)
            
             
            overlapping_appointments = self.env['acs.patient.procedure'].search([
                ('therapist_id', '!=', False),
              
            ])
           
            booked_therapists = [] 
            booked_therapy_names = []
            for appointment in overlapping_appointments :
                for a in appointment:
                    if a.state != 'done':
                        utc_start_datetime = a.date  
                        start_date_ist = utc_start_datetime.astimezone(ist)
                        if a.date_stop :
                            utc_end_datetime = a.date_stop 
                            end_date_ist = utc_end_datetime.astimezone(ist)
                            if (start_date_ist <= requested_start_time <= end_date_ist) or (start_date_ist <= requested_end_time <= end_date_ist) or (requested_start_time <= start_date_ist <= requested_end_time) or (requested_start_time <=  end_date_ist <= requested_end_time):                         
                                if a.therapist_id.id not in booked_therapists:
                                    booked_therapists.append(a.therapist_id.id)
                                if a.therapy_room_id:
                                    booked_therapy_names.append(a.therapy_room_id.id)
                
            if booked_therapists or booked_therapy_names:
                domain_filter = {
                    'therapist_id': [('id', 'not in', booked_therapists)],
                    'therapy_room_id': [('id', 'not in', booked_therapy_names)]
                }
                return {
                    'domain': domain_filter
                }
            else:
                return {}

    

    def action_apply(self):
        
        procedure_id = self.env.context.get('active_id')
        procedure = self.env['acs.patient.procedure'].browse(procedure_id)

        procedure.therapist_id = self.therapist_id
        procedure.therapy_room_id = self.therapy_room_id
        procedure.date = self.date
        procedure.date_stop = self.date_stop
        procedure.product_id = self.product_id
    

        return {'type': 'ir.actions.act_window_close'}
