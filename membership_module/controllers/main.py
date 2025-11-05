from odoo import http,fields
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.web.controllers.main import content_disposition
import json

class MembershipPage(http.Controller):

    @http.route('/membership', type='http', auth='public', website=True)
    def membership_page(self, **kwargs):
        # Retrieve membership plans
        plans = request.env['membership.planning'].sudo().search([])

        # Group plans by membership type
        grouped_plans = {}
        for plan in plans:
            membership_name = plan.membership_id.membership_name
            if membership_name not in grouped_plans:
                grouped_plans[membership_name] = []
            grouped_plans[membership_name].append(plan)

        # Pass the data to the template
        return request.render('membership_module.membership_page_template', {
            'grouped_plans': grouped_plans,
        })

    
    @http.route('/membership/<int:membership_id>', type='http', auth="public", website=True)
    def membership_details(self, membership_id, **kw):
        membership = request.env['member.ship'].browse(membership_id)
        plannings = request.env['membership.planning'].search([('membership_id', '=', membership.id)])
        return request.render('membership_module.membership_plans_template', {'membership': membership, 'plannings': plannings})


    


    @http.route('/planning_description/<int:planning_id>', type='http', auth="public", website=True)
    def planning_details(self, planning_id, **kw):
        planning = request.env['membership.planning'].browse(planning_id)
        repetitions = planning.plan_duration

        slots = request.env['slots.description'].search([
                ('family_membership_id', '=', planning.membership_id.id)
            ])
        repeated_slots = [slot for _ in range(repetitions) for slot in slots]
        # print(repeated_slots)
        return request.render('membership_module.membership_plans_description_slot_template', {'membership': planning.membership_id.id,'repeated_slots': repeated_slots})





    @http.route('/planning/<int:planning_id>', type='http', auth="public", website=True)
    def planning_detail(self, planning_id, **kw):
        # print("%%%%%%%%%%%%%")
        planning = request.env['membership.planning'].browse(planning_id)
        repetitions = planning.plan_duration

        slots = request.env['slots.description'].search([
                ('family_membership_id', '=', planning.membership_id.id)
            ])
        repeated_slots = [slot for _ in range(repetitions) for slot in slots]
        return request.render('membership_module.membership_plans_slot_template', {'repeated_slots': repeated_slots})


    


    


    @http.route('/membership_module/fetch_slot_data', type='json', auth="public", website=True)
    def fetch_slot_data(self, slot_id):
        slot = request.env['slots.description'].browse(int(slot_id))
        return {
            'id': slot.id,
            'slot_name': slot.slot_name,
            'product_line_ids': [{
                'product_id': line.product_id.id,
                'quantity': line.quantity
            } for line in slot.product_line_ids],
        }




    
    @http.route('/membership_module/add_to_cart', type='json', auth="public", website=True)
    def add_to_cart(self, **post):
        product_lines = post.get('product_lines', [])
    
        if product_lines:
            # Add each product from the fetched slot data to the cart
            order = request.website.sale_get_order(force_create=True)
            for product_line in product_lines:
                order._cart_update(
                    product_id=int(product_line.get('product_id')),
                    add_qty=float(product_line.get('quantity'))
                )

            # Return some response if needed
            return {'status': 'success'}
        else:
            return {'status': 'error', 'message': 'No product lines provided'}  






    
    

    # @http.route('/custom/buy_plan', type='json', auth='public', website=True)
    # def custom_buy_plan(self, planning_id, plan_name, membership_id):
    #     try:
    #         # Fetch all products matching the criteria in a single query
    #         products = request.env['product.product'].sudo().search([
    #             ('plan_name', '=', plan_name),
    #             ('plan_id.membership_id.id', '=', membership_id),
    #         ])
    #         print(products)

    #         if products:
    #             order = request.website.sale_get_order(force_create=True)

    #             for product in products:
    #                 order_line = order.order_line.filtered(lambda line: line.product_id.id == product.id)
    #                 print('yewwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww3',order_line)

    #                 if order_line:
    #                     order_line.product_uom_qty += 1
    #                     print('yewwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww4',order_line)

    #                 else:
    #                     order_line.create({
    #                         'order_id': order.id,
    #                         'product_id': product.id,
    #                         'name': product.name,
    #                         'product_uom_qty': 1,
    #                         'price_unit': product.list_price,
    #                     })
    #                     print('yewwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww',order_line)
    #             request.session['website_sale_cart_count'] = order.cart_quantity

    #             # order.write({})

    #             return {"success": True} 
    #         else:
    #             return {"success": False, "message": "No products found for the selected plan."}
    #     except Exception as e:
    #         return {"success": False, "message": str(e)}
     


    


   
    @http.route('/your_custom_route/create_sale_order', type='json', auth='user')
    def create_sale_order(self, **post):
        try:
            print('@@@@@@@@@@@@@@@@@@', post)
            slot_id = int(post.get('slot_id'))
            product_data = post.get('product_data')

            print('@@@@@@@@@@@@@@@@@@Received slot_id:', slot_id)
            print('$$$$$$$$$$$$$Received product_data:', product_data)

            # Parse the product data from JSON
            product_data = json.loads(product_data)


            # Create a sale order and related sale order lines
            sale_order = request.env['sale.order'].create({
                'partner_id': request.env.user.partner_id.id,
                'date_order': fields.Datetime.now(),
                
            })

            sale_order_lines = []
            for product in product_data:
                
                line_data = {
                    'order_id': sale_order.id,
                    'product_id': product['product_id'],
                    'product_uom_qty': product['quantity'],
                    
                }
                sale_order_lines.append(line_data)

            # Create sale order lines in a single create() call
            request.env['sale.order.line'].create(sale_order_lines)

            return {'success': True,'sale_order_id': sale_order.id}

        except Exception as e:
            print('Error:', str(e))
            return {'success': False, 'error': str(e)}

    
    @http.route('/your_custom_route/get_sale_order_info', type='json', auth='user')
    def get_sale_order_info(self, sale_order_id, **kwargs):
        try:
            # Fetch sale order information based on sale_order_id
            sale_order = request.env['sale.order'].sudo().browse(int(sale_order_id))

            # Return the sale order number in the response
            return {'success': True, 'sale_order_number': sale_order.name}
        except Exception as e:
            print('Error:', str(e))
            return {'success': False, 'error': str(e)}




class WebsiteSaleExtended(WebsiteSale):

    @http.route('/custom/buy_plan', type='json', auth='public', website=True)
    def custom_buy_plan(self, planning_id, plan_name, membership_id):
        try:
            # Fetch all products matching the criteria in a single query
            products = request.env['product.product'].sudo().search([
                ('plan_name', '=', plan_name),
                ('plan_id.membership_id.id', '=', membership_id),
            ])
            print(products)

            if products:
                sale_order = request.website.sale_get_order(force_create=True)
                order_line_vals= {
                            'order_id': sale_order.id,
                            'product_id': products[0].id,
                            'name': products[0].name,
                            'product_uom_qty': 1,
                            'price_unit': products[0].list_price,
                        }
                request.env['sale.order.line'].sudo().create(order_line_vals)
                return {"success": True}
            else:
                return {"success": False, "message": "Plan not found."}

        except Exception as e:
            return {"success": False, "message": str(e)}
     
