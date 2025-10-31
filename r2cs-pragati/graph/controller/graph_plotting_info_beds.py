from odoo import http
from odoo.http import request
import json



class BedController(http.Controller):

    # **********************************crop-planning info*******************************************

    @http.route('/get_bed_info', type='json', auth='public')
    def get_bed_info(self, **kwargs):
        bed_name = kwargs.get('bed_name')
        crop_name = kwargs.get('crop_name')

        crop_planning_records = request.env['crop.planning'].search([('beds_ids', 'in', bed_id)])
        crop_request_records = request.env['crop.requests'].search([('beds_ids', 'in', bed_id)])
        print("LLLLLLLLLLLLLLLL",crop_request_records)

        
        response_data ={}

        for rec in crop_planning_records:
            
            if (rec.product_id.name == crop_name):
                for beds in rec.beds_ids:
                    if bed_name == beds.name:
                        crop_name = rec.product_id.name
                        sowing_date = rec.sowing_date.date()
                        land_prepare_date = rec.land_prepare_date.date()
                        crop_end_date = rec.crop_end_date.date()
                        harvest_date = rec.harvest_date.date()
                        total_gain_output = rec.total_gain_output

                        response_data = {
                'bed_name':bed_name,
                'crop_name':crop_name,
                'sowing_date': sowing_date,
                'land_prepare_date': land_prepare_date,
                'crop_end_date': crop_end_date,
                'harvest_date': harvest_date,
                'total_gain_output': total_gain_output,
                }
        return response_data


        # ******************************menure info********************************************************


    @http.route('/get_menure_info', type='json', auth='public', website=True)
    def get_menure_info(self, bed_name, zone_name, greenhouse_name, crop_name=None, **kwargs):
        crop_requests = request.env['crop.requests'].search([
        ('beds_ids.name', 'ilike', bed_name),
        ('zone_ids.name', 'ilike', zone_name),
        ('location_dest_id', 'ilike', greenhouse_name)
        ])
        print("$$$$$$$$$$$$$$$$$$$$$$",crop_requests,crop_name)

        if crop_name:
            crop_requests = crop_requests.filtered(lambda rec: rec.product_id.name == crop_name)

        print("$$$$$$$$$$$$$$$$$$$$$$",crop_requests)

        result_data = []

        for crop_request in crop_requests:
            crop_request_lines = crop_request.menure_line_ids
            print("$$$$$$$$$$$$$$$$$$$$$$",crop_request_lines)


            for line in crop_request_lines:
                result_data.append({
                    'product_id_menure': line.product_id_menure.name,  
                    'stock_change_menure': line.stock_change_menure, 
                    'crop_name_in_menure': line.crop_id.product_seed_id.name
                    
                })

            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",result_data)

        return result_data
            
        
        



        # ********************************pest info******************************************************


    @http.route('/get_pest_info', type='json', auth='public', website=True)
    def get_pest_info(self, bed_name,  zone_name,greenhouse_name, crop_name=None, **kwargs):
        crop_requests = request.env['crop.requests'].search([
        ('beds_ids.name', 'ilike', bed_name),
        ('zone_ids.name', 'ilike', zone_name),
        ('location_dest_id', 'ilike', greenhouse_name)
        ])
        print("$$$$$$$$$$$$$$$$$$$$$$",crop_requests,crop_name)

        if crop_name:
            crop_requests = crop_requests.filtered(lambda rec: rec.product_id.name == crop_name)

        print("$$$$$$$$$$$$$$$$$$$$$$",crop_requests)

        result_data = []

        for crop_request in crop_requests:
            crop_request_lines = crop_request.pest_line_ids
            print("$$$$$$$$$$$$$$$$$$$$$$",crop_request_lines)


            for line in crop_request_lines:
                result_data.append({
                    'product_id_pest': line.product_id_pest.name,  
                    'stock_change_pest': line.stock_change_pest, 
                    'disease':line.disease.name,
                    'crop_name_in_pest': line.crop_id.product_seed_id.name
                    
                })

            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",result_data)

        return result_data
        
       
   



    

   

            

        

