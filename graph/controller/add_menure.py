from odoo import http
from odoo.http import request
import json



class AddMenureController(http.Controller):

    @http.route('/<string:greenhouse>/<string:zone>/adding-menure', type='http', auth='user', website=True)
    def apply_new_menure(self,greenhouse,zone,**Kw):

        greenhouse_record = request.env['stock.location'].search([('name','=',greenhouse)])
        crop_records = request.env['crop.requests'].search([('location_dest_id.name', '=',greenhouse),('state', 'not in', ['draft', 'cancel', 'yield'])])
        matched_menure_records = request.env['product.product'].search([('check_product_is_menure_pest','=','menure')])
        source_locations = request.env['stock.location'].search([('name', 'ilike', '%Stock%')])

        matched_crop_records = []
        

        for crop in crop_records:
            if zone in crop.zone_ids.mapped('name'):
                
                matched_crop_records.append(crop)
        

        return request.render('graph.adding_menure_template',{'greenhouse':greenhouse,'greenhouse_record':greenhouse_record.id,'menure_zone':zone,'matched_crop_records':matched_crop_records,'matched_menure_records':matched_menure_records,'source_locations':source_locations})



    @http.route('/fetch_bed_ids', type='json', auth='user')
    def fetch_bed_ids(self, crop_id, **kwargs):
        print("crop_idxxxxxxxxxxxxxxxxxxx",crop_id)
    
        bed_records = request.env['crop.requests'].search([('id', '=' ,crop_id),])
        print("CCCCCCCCCCCCCCC",bed_records)

        matched_bed_records = []

        for rec in bed_records:
            bed_ids_list = rec.beds_ids
            matched_bed_records.extend(bed_ids_list)
        print("################", matched_bed_records)
        bed_names=[]

        for rec in matched_bed_records:
            bed_names.append(rec.name)

        return  bed_names
        