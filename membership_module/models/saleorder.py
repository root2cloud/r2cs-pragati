from odoo import api, fields, models
from datetime import datetime, timedelta

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        invoices = super(SaleAdvancePaymentInv, self).create_invoices()

        for order in self:
            for sale_order in order.sale_order_ids:
                invoice_date = False 
                if sale_order.invoice_date:
                    invoice_date =sale_order.invoice_date

                plan_ids = []  # List to store plan_ids
                plan_duration_total = 0  # Total plan duration
                slot_ids = []  # List to store repeated slot_ids
                membership_ids = []
                slot_names = []
               
            
                for line in sale_order.order_line:
                    if line.product_template_id and line.product_template_id.plan_id:
                        plan_id = line.product_template_id.plan_id
                        plan_ids.append(plan_id.id)
                        membership_ids.extend(plan_id.membership_id.ids)
                        plan_duration_total += plan_id.plan_duration * line.product_uom_qty

                slot_descriptions = self.env["slots.description"].search([("plan_id.membership_id", "in", membership_ids)])
                print(slot_descriptions)
               
                

                slot_ids.extend(slot_descriptions.ids * int(plan_duration_total))

                ownslots = []
                slot_date = invoice_date
                for slot_id in slot_ids:
                    slot = self.env['slots.description'].browse(slot_id)
            
                    if slot:
                        slot_date = slot_date + timedelta(days=3) if slot_date else False
                        ownslots.append((0, 0, {'slot_id': slot_id,'slot_name': slot.slot_name,'slot_date': slot_date}))    

                existing_plan_count = sale_order.partner_id.plan_count
                existing_allocated_slots = sale_order.partner_id.allocated_slots
                
                sale_order.partner_id.write({
                    'plan_ids': [(6, 0, plan_ids)],  # Replace existing plan_ids
                    'plan_count': existing_plan_count + plan_duration_total,
                    'allocated_slots':  existing_allocated_slots + plan_duration_total * 8,
                    'partner_slot_line_ids': ownslots
                })
        return invoices



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    slot_id = fields.Integer(string = "slot Number", readonly=True)
    invoice_date = fields.Date(string ="Invoice date", compute='_compute_invoice_date', store=True)

    @api.depends('invoice_ids.invoice_date')
    def _compute_invoice_date(self):
        for order in self:
            if order.invoice_ids:
                order.invoice_date = order.invoice_ids.invoice_date
                if order.invoice_date:
                    order.update_slot_dates()
                 
            else:
                order.invoice_date = False


    def update_slot_dates(self):
        for order in self:
            invoice_date = order.invoice_date
            if invoice_date:
                for partner in order.partner_id:
                    for slot_line in partner.partner_slot_line_ids:
                        if not slot_line.slot_date:
                            invoice_date += timedelta(days=3)
                            slot_line.slot_date = invoice_date

