from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    crop_end_duration = fields.Integer(string='Crop Duration')
    standard_bed_length = fields.Float(string='Standard Bed Length')
    no_of_seeds = fields.Float(string='No of Seeds Required')
    first_harvest_day = fields.Integer(string='First Harvest Starts from')
    planning_line_ids = fields.One2many('planning.period', 'product_id')
    set_interval = fields.Integer(string='Set Interval', default=30)
    total_expect_quantity = fields.Float(string='Total Expected Quantity', compute='_compute_total_expect_quantity', store=True)
    uom_name = fields.Char(string='Unit of Measures', related='uom_id.name', store=True)
    category_name = fields.Char(string='Category Name', related='categ_id.name', store=True)
    attrs_field = fields.Boolean(string='attrs field', default=False)
    radio_field = fields.Selection([('none','None'),('leafy','Leafy'),('normal','Normal')],string="Radio Field",default='none')

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        for rec in self:
            if rec.category_name == 'Seeds & Seedlings':
                rec.attrs_field = True
            else:
                rec.attrs_field = False

    @api.depends('planning_line_ids.expected_output')
    def _compute_total_expect_quantity(self):
        for rec in self:
            rec.total_expect_quantity = sum(rec.planning_line_ids.mapped('expected_output'))

    def get_interval_details(self):
        self.ensure_one()

        # Retrieve values
        crop_end_duration = self.crop_end_duration
        first_harvest_day = self.first_harvest_day
        set_interval = self.set_interval

        if crop_end_duration <= 0 or first_harvest_day <= 0 or set_interval <= 0:
            raise ValidationError("Values must be greater than zero.")

        # Remove existing planning period records
        self.planning_line_ids.unlink()

        intervals = []
        current_day = first_harvest_day

        while current_day <= crop_end_duration:
            next_interval_end = min(current_day + set_interval - 1, crop_end_duration)
            interval = f"{current_day}-{next_interval_end}"
            intervals.append((0, 0, {
                'product_id': self.id,
                'interval_period': interval,
                'expected_output': 0.0  # You might want to set this to a default value
            }))
            current_day += set_interval

        self.write({'planning_line_ids': intervals})


class PlanningPeriod(models.Model):
    _name = 'planning.period'
    _description = 'Planning periods of the seed items'

    product_id = fields.Many2one('product.template', string='Products')
    interval_period = fields.Char(string='Interval Periods')
    expected_output = fields.Float(string='Output per Interval')
    uom_name = fields.Char(string='UOM', default='Kg')