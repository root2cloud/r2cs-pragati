from odoo import models, fields, api, _

class StockLocation(models.Model):
    _inherit = 'stock.location'

    def _get_default_location_custom_id(self):
        domain = [('name', '=', "Stock")]
        location = self.env['stock.location'].search(domain, limit=1)
        if location:
            return location.id
        return False

    net_area = fields.Float(string="Net Area(sq'yds)")
    check_bed = fields.Boolean(string="Check If it's Bed", default=False)
    bed_length = fields.Float(string="Bed Length(ft's)")
    location_confirm = fields.Boolean(string='Location Confirm', default=False)
    location_type_id = fields.Many2one('location.type', string='Location type')
    location_custom_id = fields.Many2one('stock.location', string='Ware House', default=_get_default_location_custom_id)
    farmer_emp_id = fields.Many2one('res.partner', string='Farmer Name')
    planning_id = fields.Many2one('crop.requests',string='Plan Id')
    menure_id = fields.Many2many('menure.request',string='Menure Id',compute='_get_menure_ids',readonly = False)
    pest_id = fields.Many2many('pest.request',string='Pest Id',compute='_get_pest_ids',readonly = False)
    is_cost_center =  fields.Boolean(string="Is Cost Center", default=False)

    # *********compute menure_id field in stock location *************

    @api.depends('planning_id')
    def _get_menure_ids(self):
        for rec in self:
            if rec.planning_id:
                if rec.planning_id.menure_line_ids:
                    print("YYYYYYYYYeeeeesssssssssssiiiiiiiiiiiiddddddddddd")
                    for r in rec.planning_id.menure_line_ids:
                        rec.menure_id = [(4, r.id, 0)]


    # *********compute pest_id field in stock location *************

    @api.depends('planning_id')
    def _get_pest_ids(self):
        for rec in self:
            if rec.planning_id:
                if rec.planning_id.pest_line_ids:
                    print("YYYYYYYYYeeeeesssssssssssiiiiiiiiiiiiddddddddddd")
                    for r in rec.planning_id.pest_line_ids:
                        rec.pest_id = [(4, r.id, 0)]

    # ***********done compute menure pest ****************


    @api.onchange('check_bed')
    def _onchange_check_bed(self):
        for record in self:
            if record.check_bed == True:
                record.net_area = 0
            else:
                record.net_area = record.net_area

    @api.onchange('location_id')
    def _onchange_location_type_id(self):
        for record in self:
            if record.location_id and record.location_id.location_type_id:
                record.location_type_id = record.location_id.location_type_id.id
                record.farmer_emp_id = record.location_id.farmer_emp_id.id