from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from datetime import datetime, timedelta

class WebsiteSaleExtended(WebsiteSale):
    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        res = super(WebsiteSaleExtended, self).cart(**post)

        # Compute the delivery_day when the customer enters the cart page
        sale_order = request.website.sale_get_order()
        
        if sale_order:
            # Get the current date and time
            current_datetime = datetime.now()

            # Find the next available delivery day from the delivery.slot model starting from the day after the current day
            next_day = current_datetime.date() + timedelta(days=1)
            delivery_slot = None

            while not delivery_slot:
                delivery_slot = request.env['delivery.slot'].search([('name', '=', next_day.strftime('%A'))], limit=1)
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
                    next_delivery_slot = request.env['delivery.slot'].search([('name', '=', next_day.strftime('%A'))], limit=1)
                    next_day += timedelta(days=1)

                delivery_day = next_delivery_slot.name
                delivery_slot = next_delivery_slot

            # Set the delivery day and slot_id based on the found delivery_slot
            sale_order.delivery_day = delivery_day
            sale_order.slot_id = delivery_slot.id

        # Add the sale_order to the qcontext
        res.qcontext['sale_order'] = sale_order
        return res
