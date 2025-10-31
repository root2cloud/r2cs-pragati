from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class CropPlanning(models.Model):
    _name = 'crop.planning'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Planning of the crops'
    _rec_name = 'ref'

    def _get_default_location_id(self):
        domain = [('name', 'ilike', "Gaddipati Family Trust")]
        location = self.env['stock.location'].search(domain, limit=1)
        if location:
            return location.id
        return False

    ref = fields.Char(string='Reference ID', required=True, copy=False,
                      readonly=True, tracking=True,
                      default=lambda self: _('New'))
    product_id = fields.Many2one('product.product', string='Crop Name')
    product_name = fields.Char(string='Product Name', related='product_id.name', store=True)
    land_prepare_date = fields.Datetime(string="Land Preparation Date", default=datetime.today())
    sowing_date = fields.Datetime(string="Sowing/Transplantation Date", default=datetime.today(), tracking=True)
    crop_end_date = fields.Datetime(string="Crop end Date", default=datetime.today())
    harvest_date = fields.Datetime(string="Harvest Start Date", default=datetime.today())
    select_area_id = fields.Many2one('stock.location', string="Selection Area(N/H)")
    on_hand_qty = fields.Float(string='On Hand Quantity', compute='_compute_on_hand_qty',store=True)
    zone_ids = fields.Many2many(
        'stock.location', 
        string="Zone area", 
        relation='crop_planning_zone_rel',
        column1='planning_id', 
        column2='zone_id',
        domain="[('location_id', '=', select_area_id)]"
    )
    beds_ids = fields.Many2many(
        'stock.location', 
        string="Beds",
        relation='crop_planning_beds_rel',
        column1='planning_id', 
        column2='bed_id',
        domain="[('location_id', 'in', zone_ids),('location_confirm','=',False)]"
    )
    total_length = fields.Float(string='Total Length(ft\'s)', compute='_compute_total_length', store=True)
    no_seeds_required = fields.Float(string='Total Expected Seeds Required', compute='_compute_no_seeds_required', store=True)
    crop_planning_line_ids = fields.One2many('crop.planning.line','planning_id')
    total_gain_output = fields.Float(string='Total Expected Output', compute='_compute_total_gain_output', store=True)
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('execute','Cultivated'),('complete','Completed'),('cancel','Cancel')], default='draft')
    uom_name = fields.Char(string='UOM Name', related='product_id.uom_name', store=True)
    location_id = fields.Many2one(
        'stock.location', "Source Location", default=_get_default_location_id,
        store=True, readonly=False,required=True)
    # category_name = fields.Char(string='Category Name', related='categ_id.name', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id,
        help='The default company for this user.', context={'user_preference': True})
    user_id = fields.Many2one('res.users', string='Responsible user',
                              default=lambda self: self.env.user)

    @api.depends('product_id', 'location_id')
    def _compute_on_hand_qty(self):
        for record in self:
            if record.product_id and record.location_id:
                product = record.product_id
                location = record.location_id
                stock_quant = self.env['stock.quant'].search([
                    ('product_id', '=', product.id),
                    ('location_id', '=', location.id)
                ])
                on_hand_qty = sum(stock_quant.mapped('quantity'))
                record.on_hand_qty = on_hand_qty
            else:
                record.on_hand_qty = 0.0

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if values.get('ref', _('New')) == _('New'):
                values['ref'] = self.env['ir.sequence'].next_by_code(
                'crop.planning') or _('New')
                res = super(CropPlanning, self).create(values)
        return res

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '[%s] - [%s]' % (rec.ref, rec.product_name)))
        return res




    @api.depends('product_id.no_of_seeds', 'total_length', 'product_id.standard_bed_length')
    def _compute_no_seeds_required(self):
        for record in self:
            if record.product_id and record.product_id.standard_bed_length > 0:
                if record.product_id.standard_bed_length == 0:
                    record.no_seeds_required = 0.0
                else:
                    area = record.total_length / record.product_id.standard_bed_length
                    record.no_seeds_required = record.product_id.no_of_seeds * area
            else:
                record.no_seeds_required = 0.0

    @api.depends('beds_ids')
    def _compute_total_length(self):
        for record in self:
            record.total_length = sum(record.beds_ids.mapped('bed_length'))

    @api.depends('crop_planning_line_ids.expected_output')
    def _compute_total_gain_output(self):
        for record in self:
            record.total_gain_output = sum(record.crop_planning_line_ids.mapped('expected_output'))


    @api.onchange('product_id','total_length','sowing_date')
    def onchange_product_id(self):
        for record in self:
            if record.product_id and record.product_id.crop_end_duration:
                crop_end_duration = record.product_id.crop_end_duration
                first_harvest_day = record.product_id.first_harvest_day
                record.crop_end_date = record.sowing_date + timedelta(days=crop_end_duration)
                record.harvest_date = record.sowing_date + timedelta(days=first_harvest_day)
                record.land_prepare_date = record.sowing_date - timedelta(days=10)
                record.crop_planning_line_ids = [(5, 0, 0)]
                lines = []
                area = record.total_length / record.product_id.standard_bed_length
                for line in record.product_id.planning_line_ids:
                    vals = {
                        'interval_period': line.interval_period,
                        'expected_output': line.expected_output * area
                    }
                    # Calculate start and end dates based on sowing date
                    sowing_date = fields.Datetime.from_string(record.sowing_date)
                    interval_start, interval_end = map(int, line.interval_period.split('-'))
                    start_date = (sowing_date + timedelta(days=interval_start - 1)).date()
                    end_date = (sowing_date + timedelta(days=interval_end)).date()
                    vals.update({'start_date': start_date, 'end_date': end_date})
                    lines.append((0, 0, vals))

                record.crop_planning_line_ids = lines


    def draft_planning(self):
        self.state = 'draft'

    def confirm_planning(self):
        l1 = []
        for rec in self:
            for bed in rec.beds_ids:
                if not bed.location_confirm:
                    bed.write({'location_confirm': True})

                else:
                    l1.append(bed.name)
            bed_names = ",".join(l1)
            if bed_names:
                raise ValidationError(_(f"{bed_names} are already used for another crop "))
            else:
                rec.state = 'confirm'

    @api.model
    def update_date_for_today(self):
        confirmed_records = self.search([('state', '=', 'confirm')])
        for record in confirmed_records:
            if record.crop_end_date and record.crop_end_date < fields.Datetime.now():
                expired_beds = record.beds_ids.filtered(lambda bed: bed.location_confirm)
                expired_beds.write({'location_confirm': False})
                record.state = 'complete'



    def cancel_planning(self):
        self.state = 'cancel'
        for record in self:
            for bed in record.beds_ids:
                if bed.location_confirm:
                    bed.write({'location_confirm': False})



class CropPlanningLine(models.Model):
    _name = 'crop.planning.line'
    _description = 'Planning of the crop intervals'

    planning_id = fields.Many2one('crop.planning', string='Planning ID')
    interval_period = fields.Char(string='Interval Periods')
    start_date = fields.Date(string='Harvest start date')
    end_date = fields.Date(string='Harvest end date')
    expected_output = fields.Float(string='Expected Output/Interval')
    uom_name = fields.Char(string='Unit of Measure', default='Kg')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id,
        help='The default company for this user.', context={'user_preference': True})
    user_id = fields.Many2one('res.users', string='Responsible user',
                              default=lambda self: self.env.user)