from odoo import http
from odoo.http import request
import re 


class GraphPlottingController(http.Controller):


    @http.route('/graph layout', type="http", auth="public", website=True)
    def get_graph_page_layout(self, **kw):

        return request.render('graph.graph_page_template_layout',{})




    # *****************************graph nethouses/openlands display page ************************************

    @http.route('/graph', type="http", auth="public", website=True)
    def get_page_graph(self, **kw):
        locations = request.env['stock.location'].search([])

        greenhouses_list = []
        openlands_list = []
        greenhouses_zones_list = []
        openlands_zones_list = []

        for loc in locations:
            if loc.net_area >= 5000.0 and loc.check_greenhouse_openland == 'greenhouse':
                greenhouses_list.append(loc.id)
            elif loc.net_area >=5000.0 and loc.check_greenhouse_openland == 'openland':
                openlands_list.append(loc.id)

        greenhouses_records = request.env['stock.location'].browse( greenhouses_list)
        openlands_records = request.env['stock.location'].browse( openlands_list)

        for green_rec in greenhouses_records:
            for loc in locations:
                if loc.location_id.name == green_rec.name:
                    greenhouses_zones_list.append(loc.id)

        greenhouses_zones_records = request.env['stock.location'].browse(greenhouses_zones_list)

        for open_rec in openlands_records:
            for loc in locations:
                if loc.location_id.name == open_rec.name:
                    openlands_zones_list.append(loc.id)

        openlands_zones_records = request.env['stock.location'].browse(openlands_zones_list)
      
        return request.render('graph.graph_greenhouses_openland_template',{'greenhouses_records':greenhouses_records,'openlands_records':openlands_records,'greenhouses_zones_records':greenhouses_zones_records,'openlands_zones_records':openlands_zones_records,'page_name':'Greenhouses openlands page'})

      # ********************************* zone page for green house  ***********************************************************

    @http.route('/graph/<string:greenhouse>', type="http", auth="public", website=True)
    def show_greenhouse_zones(self, greenhouse, **kwargs):
        locations = request.env['stock.location'].search([('location_id.name', '=', greenhouse)])
        # zone_beds_list = request.env['stock.location'].search([])
        greenhouse_zones_list = []
        # zone_beds_count = []
        for loc in locations:
            if loc.location_id.name == greenhouse:
                greenhouse_zones_list.append(loc.id)

        # for zone in greenhouse_zones_list:
        #     bed_count = 0
        #     for bed in zone_beds_list :
        #         if bed.location_id.name == greenhouse + '/' +zone:
        #             bed_count += 1 
        #     zone_beds_count.append(bed_count)

        # print("aaaaaaaaaaaaaaaaa%%%%%%%%%%%%%%%%%%%%%%%",zone_beds_count)

        greenhouse_zones_records = request.env['stock.location'].browse(greenhouse_zones_list)
        return request.render('graph.zones_greenhouse_template', {'greenhouse': greenhouse, 'greenhouse_zones_records': greenhouse_zones_records,'page_name':'greenhouse Zones page'})


    # ********************************* zone page for openland  ***********************************************************

    @http.route('/graph/<string:openland>', type="http", auth="public", website=True)
    def show_openland_zones(self, openland, **kwargs):
        locations = request.env['stock.location'].search([('location_id.name', '=', openland)])
        openland_zones_list = []

        for loc in locations:
            if loc.location_id.name == openland:
                openland_zones_list.append(loc.id)

        openland_zones_records = request.env['stock.location'].browse(openland_zones_list)

        return request.render('graph.zones_openlands_template', {'openland': openland, 'openland_zones_records': openland_zones_records,'page_name':'openland Zones page'})

        # ****************************************crop-menure-pest********************************


    @http.route('/graph/<string:greenhouse>/<string:zone>', type="http", auth="public", website=True)
    def show_greenhouse_crop_planning_beds(self, greenhouse, zone, **kwargs):

        locations = request.env['stock.location'].search([('location_id', '=', greenhouse+ "/" + zone)])

        greenhouse_beds_records = []

        for loc in locations:
            if loc.location_id.name == zone and loc.check_bed:
                greenhouse_beds_records.append(loc)
        return request.render('graph.greenhouse_bed_info_template', {'greenhouse': greenhouse, 'zone': zone, 'greenhouse_beds_records': greenhouse_beds_records, 'page_name': 'greenhouse Bed info Page'})


    # ************************************trial crop-menure-pest openland****************************************


    @http.route('/graph/<string:openland>/<string:zone>', type="http", auth="public", website=True)
    def show_openland_crop_planning_beds(self, openland, zone, **kwargs):

        locations = request.env['stock.location'].search([('location_id', '=',openland + "/" + zone)])


        openland_beds_records = []

        for loc in locations:
            if loc.location_id.name == zone and loc.check_bed:
                openland_beds_records.append(loc)
        return request.render('graph.openland_bed_info_template', {'openland': openland, 'zone': zone, 'openland_beds_records': openland_beds_records, 'page_name': 'openland Bed info Page'})


     # **************************** greenhouse crop planning bed page *******************************************


    @http.route('/graph/<string:greenhouse>/<string:zone>/crop-planning', type="http", auth="public", website=True)
    def show_greenhouse_crop_planning_info_beds(self, greenhouse, zone, **kwargs):
        locations = request.env['stock.location'].search([('location_id', '=', greenhouse + "/" + zone)])
        greenhouse_beds_records = []

        for loc in locations:
            if loc.location_id.name == zone and loc.check_bed:
                greenhouse_beds_records.append(loc)

        return http.request.render('graph.greenhouse_crop_planning_info_template', {
            'greenhouse': greenhouse,
            'zone': zone,
            'greenhouse_beds_records': greenhouse_beds_records,
            'page_name': 'greenhouse Bed crop planning info Page'
        })

        # ******************************openland crop planning bed page******************************
    @http.route('/graph/<string:openland>/<string:zone>/crop-planning', type="http", auth="public", website=True)
    def show_openland_crop_planning_info_beds(self, openland, zone, **kwargs):
        locations = request.env['stock.location'].search([('location_id', '=',openland + "/" + zone)])
        openland_beds_records = []

        for loc in locations:
            if loc.location_id.name == zone and loc.check_bed:
                openland_beds_records.append(loc)

        return http.request.render('graph.openland_crop_planning_info_template', {
            'openland': openland,
            'zone': zone,
            'openland_beds_records': openland_beds_records,
            'page_name': 'openland Bed crop planning info Page'
        })

            # **************************** greenhouse menure bed page****************************************

    @http.route('/graph/<string:greenhouse>/<string:zone>/menure', type="http", auth="public", website=True)
    def show_greenhouse_menure_info_beds(self, greenhouse, zone, **kwargs):
        locations = request.env['stock.location'].search([('location_id', '=', greenhouse + "/" + zone)])
        greenhouse_beds_records = []

        for loc in locations:
            if loc.location_id.name == zone and loc.check_bed:
                greenhouse_beds_records.append(loc)

        return http.request.render('graph.greenhouse_menure_info_template', {
            'greenhouse': greenhouse,
            'zone': zone,
            'greenhouse_beds_records': greenhouse_beds_records,
            'page_name': 'greenhouse Bed menure info Page'
        })


        # ****************************openland menure bed page****************************************

    @http.route('/graph/<string:openland>/<string:zone>/menure', type="http", auth="public", website=True)
    def show_openland_menure_info_beds(self, openland, zone, **kwargs):
        locations = request.env['stock.location'].search([('location_id', '=', openland + "/" + zone)])
        openland_beds_records = []

        for loc in locations:
            if loc.location_id.name == zone and loc.check_bed:
                openland_beds_records.append(loc)

        return http.request.render('graph.openland_menure_info_template', {
            'openland': openland,
            'zone': zone,
            'openland_beds_records': openland_beds_records,
            'page_name': 'openland Bed menure info Page'
        })
        # ******************************* greenhouse pest bed page *****************************

    @http.route('/graph/<string:greenhouse>/<string:zone>/pest', type="http", auth="public", website=True)
    def show_greenhouse_pest_info_beds(self, greenhouse, zone, **kwargs):
        locations = request.env['stock.location'].search([('location_id', '=', greenhouse + "/" + zone)])
        greenhouse_beds_records = []

        for loc in locations:
            if loc.location_id.name == zone and loc.check_bed:
                greenhouse_beds_records.append(loc)

        return http.request.render('graph.greenhouse_pest_info_template', {
            'greenhouse': greenhouse,
            'zone': zone,
            'greenhouse_beds_records': greenhouse_beds_records,
            'page_name': 'greenhouse Bed pest info Page'
        })

            # *******************************openland pest bed page *****************************

    @http.route('/graph/<string:openland>/<string:zone>/pest', type="http", auth="public", website=True)
    def show_openland_pest_info_beds(self, openland, zone, **kwargs):
        locations = request.env['stock.location'].search([('location_id', '=', openland + "/" + zone)])
        openland_beds_records = []

        for loc in locations:
            if loc.location_id.name == zone and loc.check_bed:
                openland_beds_records.append(loc)

        return http.request.render('graph.openland_pest_info_template', {
            'openland': openland,
            'zone': zone,
            'openland_beds_records': openland_beds_records,
            'page_name': 'openland Bed pest info Page'
        })



     # *************************** openland bed page ********************************


    # @http.route('/graph/<string:openland>/<string:zone>', type="http", auth="public", website=True)
    # def show_openland_beds(self, openland, zone, **kwargs):
    #     locations = request.env['stock.location'].search([('location_id', '=', openland+ "/" + zone)])
    #     print("Locations:", locations)

    #     crop_planning_list = request.env['crop.planning'].search([])
    #     print("Crop Planning List:", crop_planning_list)

    #     openland_beds_records = []

    #     for loc in locations:
    #         if loc.location_id.name == zone and loc.check_bed:
    #             openland_beds_records.append(loc)
    #     print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",openland_beds_records)

    #     return request.render('graph.openland_beds_template', {'openland': openland, 'zone': zone, 'openland_beds_records': openland_beds_records, 'page_name': 'Openland Beds Page'})





   





    