# coding=utf-8

from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
import dateutil.relativedelta
from odoo.exceptions import ValidationError, AccessError, UserError, RedirectWarning, Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AdmissionCheckListTemplate(models.Model):
    _name="inpatient.checklist.template"
    _description = "Inpatient Checklist Template"

    name = fields.Char(string="Name", required=True)
    remark = fields.Char(string="Remarks")


class AdmissionCheckList(models.Model):
    _name="inpatient.checklist"
    _description = "Inpatient Checklist"

    name = fields.Char(string="Name", required=True)
    is_done = fields.Boolean(string="Y/N")
    remark = fields.Char(string="Remarks")
    hospitalization_id = fields.Many2one("acs.hospitalization", ondelete="cascade", string="Hospitalization")


class PreWardCheckListTemplate(models.Model):
    _name="pre.ward.check.list.template"
    _description = "Pre Ward Checklist Template"

    name = fields.Char(string="Name", required=True)
    remark = fields.Char(string="Remarks")


class PreWardCheckList(models.Model):
    _name="pre.ward.check.list"
    _description = "Pre Ward Checklist"

    name = fields.Char(string="Name", required=True)
    is_done = fields.Boolean(string="Done")
    remark = fields.Char(string="Remarks")
    hospitalization_id = fields.Many2one("acs.hospitalization", ondelete="cascade", string="Hospitalization")


class PatientAccommodationHistory(models.Model):
    _name = "patient.accommodation.history"
    _rec_name = "patient_id"
    _description = "Patient Accommodation History"

    def _rest_time(self):
        for registration in self:
            rest_time = 0
            end_date = registration.end_date or fields.Datetime.now()
            if end_date and registration.start_date:
                diff = end_date - registration.start_date
                if registration.bed_id.invoice_policy=='full' and registration.extra_bed_id.invoice_policy=='full':
                    rest_time = diff.days if diff.days > 0 else 1
                else:
                    total_seconds = int(diff.total_seconds())
                    rest_time = (total_seconds/3600) if total_seconds else 0
            registration.rest_time = rest_time

    @api.depends('account_move_line_ids')
    def acs_get_move_lines_data(self):
        for rec in self:
            rec.invoiced_rest_time = sum(rec.account_move_line_ids.mapped('quantity'))

    hospitalization_id = fields.Many2one('acs.hospitalization', ondelete="cascade", string='Inpatient')
    patient_id = fields.Many2one('hms.patient', ondelete="restrict", string='Patient', required=True)
    ward_id = fields.Many2one('hospital.ward', ondelete="restrict", string='Ward/Room')
    bed_id = fields.Many2one('hospital.bed', ondelete="restrict", string='Bed No.')
    extra_bed_id = fields.Many2one ('hospital.bed', ondelete="restrict", string='Extra Person Bed No.')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    rest_time = fields.Float(compute=_rest_time, string='Rest Time')
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Hospital', related='hospitalization_id.company_id') 
    invoice_policy = fields.Selection(related="bed_id.invoice_policy", string='Invoice Policy', readonly=True)
    account_move_line_ids = fields.Many2many('account.move.line', 'acs_accomodation_account_move_line_rel', 'move_id', 'accommodation_id', string='Invoice Lines')
    invoiced_rest_time = fields.Float(compute="acs_get_move_lines_data", string="Invoiced Rest Time")
    nutrition_id = fields.Many2one('acs.hospitalization', string='Nutrition')
    food_category = fields.Selection([
        ('breakfast', 'Breakfast'),
        ('pre_lunch_snacks', 'Pre-Lunch Snacks'),
        ('lunch', 'Lunch'),
        ('post_lunch_snacks', 'Post-Lunch Snacks'),
        ('dinner', 'Dinner'),
        ('late_night_snacks', 'Late Night Snacks'),
        ('any_other_eatables', 'Any Other Eatables')],
        string='Food Category')
    timing = fields.Char(string='Timing')
    usual_items = fields.Char(string='Usual items')
    regularity = fields.Selection([
        ('regular', 'Regular'),
        ('irregular', 'Irregular')],
        string='Regular / Irregular')

class WardRounds(models.Model):
    _name = "ward.rounds"
    _description = "Ward Rounds"

    instruction = fields.Char(string='Instruction')
    remarks = fields.Char(string='Remarks')
    hospitalization_id = fields.Many2one('acs.hospitalization', ondelete="restrict",string='Inpatient')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    physician_id = fields.Many2one('hms.physician', string='Physician', ondelete="restrict")
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)


class ACSDietPlan(models.Model):
    _name = "hms.diet.plan"
    _description = "Diet Plan"

    name = fields.Many2one('product.template', string='Meal Name', domain=[('detailed_type', '=', 'consu'),('hospital_product_type','=','fdrinks')])
    uom_id = fields.Many2one(
        'uom.uom', 
        string='Unit of Measure', 
        related='name.uom_id',
        readonly=True,
    )
    quantity = fields.Float(string='Quantity')
    calories_count = fields.Float(string='Calories',compute="_onchange_quantity_update_calories",readonly=False)
    time = fields.Selection([
        ('01:00', '01:00'),
        ('02:00', '02:00'),
        ('03:30', '03:30'),
        ('04:00', '04:00'),
        ('05:00', '05:00'),
        ('06:00', '06:00'),
        ('07:00', '07:00'),
        ('08:00', '08:00'),
        ('09:00', '09:00'),
        ('10:00', '10:00'),
        ('11:00', '11:00'),
        ('12:00', '12:00'),
        ('13:00', '13:00'),
        ('14:00', '14:00'),
        ('15:00', '15:00'),
        ('16:00', '16:00'),
        ('17:00', '17:00'),
        ('18:00', '18:00'),
        ('19:00', '19:00'),
        ('20:00', '20:00'),
        ('21:00', '21:00'),
        ('22:00', '22:00'),
        ('23:00', '23:00'),
        ('24:00', '24:00'),
        # Add more options as needed
    ], string='Time')
    care_plan_id = fields.Many2one('hms.care.plan.template', string='Care Plan')
    plan_care_id = fields.Many2one('acs.hospitalization')

    @api.depends('quantity','name')
    def _onchange_quantity_update_calories(self):
        for rec in self:
            print("kkkkkkkkkkkkkkkkk",rec.name.id,rec.name.calories_count)
            rec.calories_count = rec.quantity * rec.name.calories_count
            

class ACSCarePlanTemplate(models.Model):
    _name = "hms.care.plan.template"
    _description = "Care Plan Template"

    name = fields.Char(string='Care Plan Name')
    diseases_id = fields.Many2one('hms.diseases', ondelete='restrict', string='Disease')
    nursing_plan = fields.Text(string='Nursing Plan')
    diet_plan_ids = fields.One2many('hms.diet.plan', 'care_plan_id', string='Diet Plan')


# ******************diet chart model **************************

class ACSDietChart(models.Model):
    _name = "hms.diet.chart"
    _description = "Diet Chart Template"

    diet_chart_id = fields.Many2one('acs.hospitalization')
    diet_plan_id = fields.Many2one('acs.hospitalization')
    body_chart_id = fields.Many2one('acs.hospitalization')
    timings = fields.Selection([
        ('EARLY MORNING-6:30AM','EARLY MORNING-6:30AM'),
        ('BREAKFAST 7:30- 8 AM','BREAKFAST 7:30- 8 AM'),
        ('MID MORNING 10:30-11 AM','MID MORNING 10:30-11 AM'),
        ('LUNCH 12:30-1:30 PM','LUNCH 12:30-1:30 PM'),
        ('EVENING SNACKS 3:30- 4 PM','EVENING SNACKS 3:30- 4 PM'),
        ('DINNER 7:30 – 8 PM','DINNER 7:30 – 8 PM'),
        ('BED TIME 9 PM','BED TIME 9 PM'),

        ])
    sunday = fields.Text(string='Sunday')
    monday = fields.Text(string='Monday')
    tuesday = fields.Text(string='Tuesday')
    wednesday = fields.Text(string='Wednesday')
    thursday = fields.Text(string='Thursday')
    friday = fields.Text(string='Friday')
    saturday = fields.Text(string='Saturday')
    date = fields.Date(string="Date")
    food_quantity = fields.Char(string="FOOD QUANTITY")
    food_quality = fields.Char(string="FOOD QUALITY")
    constipation = fields.Char(string="Constipation")
    indigestion = fields.Char(string="Indigestion")
    complaints = fields.Char(string="Complaints")
    fcr = fields.Char(string = "Food changes recommended")
    pre_post = fields.Selection([
        ('pre', 'Pre'),
        ('post', 'Post')
    ], string="Pre/Post")
    weight = fields.Float(string="WEIGHT")
    visceral_fat = fields.Float(string="Visceral fat")
    body_fat = fields.Float(string="Body fat")
    bmi = fields.Float(string="BMI")
    b_a = fields.Float(string="Biological age")
    chest = fields.Float(string="CHEST")
    rt_arm = fields.Char(string="RT.ARM")
    lt_arm = fields.Char(string="LT.ARM")
    rt_waist = fields.Char(string="RT.WAIST")
    lt_waist = fields.Char(string="LT.WAIST")
    waist = fields.Char(string="WAIST")
    hip = fields.Char(string="HIP")
    lt_thigh = fields.Char(string="LT_THIGH")
    rt_thigh = fields.Char(string="RT_THIGH")





# class ACSDietChartPlanTemplate(models.Model):
#     _name = "hms.diet.chart.plan.template"
#     _description = "Diet Chart Plan Template"

#     diet_chart_ids = fields.One2many('hms.diet.chart','diet_chart_plan_id',string='diet chart')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: