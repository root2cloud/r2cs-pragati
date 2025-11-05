from odoo import http
from odoo.http import request

class DailyHarvestController(http.Controller):


    @http.route('/submit_harvest', type='http', auth='user', website=True)
    def submit_harvest(self, **Kw):
        print("LLLLLLLLLLLLLLL",Kw)
        new_request = request.env['crop.request.line'].sudo().create(Kw)
        

        return request.render("graph.successful_daily_harvest_record_template", {})  

            
