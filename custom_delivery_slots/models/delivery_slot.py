from odoo import api, fields, models
from datetime import datetime, timedelta, time
from odoo import exceptions

class DeliverySlot(models.Model):
    _name = 'delivery.slot'
    _description = 'Delivery slot'

    name = fields.Char(string='Slot', help="Slot name")
    time_before = fields.Float(string='Time Before (hours)', digits=(2, 2), default=11.30)

    @api.constrains('name')
    def _check_valid_day(self):
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for record in self:
            if record.name not in valid_days:
                raise exceptions.ValidationError(f"Invalid day '{record.name}'. Please enter a valid day of the week.")

    def convert_to_time(self, float_value):
        hours, minutes = divmod(int(float_value * 60), 60)
        return time(hours, minutes)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_day = fields.Char(string='Delivery Day')
    slot_id = fields.Many2one('delivery.slot', string='Slot ID')

    @api.model
    def create(self, vals):
        # Get the current date and time
        current_datetime = datetime.now()

        # Find the next available delivery day from the delivery.slot model starting from the day after the current day
        next_day = current_datetime.date() + timedelta(days=1)
        delivery_slot = None

        while not delivery_slot:
            delivery_slot = self.env['delivery.slot'].search([('name', '=', next_day.strftime('%A'))], limit=1)
            next_day += timedelta(days=1)

        # Convert time_before to a time object
        delivery_time = delivery_slot.convert_to_time(delivery_slot.time_before)

        # Check if the current time is before the specified time_before
        if current_datetime.time() <= delivery_time:
            delivery_day = delivery_slot.name
        else:
            # If the current time is after the specified time_before, consider the next available delivery day
            next_day = current_datetime.date() + timedelta(days=2)
            next_delivery_slot = None

            while not next_delivery_slot:
                next_delivery_slot = self.env['delivery.slot'].search([('name', '=', next_day.strftime('%A'))], limit=1)
                next_day += timedelta(days=1)

            delivery_day = next_delivery_slot.name
            delivery_slot = next_delivery_slot

        # Set the delivery day and slot_id based on the found delivery_slot
        vals.update({
            'delivery_day': delivery_day,
            'slot_id': delivery_slot.id,
        })

        return super(SaleOrder, self).create(vals)
