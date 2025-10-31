from odoo import http
from odoo.http import request

class PestRequestController(http.Controller):

    @http.route('/submit_pest', type='http', auth='user', website=True)
    def submit_pest(self, **Kw):
        print("LLLLLLLLLLLLLLL",Kw)
        new_request = request.env['pest.request'].sudo().create(Kw)
        

        return request.render("graph.successful_pest_record_template", {}) 