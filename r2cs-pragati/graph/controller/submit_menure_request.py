from odoo import http
from odoo.http import request

class MenureRequestController(http.Controller):

    @http.route('/submit_menure', type='http', auth='user', website=True)
    def submit_menure(self, **Kw):
        print("LLLLLLLLLLLLLLL",Kw)
        new_request = request.env['menure.request'].sudo().create(Kw)
        

        return request.render("graph.successful_menure_record_template", {})  
