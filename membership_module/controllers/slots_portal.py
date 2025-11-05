from odoo import fields
from odoo import http
from odoo.http import request
from odoo.tools import date_utils
from odoo.addons.portal.controllers import portal
from datetime import datetime
from itertools import count
from base64 import b64encode
from werkzeug.wrappers import Response
from werkzeug import datastructures
import json
import logging

# _logger = logging.getLogger(__name__)


 
class MySlotsPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(MySlotsPortal, self)._prepare_home_portal_values(counters)
        user = request.env.user
        partner_id = request.env.user.partner_id.id,
        print('%%%%%%',user)
        if user.partner_id:
            allocated_slots = user.partner_id.allocated_slots
            # print('%%%%%%',allocated_slots)
            values['slots_count'] = allocated_slots
            # values['partner_id'] = partner_id
        return values


    @http.route(['/my/slots'], type='http', auth="public", website=True)
    def my_slots_list_view(self, **kw):
        partner = request.env.user.partner_id
        slot_counter = count(start=1)
        
        values = {
                    'slots': [],
                    'page_name': 'my_slot_view'
        }
        for slot_line in partner.partner_slot_line_ids:
            unique_slot_id = next(slot_counter)
            slot_values = {
            'unique_slot_id': slot_line.id,
            'partner_id':request.env.user.partner_id.id,
            'slot_id': slot_line.slot_id.id,
            'slot_name': slot_line.slot_id.slot_name,
            'slot_date': slot_line.slot_date,
            }
            values['slots'].append(slot_values)
            # print('####',values)
        return request.render("membership_module.portal_slots_template", values)

   
   
    @http.route('/slot/detail/<int:slot_id>/<int:unique_slot_id>', type='http', auth="public", website=True)
    def slot_detail_view(self, slot_id,unique_slot_id, **kw):
        partner = request.env.user.partner_id
        slot = request.env['slots.description'].browse(slot_id)
        slot_details = request.env['partner.ownslots'].search([('slot_id', '=', slot_id), ('partner_id', '=', int(partner))], limit=1)
        print("!!!!",slot_details.slot_date)
        values = {
                'unique_slot_id': unique_slot_id,
                'partner_id':request.env.user.partner_id.id,
                'slot': slot,
                'slot_date': slot_details.slot_date if slot_details else False,
                'product_lines': slot.product_line_ids,
                'page_name': 'my_slot_details_view'
                }
        # previous_slot = request.env['partner.ownslots'].search([('slot_date', '<', slot_details.slot_date), ('partner_id', '=', int(partner))], limit=1, order='slot_date desc')
  
        # if not previous_slot:
        #     values = {
        #         'unique_slot_id': unique_slot_id,
        #         'partner_id':request.env.user.partner_id.id,
        #         'slot': slot,
        #         'slot_date': slot_details.slot_date if slot_details else False,
        #         'product_lines': slot.product_line_ids,
        #         'page_name': 'my_slot_details_view'
        #         }
            # return request.render("membership_module.slot_detail_template", values)
        # else:
        #     current_date = datetime.now().date()
        #     if previous_slot.slot_date < current_date:
        #         values = {
        #         'unique_slot_id': unique_slot_id,
        #         'partner_id':request.env.user.partner_id.id,
        #         'slot': slot,
        #         'slot_date': slot_details.slot_date if slot_details else False,
        #         'product_lines': slot.product_line_ids,
        #         'page_name': 'my_slot_details_view'
        #     }
        #     else:
        #         js_code = """
        #             alert("Slot is open after the first slot delivered.");
        #         """
        #         return request.make_response(js_code, headers=[('Content-Type', 'application/javascript')])
        return request.render("membership_module.slot_detail_template", values)



    @http.route('/slot/detail', type='http', auth="user", website=True)
    def slot_details_redirect(self, **kw):
        return request.redirect('/my/slots')





    # @http.route('/get_inventory_products', type='json', auth='public', website=True,csrf=False)
    # def get_inventory_products(self):
    #     ProductTemplate = http.request.env['product.template'].sudo()
       

    #     print('######################@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2')

    #     leaf_products_template = ProductTemplate.search([('radio_field', '=', 'leafy')])
    #     normal_products_template = ProductTemplate.search([('radio_field', '=', 'normal')])

    #     normal_product_data = []
    #     leaf_product_data = []
    #     print(leaf_products_template,'######################@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2')
    #     print(leaf_products_template,'######################@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2')
        
        

    #     for template in normal_products_template:
    #         product_product = template.product_variant_id
    #         if product_product:
    #             on_hand_quantity = product_product.qty_available # Assuming you want the on-hand quantity
    #             print('######################@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2')
    #             if on_hand_quantity > 0:
    #                 image_url = get_image_url_from_bytes(product_product.image_1920,product_product.id)
    #                 # image_url = self._get_product_image_url(product_product)
    #                 normal_product_data.append({
    #                     'id': product_product.id,
    #                     'name': product_product.name,
    #                     'list_price': product_product.lst_price,
    #                     'quantity': 1,  # Set default quantity
    #                     'uom': product_product.uom_id.name,
    #                     'image':image_url 
    #                 })

    #     for template in leaf_products_template:
    #         product_product = template.product_variant_id
    #         if product_product:
    #             on_hand_quantity = product_product.qty_available  # Assuming you want the on-hand quantity
    #             if on_hand_quantity > 0:
    #                 image_url = get_image_url_from_bytes(product_product.image_1920,product_product.id)
    #                 # image_url = self._get_product_image_url(product_product)
    #                 leaf_product_data.append({
    #                     'id': product_product.id,
    #                     'name': product_product.name,
    #                     'list_price': product_product.lst_price,
    #                     'quantity': 1,  # Set default quantity
    #                     'uom': product_product.uom_id.name,
    #                     'image': image_url
    #                 })

    #     return {
    #         'leaf_products': leaf_product_data,
    #         'normal_products': normal_product_data
    #     }
    

    @http.route('/get_inventory_products', type='json', auth='public', website=True, csrf=False)
    def get_inventory_products(self):
        ProductTemplate = http.request.env['product.template']
        normal_product_data = []
        leaf_product_data = []

        leaf_products_template = ProductTemplate.sudo().search([('radio_field', '=', 'leafy')])
        normal_products_template = ProductTemplate.sudo().search([('radio_field', '=', 'normal')])

        for template in normal_products_template:
            product_product = template.product_variant_id.sudo()
            if product_product:
                on_hand_quantity = product_product.qty_available
                if on_hand_quantity > 0:
                    print("@@@@@@@^^^^^^^^^",str(template.id))
                    image_url = '/web/image/product.template/' + str(template.id) + '/image_128'  # Constructing image URL
                    normal_product_data.append({
                        'id': product_product.id,
                        'name': product_product.name,
                        'list_price': product_product.lst_price,
                        'quantity': 1,
                        'uom': product_product.uom_id.name,
                        'image_url': image_url,  # Include image URL in the data
                        'status': 'Out of Stock' if on_hand_quantity <= 8 else 'In Stock' # Status indicator
                    })

        for template in leaf_products_template:
            product_product = template.product_variant_id.sudo()
            if product_product:
                on_hand_quantity = product_product.qty_available
                if on_hand_quantity > 0:
                    image_url = '/web/image/product.template/' + str(template.id) + '/image_128'  # Constructing image URL
                    leaf_product_data.append({
                        'id': product_product.id,
                        'name': product_product.name,
                        'list_price': product_product.lst_price,
                        'quantity': 1,
                        'uom': product_product.uom_id.name,
                        'image_url':image_url,  # Include image URL in the data
                        'status': 'Out of Stock' if on_hand_quantity <= 20 else 'In Stock'             
                    })

        return {
            'leaf_products': leaf_product_data,
            'normal_products': normal_product_data
        }

        
    # def _get_product_image_url(self, product_product):
    #     ProductProduct = http.request.env['product.product'].sudo()
    #     product_product_sudo = ProductProduct.browse(product_product.id).sudo()
    #     if product_product_sudo.image_1920:
    #         print('imageeeeeeeeeeee')
    #         image_url = '/web/image/product.product/{}/image_1920'.format(product_product_sudo.id)
    #         print('imageeeeeeeeeeee',image_url)
    #         return image_url

    




    @http.route('/add_to_cart_with_extra_payment', type='json', auth='public', website=True)
    def add_to_cart_with_extra_payment(self, products,uniqueSlotId):
        print('@@@@@@@@@',products)
        
        order = request.website.sale_get_order(force_create=True)

        product_name_with_quantity=[]
        
        product_unit_price=0

        for product in products:
            product_id = product.get('id')
            product_name = product.get('name')
            product_quantity = product.get('quantity')
            product_unit_price = product.get('extraAmount')
            print('@@@@@@@@@',product_id,product_name,product_quantity,product_unit_price)
            formatted_product = f"{product_name} ({product_quantity})"
            product_name_with_quantity.append(formatted_product)


        formatted_name = '\n'.join(product_name_with_quantity)
        product = http.request.env['product.product'].sudo().search([('name', '=', 'Extra Payment')])
        for rec in product:
            rec.lst_price=product_unit_price
            # print('eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',rec.lst_price)
        
        if product:
            
            order_line = order.order_line.filtered(lambda line: line.product_id.id == product.id)

            if order_line:
                order_line.product_uom_qty += 1
            else:
                order_line.create({
                    'order_id': order.id,
                    'product_id': product.id,
                    'name': formatted_name,
                    'product_uom_qty': 1,
                    'price_unit': product_unit_price,
                })
                order.write({'slot_id': uniqueSlotId})
            

        return {"success": True}


    @http.route('/backend/check-sale-order', type='http', auth='public', website=True)
    def check_sale_order_exists(self,**kwargs):
        slot_id = request.params.get('slotId')

        if not slot_id:
            return Response(json.dumps({'error': 'Slot ID is required'}), status=400, content_type='application/json')

        try:
            slot_id = int(slot_id)
            partner_id = request.env.user.partner_id.id
            sale_order_exists = request.env['sale.order'].sudo().search_count([
                ('partner_id', '=', partner_id),
                ('slot_id', '=', slot_id)
            ])
            return Response(json.dumps({'hasSaleOrder': bool(sale_order_exists)}), content_type='application/json')

        except ValueError:
            return Response(json.dumps({'error': 'Invalid slot ID'}), status=400, content_type='application/json')

        except Exception as e:
            return Response(json.dumps({'error': str(e)}), status=500, content_type='application/json')


    @http.route('/backend/save-template-products', type='json', auth='public')
    def save_template_products(self, **post):
        print('9999999999')

        try:
            print('@@@@@@@@@@@@@@@@@@', post)
            slot_id = int(post.get('slot_id'))
            template_products = post.get('template_products')

            print('@@@@@@@@@@@@@@@@@@Received slot_id:', slot_id)
            print('$$$$$$$$$$$$$Received product_data:', template_products)

            # Parse the product data from JSON
            template_products = json.loads(template_products)
            
            print('$$$$$$$$$$$$$Received product_data:', template_products)

            partner_id = request.env.user.partner_id.id

            partner_payment_slot = request.env['res.partner'].sudo().search([
            ('id', '=', partner_id)])
            print(partner_payment_slot)

            if not partner_payment_slot:
                return False

            # Clear existing template products
            # partner_payment_slot.write({'template_product_ids': [(5, 0, 0)]})

            # partner_payment_slot.write({'partner_payment_slot_line_ids': [(5, 0, 0)]})

            # existing_product = partner_payment_slot.partner_payment_slot_line_ids.filtered(lambda x: x.slot_id == slot_id).mapped('product_id.id')
            
            # Create new template products
            template_product_vals = []
            for product_data in template_products:
                product_vals = (0,0,{
                    'slot_id': slot_id,
                    'product_id': product_data.get('product_id'),
                    'product_name': product_data.get('name'),
                    'uomName': product_data.get('uomName'),
                    'quantity': product_data.get('quantity'),
                    'price_unit': product_data.get('price'),
                })
                template_product_vals.append(product_vals)
            partner_payment_slot.write({'partner_payment_slot_line_ids': template_product_vals })
            return {'success': True}


            #     # product_id = product_data.get('product_id')

            #     # if product_id not in existing_product:
            #         template_product_vals.append((0,0,{
            #         'slot_id': slot_id,
            #         'product_id':product_data.get('product_id'),
            #         'product_name': product_data.get('name'),
            #         'quantity': product_data.get('quantity'),
            #         # 'uom_name': product_data.get('uom_name'),
            #         'price_unit': product_data.get('price'),
            #     }))
            #     # existing_products |= product_id    
            # # partner_payment_slot.write({'partner_payment_slot_line_ids': [(0, 0, template_product_vals)]})
            # if template_product_vals:
            #     print(template_product_vals)
            #     partner_payment_slot.partner_payment_slot_line_ids.create(template_product_vals)
            #     #partner_payment_slot.write({'partner_payment_slot_line_ids': template_product_vals})
            #     # partner_payment_slot.partner_payment_slot_line_ids = template_product_vals
                
        except Exception as e:
            print('Error:', str(e))
            return {'success': False, 'error': str(e)} 




           
                
           
           

            