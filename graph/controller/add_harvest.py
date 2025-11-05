from odoo import http
from odoo.http import request
import json



class AddHarvestController(http.Controller):

    @http.route('/<string:greenhouse>/<string:zone>/adding-daily-harvest', type='http', auth='user', website=True)
    def apply_new_menure(self,greenhouse,zone,**Kw):


        warehouse_ids=request.env['stock.location'].search([('usage', '=', 'internal'), ('replenish_location', '=', True)])

        
        greenhouse_rec = request.env['stock.location'].search([('name','=',greenhouse)])

        wh_related_crops =request.env['product.product'].search([('radio_field', 'in', ['leafy', 'normal'])])
        crop_req_gh_rec = request.env['crop.requests'].search([('location_dest_id','=',greenhouse_rec.id),('zone_ids.name', 'in', [zone]) ])

       
        
        return request.render('graph.adding_daily_harvest_template',{'greenhouse_rec':greenhouse_rec.id if greenhouse_rec else False,'greenhouse':greenhouse,'harvest_zone':zone,'warehouse_ids':warehouse_ids,'wh_related_crops':crop_req_gh_rec,})



    @http.route('/fetch_crop_ids',type='json',auth='user')
    def fetch_crop_ids(self,product_id,greenhouse,**kwargs):
        crop_ids = request.env['crop.requests'].search([('product_id.id','=',product_id),('state','=','harvest'),('location_dest_id.name','=',greenhouse)])
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",crop_ids,greenhouse,product_id)
        options = []
        for crop in crop_ids:
            bed_names = ', '.join(crop.beds_ids.mapped('name'))
            options.append({
                'value': crop.id,
                'text': crop.ref,
                'bed_names': bed_names
            })

        return options




      