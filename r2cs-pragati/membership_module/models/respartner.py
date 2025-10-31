from odoo import models, fields, api
from datetime import datetime, timedelta, time

class ResPartner(models.Model):
	_inherit = 'res.partner'

	plan_count = fields.Integer(string = "Plan Count")
	allocated_slots = fields.Integer("Allocated Slots")
	plan_ids = fields.Many2many("membership.planning", string="Plan Names")
	partner_slot_line_ids = fields.One2many('partner.ownslots', 'partner_id', string="Slot Line Ids")
	partner_payment_slot_line_ids = fields.One2many('partner.paymentslot', 'partner_id', string="Slot Payment Line Ids")
	

	@api.model
	def _cron_remove_slots(self):
	    current_datetime = fields.Datetime.now()
	    print('^^^^^',current_datetime)
	    partners = self.env['res.partner'].search([])
	    for partner in partners:
	        slots_to_remove = partner.partner_slot_line_ids.filtered(lambda slot: slot.slot_date and fields.Datetime.from_string(slot.slot_date) < current_datetime)
	        print('^^^^^',slots_to_remove)
	        if slots_to_remove:
	        	partner.allocated_slots -= len(slots_to_remove)
	        	slots_to_remove.unlink()
	        	payment_slots_to_remove = partner.partner_payment_slot_line_ids.filtered(lambda payment_slot: payment_slot.slot_id in slots_to_remove.mapped('id'))
	        	if payment_slots_to_remove:
	        		payment_slots_to_remove.unlink()
	

	@api.model
	def _cron_payment_slots_save(self):
		print('^^^^^>>>>>>>>>>>>>>>>>>>>>>>>>>>')
		current_datetime = fields.Datetime.now()
		partners = self.env['res.partner'].search([('plan_ids', '!=', False)])
		for partner in partners:
			valid_slot_lines = partner.partner_slot_line_ids.filtered(lambda s: s.slot_date)
			for slot_line in valid_slot_lines:
				slot_datetime = slot_line.slot_date
				slot_datetime = datetime.combine(slot_line.slot_date, datetime.min.time())
				time_difference = current_datetime - slot_datetime
				print(time_difference)
				# if 0 < time_difference.total_seconds() < 7 * 3600:
				print("Slot date:", slot_datetime)
				print('slot_id', slot_line.id)
				slot_id = slot_line.id
				slot_payments = self.env['partner.paymentslot'].search([('slot_id', '=', slot_id)])
				print(slot_payments)
			
				if not slot_payments:
					slot_description = self.env['slots.description'].browse(slot_line.slot_id.id)
					sale_order = self.env['sale.order'].search([('partner_id', '=', partner.id), ('slot_id', '=', slot_line.slot_id.id)])
					if not sale_order:
						sale_order_line_vals_list = []
						for product_line in slot_description.product_line_ids:
							sale_order_line_vals = {
							'product_id': product_line.product_id.id,
	                        'name': product_line.product_id.display_name,
	                        'product_uom_qty': product_line.quantity,
	                        'price_unit': product_line.price_unit,
	                        'product_uom': product_line.uom.id,

							}
							sale_order_line_vals_list.append((0, 0, sale_order_line_vals))
						sale_order_vals = {
						'partner_id': partner.id,
						'order_line': sale_order_line_vals_list,
						'slot_id': slot_line.slot_id.id
						}
						sale_order = self.env['sale.order'].create(sale_order_vals)
				else:
					print('^^^^^>>>>>>>>>>>>>>>>>>>>>>>>>>> sale order creation')
					for slot_payment in slot_payments:
						uom = self.env['uom.uom'].search([('name', '=', slot_payment.uomName)], limit=1)
						sale_order_line_vals_list = []
						sale_order_line_vals ={
						'product_id': slot_payment.product_id,
						'name': slot_payment.product_name,
	                    'product_uom_qty': slot_payment.quantity,
	                    'price_unit': slot_payment.price_unit,
	                    'product_uom': uom.id if uom else False,
						}
						sale_order_line_vals_list.append((0, 0, sale_order_line_vals))

					sale_order_vals = {
						'partner_id': partner.id,
						'order_line': sale_order_line_vals_list,
						'slot_id': slot_line.slot_id.id
						}
					sale_order = self.env['sale.order'].create(sale_order_vals)



			



	# @api.model
	# def _cron_next_delivery_slots(self):
	# 	print('^^^^^>>>>>>>>>>>>>>>>>>>>>>>>>>>')
	# 	partners = self.env['res.partner'].search([('plan_ids', '!=', False)])
	# 	for partner in partners:
	# 		valid_slot_lines = partner.partner_slot_line_ids.filtered(lambda s: s.slot_date)
	# 		sorted_slot_lines = valid_slot_lines.sorted(key=lambda s: s.slot_date)
	# 		earliest_slot = sorted_slot_lines[0] if sorted_slot_lines else False
	# 		print('Earliest Slot:', earliest_slot)
	# 		if earliest_slot:
	# 			slot_exists = self.env['partner.editslots'].search([('partner_id', '=', partner.id),('slot_id', '=', earliest_slot.slot_id.id)])
	# 			if not slot_exists:
	# 				slot_description = self.env['slots.description'].browse(earliest_slot.slot_id.id)
	# 				print(' Slot:', slot_description)
	# 				if slot_description:
	# 					for product_line in slot_description.product_line_ids:
	# 						product_data = {
	# 						'slot_id':earliest_slot.slot_id.id,
	# 						'product_id': product_line.product_id.name,
    #                         'quantity': product_line.quantity,
    #                         'uom_name': product_line.uom_name,
    #                         'price_unit': product_line.price_unit,
	# 						}
	# 						print('Earliest Slot:', product_data)
	# 						partner.write({
    #                         'partner_edit_slot_line_ids': [(0, 0, product_data)]
    #                     })				
							
		

class PartnerOwnslots(models.Model):
	_name = 'partner.ownslots'


	slot_id = fields.Many2one("slots.description",string="Slot id")
	partner_id = fields.Many2one("res.partner",string="Partner")
	slot_date = fields.Date(string="Slot Date")
	slot_name = fields.Char(string="Slot Name", compute="_compute_slot_name", store=True)
	

	
	# @api.model
	# def get_partner_slots_before_one_day(self):

	#     current_datetime = fields.Datetime.now()
	#     partners = self.env['res.partner'].search([('plan_ids', '!=', False)])
	#     slots_to_return = []

	#     for partner in partners:
	#         for slot in partner.partner_slot_line_ids:
	#             slot_date = fields.Datetime.from_string(slot.slot_date)
	#             if (current_datetime - slot_date) == timedelta(days=1):
	#                 slots_to_return.append(slot)
	#                 print('.............')
	#     return slots_to_return
													

class PartnerPaymentslot(models.Model):
	_name = 'partner.paymentslot'


	
	partner_id = fields.Many2one("res.partner",string="Partner")
	slot_id = fields.Integer(string="Slot id")
	product_id = fields.Char(string="Product id")
	product_name = fields.Char(string="Product Name")
	quantity = fields.Float(string="Quantity",copy=True)
	uomName = fields.Char(string='UOMs')
	price_unit = fields.Float(string="Unit price",copy=True)

