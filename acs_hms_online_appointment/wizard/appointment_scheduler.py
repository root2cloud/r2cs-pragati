# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT


class AppointmentSchedulerWizard(models.TransientModel):
    _name = 'appointment.scheduler.wizard'
    _description = 'Appointment Scheduler Wiz'

    schedule_id = fields.Many2one("appointment.schedule", string="Appointment schedule", required=True, ondelete="cascade")
    start_date = fields.Date('Start Date', required=True, default=fields.Date.today)
    end_date = fields.Date('End Date',required=True)
    booking_slot_time = fields.Integer("Minutes in each slot", help="Configure your slot length, 15-30min.")
    allowed_booking_per_slot = fields.Integer("Allowed Booking per Slot", help="No of allowed booking per slot.")
    department_id = fields.Many2one('hr.department', string="Department")
    physician_ids = fields.Many2many('hms.physician', string="Physicians")
    acs_own_schedule = fields.Boolean("Own Schedule")
    schedule_ids = fields.Many2many("appointment.schedule", "wiz_appointment_schedule_rel", "wiz_id", "schedule_id", compute="get_schedule_ids", string="schedules")

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for wizard in self:
            if wizard.start_date > wizard.end_date:
                raise ValidationError(_("Scheduler 'Start Date' must be before 'End Date'."))
        return True

    #ACS: Can be dpne by adding two fields in view with domain and optinal show. but it was applying same 
    #domain on both fields so done with extra m2m field.
    @api.depends('acs_own_schedule')
    def get_schedule_ids(self):
        Schedule = self.env['appointment.schedule']
        for rec in self:
            domain = []
            if rec.acs_own_schedule:
                domain = [('acs_own_schedule','=',True),('physician_ids.user_id','=',self.env.user.id)]
            rec.schedule_ids = Schedule.search(domain)

    @api.model
    def default_get(self, fields):
        res = super(AppointmentSchedulerWizard, self).default_get(fields)
        if self._context.get('acs_own_scheduling'):
            res['physician_ids'] = self.env.user.sudo().physician_ids.ids
            res['acs_own_schedule'] = True
        return res

    @api.onchange('schedule_id')
    def onchange_schedule(self):
        company_id = self.env.user.company_id
        if self.schedule_id and self.schedule_id.company_id:
            company_id = self.schedule_id.company_id
            self.booking_slot_time = company_id.booking_slot_time
            self.allowed_booking_per_slot = company_id.allowed_booking_per_slot
            self.department_id = self.schedule_id.department_id and self.schedule_id.department_id.id or False
            self.physician_ids = [(6,0,self.schedule_id.physician_ids.ids)]

    def appointment_slot_create_wizard(self):
        Slot = self.env['appointment.schedule.slot']
        # create slot
        start_date = self.start_date
        end_date = self.end_date

        while (start_date != end_date + timedelta(days=1)):
            slot_found = Slot.search([('schedule_id','=',self.schedule_id.id), ('slot_date','=',start_date.strftime(DEFAULT_SERVER_DATE_FORMAT))])
            if slot_found:
                raise UserError(_("Appointment Slot exist for date %s." % start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)))
            Slot.create_appointment_slot(start_date, self.schedule_id, self.booking_slot_time, self.allowed_booking_per_slot, self.physician_ids, self.department_id)
            start_date = start_date  + timedelta(days=1)
        end_scheduler =(end_date - timedelta(days=7)).strftime(DEFAULT_SERVER_DATE_FORMAT)