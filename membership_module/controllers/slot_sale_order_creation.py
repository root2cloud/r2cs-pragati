from odoo import http,fields
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.web.controllers.main import content_disposition
import json

class SaleOrderController(http.Controller):

    @http.route('/create_sale_order', type='json', auth='user')
    def create_sale_order(self, **post):
        try:
            print('@@@@@@@@@@@@@@@@@@', post)
            slot_id = int(post.get('slot_id'))
            product_data = post.get('product_data')

            print('@@@@@@@@@@@@@@@@@@Received slot_id:', slot_id)
            print('$$$$$$$$$$$$$Received product_data:', product_data)

            # Parse the product data from JSON
            product_data = json.loads(product_data)
            
            print('$$$$$$$$$$$$$Received product_data:', product_data)


            # Create a sale order and related sale order lines
            sale_order = request.env['sale.order'].create({
                'partner_id': request.env.user.partner_id.id,
                'date_order': fields.Datetime.now(),
                'slot_id': slot_id,
                
            })
            sale_order_lines = []

            for line in product_data:

             products=request.env['product.product'].browse(line['product_id'])
             print(products)
             line_data = {
                    'order_id': sale_order.id,
                    'product_id': line['product_id'],
                    # 'name': products.name,
                    'product_uom_qty': line['quantity'],
                    # 'price_unit': line['price_unit'],  # Assuming price_unit is provided in product_lines
                    }
             sale_order_lines.append(line_data)
            request.env['sale.order.line'].create(sale_order_lines)

            return {'success': True,'sale_order_id': sale_order.id}

        except Exception as e:
            print('Error:', str(e))
            return {'success': False, 'error': str(e)}