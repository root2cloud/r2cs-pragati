# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, SUPERUSER_ID

PHY_WRITABLE_FIELDS = [
    'acs_allowed_online_booking',
    'acs_basic_info',
    'acs_allow_home_appointment',
    'acs_show_fee_on_booking',
]

class User(models.Model):
    _inherit = ['res.users']

    acs_allowed_online_booking = fields.Boolean(related='physician_id.allowed_online_booking', string="Acs Allowed Online Booking", readonly=False, related_sudo=False)
    acs_basic_info = fields.Char(related='physician_id.basic_info', string="Acs Basic Info",readonly=False, related_sudo=False)
    acs_allow_home_appointment = fields.Boolean(related='physician_id.allow_home_appointment', string="Acs Allowed Home Visit Booking", readonly=False, related_sudo=False)
    acs_show_fee_on_booking = fields.Boolean(related='physician_id.show_fee_on_booking', string="Acs Show Fee On Booking", readonly=False, related_sudo=False)

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + PHY_WRITABLE_FIELDS

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + PHY_WRITABLE_FIELDS