from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale as BaseWebsiteSale

class MyWebsiteCart(BaseWebsiteSale):
    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        val = super(MyWebsiteCart, self).cart(**post)
        order = request.website.sale_get_order()
        order_lines_total = []
        for line in order.order_line:
            line_total = line.price_subtotal
            order_lines_total.append({
                'line_id': line.id,
                'total': line_total,
            })
        val.qcontext.update({
            'order_lines_total': order_lines_total,
        })
        return val

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, **kw):
        line_id = kw.get('line_id')
        quantity = kw.get('quantity')
        val = super(MyWebsiteCart, self).cart_update_json(**kw)
        if line_id:
            order_line = request.env['sale.order.line'].sudo().browse(int(line_id))
            if quantity is not None:
                order_line.product_uom_qty = int(quantity)
        return val
