# coding=utf-8

from odoo import api, fields, models, _, exceptions
from datetime import datetime, date, timedelta
import dateutil.relativedelta
from odoo.exceptions import ValidationError, AccessError, UserError, RedirectWarning, Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class Hospitalization(models.Model):
    _name = "acs.hospitalization"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin']
    _description = "Patient Hospitalization"
    _order = "id desc"


    @api.model
    def get_treatments(self):
        # Retrieve treatments for the current patient
        treatments = self.env["hms.treatment"].search([('patient_id', '=', self.patient_id.id)])
        print("KKKKKKKKKKKKKKKKKKKKKKKKKKK",treatments)

        return treatments

    @api.model
    def _default_checklist(self):
        vals = []
        checklists = self.env['inpatient.checklist.template'].search([])
        for checklist in checklists:
            vals.append((0, 0, {
                'name': checklist.name,
                'remark': checklist.remark,
            }))
        return vals

    @api.model
    def _default_prewardklist(self):
        vals = []
        prechecklists = self.env['pre.ward.check.list.template'].search([])
        for prechecklist in prechecklists:
            vals.append((0,0,{
                'name': prechecklist.name,
                'remark': prechecklist.remark,
            }))
        return vals

    def _rec_count(self):
        Treatment = self.env['hms.treatment']
        for rec in self:
            rec.invoice_count = len(rec.sudo().invoice_ids)
            rec.prescription_count = len(rec.prescription_ids.ids)
            rec.surgery_count = len(rec.surgery_ids)
            rec.accommodation_count = len(rec.accommodation_history_ids)
            rec.evaluation_count = len(rec.evaluation_ids)
            # rec.treatment_count = len(rec.treatment_ids)
            rec.treatment_count = Treatment.search_count([('patient_id','=',self.patient_id.id)])

    @api.depends('checklist_ids','checklist_ids.is_done')
    def _compute_checklist_done(self):
        for rec in self:
            if rec.checklist_ids:
                done_checklist = rec.checklist_ids.filtered(lambda s: s.is_done)
                rec.checklist_done = (len(done_checklist)* 100)/len(rec.checklist_ids)
            else:
                rec.checklist_done = 0

    @api.depends('pre_ward_checklist_ids','pre_ward_checklist_ids.is_done')
    def _compute_pre_ward_checklist_done(self):
        for rec in self:
            if rec.pre_ward_checklist_ids:
                done_checklist = rec.pre_ward_checklist_ids.filtered(lambda s: s.is_done)
                rec.pre_ward_checklist_done = (len(done_checklist)* 100)/len(rec.pre_ward_checklist_ids)
            else:
                rec.pre_ward_checklist_done = 0

    

    READONLY_STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}

    name = fields.Char(string='Hospitalization#', copy=False, default="Hospitalization#", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('reserved', 'Reserved'),
        ('hosp','Hospitalized'), 
        ('discharged', 'Discharged'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),], string='Status', default='draft', tracking=True)
    discharge_type = fields.Selection([('emergency','Emergency'),('against_advice','Against Advice')], string='Discharge Type')
    gst_number = fields.Char(string='GST NO.', related='patient_id.partner_id.vat', readonly=False)
    pan_number = fields.Char(string='PAN Number', required=True)
    aadhar_number = fields.Char(string='AADHAR Number', required=True)
    title = fields.Selection([
        ('mr', 'Mr'),
        ('mrs', 'Mrs'),
        ('miss', 'Miss')
    ], string="Title")
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    patient_id = fields.Many2one('hms.patient', ondelete="restrict", string='Patient', states=READONLY_STATES, tracking=True)
    image_128 = fields.Binary(related='patient_id.image_128',string='Image', readonly=True)
    age = fields.Char(string="Age" ,related="patient_id.age")
    appointment_id = fields.Many2one('hms.appointment', ondelete="restrict", 
        string='Appointment', states=READONLY_STATES)
    hospitalization_date = fields.Datetime(string='Hospitalization Date', 
        default=fields.Datetime.now, states=READONLY_STATES, tracking=True)
    company_id = fields.Many2one('res.company', ondelete="restrict", 
        string='Hospital', default=lambda self: self.env.company, 
        states=READONLY_STATES)
    department_id = fields.Many2one('hr.department', ondelete="restrict", 
        string='Department', domain=[('patient_department', '=', True)], states=READONLY_STATES)
    attending_physician_ids = fields.Many2many('hms.physician','hosp_pri_att_doc_rel','hosp_id','doc_id',
        string='ASSISTANT DOCTOR', states=READONLY_STATES)
    relative_id = fields.Many2one('res.partner', ondelete="cascade", 
        domain=[('type', '=', 'contact')], string='Emergency Contact Name', states=READONLY_STATES)
    relative_number = fields.Char(string='Emergency Contact Number', states=READONLY_STATES)
    ward_id = fields.Many2one('hospital.ward', ondelete="restrict", string='Room Category', states=READONLY_STATES)
    bed_id = fields.Many2one ('hospital.bed', ondelete="restrict", string='Bed No.', states=READONLY_STATES)
    extra_bed_id = fields.Many2one ('hospital.bed', ondelete="restrict", string='Extra Person Bed No.', states=READONLY_STATES)
    admission_type = fields.Selection([
        ('routine','Routine'),
        ('elective','Elective'),
        ('urgent','Urgent'),
        ('emergency','Emergency')], string='Admission type', default='routine', states=READONLY_STATES)
    diseases_ids = fields.Many2many('hms.diseases', 'diseases_hospitalization_rel', 'diseas_id', 'hospitalization_id', 
        string='Diseases', states=READONLY_STATES)
    discharge_date = fields.Datetime (string='Discharge date', states=READONLY_STATES, tracking=True)
    invoice_exempt = fields.Boolean(string='Invoice Exempt', states=READONLY_STATES)
    accommodation_history_ids = fields.One2many("patient.accommodation.history", "hospitalization_id", 
        string="Accommodation History", states=READONLY_STATES)
    accommodation_count = fields.Integer(compute='_rec_count', string='# Accommodation History')
    physician_id = fields.Many2one('hms.physician', string='CHIEF CONSULTANT', states=READONLY_STATES, tracking=True)

    #CheckLists
    checklist_ids = fields.One2many('inpatient.checklist', 'hospitalization_id', 
        string='Admission Checklist', default=lambda self: self._default_checklist(), 
        states=READONLY_STATES)
    checklist_done = fields.Float('Admission Checklist Done', compute='_compute_checklist_done', store=True)
    pre_ward_checklist_ids = fields.One2many('pre.ward.check.list', 'hospitalization_id', 
        string='Pre-Ward Checklist', default=lambda self: self._default_prewardklist(), 
        states=READONLY_STATES)
    pre_ward_checklist_done = fields.Float('Pre-Ward Checklist Done', compute='_compute_pre_ward_checklist_done', store=True)

    #Hospitalization Surgery
    picking_type_id = fields.Many2one('stock.picking.type', ondelete="restrict", 
        string='Picking Type', states=READONLY_STATES)

    consumable_line_ids = fields.One2many('hms.consumable.line', 'hospitalization_id',
        string='Consumable Line', states=READONLY_STATES)

    treatment_line_ids = fields.One2many('hms.treatment.line', 'hospitalization_id',
        string='Treatments Line', states=READONLY_STATES)
    #history of illness fields
    reason_for_admission = fields.Text(string="PROVISANAL DIAGNOSIS", states=READONLY_STATES)
    observations_during_admission = fields.Text(string="HISTORY OF PRESENT COMPLAINTS:", states=READONLY_STATES)
    past_history = fields.Text(string="PAST HISTORY:", states=READONLY_STATES)
    pth_pm = fields.Text(string="PAST TREATMENT HISTORY &PRESENT MEDICATION")
    gh_oh = fields.Text(string="GYNECOLOGICAL HISTORY &OBSTETRICS HISTORY")

    #personal/family History
    family_history = fields.Text(string="FAMILY HISTORY")
    personal_history = fields.Text(string="PERSONAL HISTORY")
    appetite = fields.Char(string="APPETITE")
    sleep = fields.Char(string="SLEEP")
    habbits = fields.Char(string="HABBITS")
    bowel = fields.Char(string="BOWEL")
    micturation = fields.Char(string="MICTURATION")

    #VITAL EXAMINATION fields
    temp = fields.Float(string="TEMPERATURE")
    pulse = fields.Integer(string="PULSE")
    bp = fields.Char(string="BLOOD PRESSURE")
    rr = fields.Integer(related="last_evaluation_id.rr", string='RR', readonly=True, help='Respiratory Rate')
    spo2 = fields.Integer(related="last_evaluation_id.spo2", string='SpO2', readonly=True, 
        help='Oxygen Saturation, percentage of oxygen bound to hemoglobin')
    temp = fields.Float(related="last_evaluation_id.temp", string='Temp', readonly=True)

    #PHYSICAL EXAMINATION
    buit = fields.Char(string="UNDER WEIGHT/NORMAL WEIGHT/OVER WEIGHT")
    appearance = fields.Char(string = "APPEARANCE:")
    pallor = fields.Char(string="PALLOR:")
    iceterus = fields.Char(string="ICTERUS:")
    cyanosis = fields.Char(string="CYANOSIS:")
    edema = fields.Char(string="EDEMA")
    ln = fields.Char(string="LYMPHADENOPATHY")
    club = fields.Char(string="CLUBBING")
    tongue = fields.Char(string="TONGUE")
    nails = fields.Char(string="NAILS")
    eyes = fields.Char(string ="EYES")
    skin = fields.Char(string = "SKIN")
    hair = fields.Char(string = "HAIR")
    existing_investigation = fields.Text(string="EXISITING INVESTIGATION IF ANY")
    # SYSTEMIC EXAMINATION
    cs = fields.Char(string="CARDIOVASCULAR SYSTEM")
    gs = fields.Char(string="GASTRO-INTESTINAL SYSTEM")
    gus = fields.Char(string="GENITO-URINARY SYSTEM")
    cns = fields.Selection([('sensory',"SENSORY"),('loco_motor',"LOCO-MOTOR"),('other',"OTHER")], string="CENTRAL NERVOUS SYSTEM")
    # cns_description = fields.Char()
    msystem = fields.Char(string="MUSCULOSKELETAL SYSTEM")
    rsystem = fields.Char(string="RESPIRATORY SYSTEM")
    es = fields.Char(string="ENDOCRINE SYSTEM")
    ps = fields.Char(string="PSYCHIATRIC")
    skin = fields.Char(string="SKIN")
    assessment = fields.Selection([('ayurveda',"AYURVEDA"),('naturopathy',"NATUROPATHY"),('homupathy',"HOMEOPATHY"),('unnai',"UNNANI"),('siddha',"SIDDA")], string="ASSESSMENT")
    dd = fields.Text(string="DIFFERENTIAL DIAGNOSIS")
    at = fields.Char(string="AYURVEDA TREATMENT")
    nt = fields.Char(string="NATUROPATHY TREATMENT")
    ut = fields.Char(string="UNANI TREATMENT")
    st = fields.Char(string="SIDDHA TREATMENT")
    #CLINICAL ASSESSMENT FIELDS
    puls = fields.Integer(related="last_evaluation_id.puls",string='Pulse', states=READONLY_STATES)
    bloodp = fields.Integer(related="last_evaluation_id.bloodp",string='BP', states=READONLY_STATES)
    slep = fields.Integer(related="last_evaluation_id.slep",string="Sleep", states=READONLY_STATES)
    bow = fields.Char(related="last_evaluation_id.bow",string="BOWEL:")
    apt = fields.Char(related="last_evaluation_id.apt",string="APPETIT:")
    uri = fields.Char(related="last_evaluation_id.uri",string="URINATION:")
    # ****************************h**********************************
    anc = fields.Text(related="last_evaluation_id.anc",string="ANY NEW COMPLIANTS:")
    anp = fields.Text(related="last_evaluation_id.anp",string="ANY CHANGES IN PROTOCAL:")
    yes_box1 = fields.Boolean(related="last_evaluation_id.yes_box1",string="Yes")
    no_box1 = fields.Boolean(related="last_evaluation_id.no_box1",string="No")
    yes_box2 = fields.Boolean(related="last_evaluation_id.yes_box2",string="Yes")
    no_box2 = fields.Boolean(related="last_evaluation_id.no_box2",string="No")
    yes_box3 = fields.Boolean(related="last_evaluation_id.yes_box3",string="Yes")
    no_box3 = fields.Boolean(related="last_evaluation_id.no_box3",string="No")
    anm = fields.Text(related="last_evaluation_id.anm",string="ANY CHANGES IN MEDICATION:")
    ai = fields.Text(related="last_evaluation_id.ai",string="ANY IMPROVEMENT")
        # ****************************h**********************************

    
    rr = fields.Integer(related="last_evaluation_id.rr",string='RR', states=READONLY_STATES, help='Respiratory Rate')
    spoo2 = fields.Integer(related="last_evaluation_id.spo2",string='SpO2', states=READONLY_STATES, 
        help='Oxygen Saturation, percentage of oxygen bound to hemoglobin')
    tempr = fields.Float(related="last_evaluation_id.temp",string='Temp', states=READONLY_STATES)
    # Discharge fields
    diagnosis = fields.Text(string="Diagnosis", states=READONLY_STATES)
    clinincal_history = fields.Text(string="Clinical Summary", states=READONLY_STATES)
    examination = fields.Text(string="Examination", states=READONLY_STATES)
    investigation = fields.Text(string="Investigation", states=READONLY_STATES)
    adv_on_dis = fields.Text(string="Advice on Discharge", states=READONLY_STATES)
    examination_at_discharge = fields.Text(string="Examination During Discharge", states=READONLY_STATES)
    chief_complaint = fields.Text(string="CHIEF COMPLAINT", states=READONLY_STATES)
    reason_for_hospitalization = fields.Text(string="Reason For Hospitalization",states=READONLY_STATES)
    ho = fields.Text(string="Condition of patient at time of Discharge", states=READONLY_STATES)
    obg = fields.Text(string="OBG History", states=READONLY_STATES)
    instructions = fields.Text(string='Instructions', states=READONLY_STATES)
    ivestigaing_addmision = fields.Text(string="INVESTIGATIN RESULTS AT THE TIME OF ADDMISSION")
    #diet assesment fields
    vegetarian_type = fields.Selection([
        ('non_veg', 'Non-Vegetarian'),
        ('veg', 'Vegetarian'),
        ('vegan', 'Vegan')],
        string='Are you Non-Veg/Vegetarian/Vegan?')
    
    liked_fruits = fields.Char(string='Write three most loved fruits/vegetables that you love to eat')
    disliked_fruits = fields.Char(string='Write three most found fruits/vegetables that you dislike to eat')

    special_diet = fields.Boolean(string='Do you have any special/restricted diet')
    diet_name = fields.Char(string='If Yes please specify names of diet and reason')
    final_dd = fields.Text(string="FINAL DIAGNOSIS")
    food_category = fields.One2many('patient.accommodation.history', 'nutrition_id', string='Food Category')
    outside_food_frequency = fields.Char(string='How often do you eat out side food')
    food_items = fields.Char(string='Do you take the following food items')
    water_consumption = fields.Boolean(string='Do you consume more than 3 liters of water per day')
    fast_food = fields.Boolean(string="Fast Foods")
    fried_food = fields.Boolean(string="Fried Foods")
    milk_product = fields.Boolean(string="Milk Products")
    carbonate_bev = fields.Boolean(string="Carbonate Beverages")
    sweets = fields.Boolean(string="Sweets")
    coffee_tea = fields.Boolean(string="Coffee/Tea")
    aftrificial = fields.Boolean(string="Artificial Sweets/Pan Parak/Meat")
    #Nutrition Protocol
    proposed_calories_day = fields.Char(string="Proposed calories / day")
    food_policy_concept = fields.Char(string="Food Policy - concept")
    additional_food_supplements = fields.Char(string="Additional special food supplements")

    #BODY PARAMETERS
    patient_height = fields.Float(string="Height(Cms)")
    ideal_body_weight = fields.Float(string="Ideal Body Weight(Kgs)")
    current_weight = fields.Float(string="Current Weight(Kgs)")
    ideal_bmi = fields.Char(string="Ideal Bmi")
    current_bmi = fields.Char(string="Current Bmi")
    resting_metabolic_rate = fields.Char(string="Resting Metabolic Rate")
    year_ago_weight = fields.Float(string="Year Ago Weight(Kgs)")
    #Legal Details
    legal_case = fields.Boolean('Legal Case', states=READONLY_STATES)
    medico_legal = fields.Selection([
        ('yes','Yes'),
        ('no','No')], string="If Medico legal", states=READONLY_STATES)
    reported_to_police = fields.Selection([
        ('yes','Yes'),
        ('no','No')], string="Reported to police", states=READONLY_STATES)
    fir_no = fields.Char(string="FIR No.", states=READONLY_STATES, help="Registration number of the police complaint.")
    fir_reason = fields.Char(string="If not reported to police give reason", states=READONLY_STATES)

    #For Basic Care Plan
    nurse_id = fields.Many2one('res.users', ondelete="cascade", string='Primary Nurse', 
        help='Anesthetist data of the patient', states=READONLY_STATES)
    nursing_plan = fields.Text (string='Nursing Plan', states=READONLY_STATES)
    physician_ward_round_ids = fields.One2many('ward.rounds', 'hospitalization_id', string='Physician Ward Rounds', states=READONLY_STATES)
    plan_diet_ids = fields.One2many('hms.diet.plan', 'plan_care_id', string='Diet Plan')
    #Daily Nutritional progress
    diet_plan_ids = fields.One2many('hms.diet.chart', 'diet_plan_id', string='Diet chart')
    date = fields.Date(string="Date")
    food_quantity = fields.Char(string="FOOD QUANTITY")
    food_quality = fields.Char(string="FOOD QUALITY")
    constipation = fields.Char(string="Constipation")
    indigestion = fields.Char(string="Indigestion")
    complaints = fields.Char(string="Complaints")
    fcr = fields.Char(string = "Food changes recommended")
    #body parameter
    body_chart_ids = fields.One2many('hms.diet.chart','body_chart_id', string='Body Chart')

  # *************diet chart******************************************************
    diet_chart_ids = fields.One2many('hms.diet.chart', 'diet_chart_id', string='Diet chart')
    patient_weight_check_in =fields.Float(string='Weight Check In')
    patient_weight_check_out =fields.Float(string='Weight Check Out')

    patient_height = fields.Float(string="Height(Cms)")
    ideal_body_weight = fields.Float(string="IBW(Kgs)")
    body_massage_index= fields.Float(string="BMI(kg/m^2)")
    hemoglobin_a1c = fields.Float(string="HBA1C")
    fasting_blood_sugar = fields.Char(string="FBS")
    blood_pressure = fields.Char(string="BP")

    
    fats = fields.Char(string="Fats")
    sweets = fields.Char(string="Sweets")
    bakery_products = fields.Char(string="Bakery Products")
    drinks = fields.Char(string="Drinks")
    fast_or_oil_foods = fields.Char(string="Fast Foods/Oil Foods")
    refined_products = fields.Char(string="Refined products")
    other_foods_need_to_avoid = fields.Char(string="Other Foods Need To Avoid")

    water = fields.Char(string="water")
    oil = fields.Char(string="Oil")
    salt = fields.Char(string="Salt")
    sleep = fields.Char(string="Sleep")
    exercise = fields.Char(string="Exercise")

    millet_rice = fields.Char(string="Millet Rice")
    Any_veg_Curry_or_dhal = fields.Char(string="Any veg Curry/Dhal")
    boiled_steamed_veggies = fields.Char(string="Boiled Steamed Veggies")
    fry = fields.Char(string="Fry")
    soup = fields.Char(string="Soup")
    buttermilk = fields.Char(string="Buttermilk")


    # **********************************************************************

    discharge_plan = fields.Text (string='Diet Advice At the time of Discharge', states=READONLY_STATES)
    move_ids = fields.One2many('stock.move','hospitalization_id', string='Moves', states=READONLY_STATES)
    invoice_ids = fields.One2many('account.move', 'hospitalization_id', 'Invoices')

    invoice_count = fields.Integer(compute='_rec_count', string='# Invoices')
    prescription_ids = fields.One2many('prescription.order', 'hospitalization_id', 'Prescriptions')
    prescription_count = fields.Integer(compute='_rec_count', string='# Prescriptions')
    surgery_ids = fields.One2many('hms.surgery', 'hospitalization_id', "Surgeries")
    surgery_count = fields.Integer(compute='_rec_count', string='# Surgery')
    ref_physician_id = fields.Many2one('res.partner', ondelete='restrict', string='Referring Physician', 
        index=True, help='Referring Physician', states=READONLY_STATES)
    death_register_id = fields.Many2one('patient.death.register', string='Death Register', states=READONLY_STATES)
    care_plan_template_id = fields.Many2one('hms.care.plan.template', ondelete='restrict',
        string= "Menu Plan Template", states=READONLY_STATES)

    evaluation_ids = fields.One2many('acs.patient.evaluation', 'hospitalization_id', '#Evaluations')
    evaluation_count = fields.Integer(compute="_rec_count", string='Evaluations')
    allow_bed_reservation = fields.Boolean('Allow Bed Reservation', related='company_id.allow_bed_reservation')
    procedure_id = fields.Many2one('acs.patient.procedure', string='Procedure')
    procedure_date = fields.Many2one('acs.patient.procedure', string='Procedure')
    last_evaluation_id = fields.Many2one("acs.patient.evaluation", related='patient_id.last_evaluation_id', string="Last Evaluation")
    weight = fields.Float(related="last_evaluation_id.weight", string='Weight', help="Weight in KG", readonly=True)
    height = fields.Float(related="last_evaluation_id.height", string='Height', help="Height in cm", readonly=True)
    temp = fields.Float(related="last_evaluation_id.temp", string='Temp', readonly=True)
    pr = fields.Integer(related="last_evaluation_id.pr", string='PR', readonly=True)
    hr = fields.Integer(related="last_evaluation_id.hr", string='HR', help="Heart Rate", readonly=True)
    rr = fields.Integer(related="last_evaluation_id.rr", string='RR', readonly=True, help='Respiratory Rate')
    systolic_bp = fields.Integer(related="last_evaluation_id.systolic_bp", string="Systolic BP")
    diastolic_bp = fields.Integer(related="last_evaluation_id.diastolic_bp", string="Diastolic BP")
    spo2 = fields.Integer(related="last_evaluation_id.spo2", string='SpO2', readonly=True, 
        help='Oxygen Saturation, percentage of oxygen bound to hemoglobin')
    rbs = fields.Integer(related="last_evaluation_id.rbs", string='RBS', readonly=True, 
        help='Random blood sugar measures blood glucose regardless of when you last ate.')
    bmi = fields.Float(related="last_evaluation_id.bmi", string='Body Mass Index', readonly=True)
    bmi_state = fields.Selection(related="last_evaluation_id.bmi_state", string='BMI State', readonly=True)
    
    pain_level = fields.Selection(related="last_evaluation_id.pain_level", string="Pain Level", readonly=True)
    pain = fields.Selection(related="last_evaluation_id.pain", string="Pain", readonly=True)

    acs_weight_name = fields.Char(related="last_evaluation_id.acs_weight_name", string='Patient Weight unit of measure label')
    acs_height_name = fields.Char(related="last_evaluation_id.acs_height_name", string='Patient Height unit of measure label')
    acs_temp_name = fields.Char(related="last_evaluation_id.acs_temp_name", string='Patient Temp unit of measure label')
    acs_spo2_name = fields.Char(related="last_evaluation_id.acs_spo2_name", string='Patient SpO2 unit of measure label')
    acs_rbs_name = fields.Char(related="last_evaluation_id.acs_rbs_name", string='Patient RBS unit of measure label')
    treatment_count = fields.Integer(compute='_rec_count', string='# Treatments')
    treatment_ids = fields.One2many('hms.treatment', 'hospital_id', 'Treatments')

    csv = fields.Integer(related="last_evaluation_id.csv", string='CSV', readonly=True)
    rs = fields.Integer(related="last_evaluation_id.rs", string='RS', readonly=True)
    ms = fields.Integer(related="last_evaluation_id.ms", string='MS', readonly=True)
    ns = fields.Integer(related="last_evaluation_id.ns", string='NS', readonly=True)
    gi = fields.Integer(related="last_evaluation_id.gi", string='GI', readonly=True)
    others = fields.Char(related="last_evaluation_id.others", string='Others', readonly=True)

    survey_id = fields.Many2one('survey.survey',string="Survey")

    # combining both title and name to display in report


    @api.depends('title', 'name')
    def _compute_display_name(self):
        for patient in self:
            if patient.title:
                patient.display_name = f"{dict(self.fields_get(allfields=['title'])['title']['selection'])[patient.title]} {patient.patient_id.name}"
            else:
                patient.display_name = patient.patient_id.name





    def action_treatment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.acs_action_form_hospital_treatment")
        action['domain'] = [('patient_id','=',self.patient_id.id)]
        action['context'] = {'default_patient_id': self.patient_id.id}
        return action

    def action_payment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")
        
        # Ensure that self.patient_id is correctly set
        if self.patient_id:
            partner_name = self.patient_id.name
            action['domain'] = [('partner_id', '=', self.patient_id.partner_id.id)]
            action['context'] = {'default_partner_id': self.patient_id.partner_id.id,
                                 'default_partner_name': partner_name}
        return action

    @api.onchange('patient_id')
    def onchange_patient(self):
        if self.patient_id:
            self.gst_number = self.patient_id.vat

    @api.onchange('care_plan_template_id')
    def on_change_care_plan_template_id(self):
        if self.care_plan_template_id:
            self.nursing_plan = self.care_plan_template_id.nursing_plan
             # Retrieve the diet plans from the selected care_plan_template_id
            diet_plans = self.care_plan_template_id.diet_plan_ids
            
            # Clear existing plan_diet_ids
            self.plan_diet_ids = [(5, 0, 0)]
            
            # Assign the retrieved diet plans to the plan_diet_ids field
            self.plan_diet_ids = [(0, 0, {
                'name': plan.name,
                'quantity': plan.quantity,
                'calories_count':plan.calories_count,
                'uom_id': plan.uom_id.id,
                'time': plan.time,
            }) for plan in diet_plans]
            
    def action_view_evaluation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_evaluation")
        action['domain'] = [('hospitalization_id','=',self.id)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id, 'default_physician_id': self.physician_id.id}
        return action

    _sql_constraints = [
        ('name_company_uniq', 'unique (name,company_id)', 'Hospitalization must be unique per company !')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            patient_id = values.get('patient_id')
            active_hospitalizations = self.search([('patient_id','=',patient_id),('state','not in',['cancel','done','discharged'])])
            if active_hospitalizations:
                raise ValidationError(_("Patient Hospitalization is already active at the moment. Please complete it before creating new."))
            if values.get('name', 'Hospitalization#') == 'Hospitalization#':
                values['name'] = self.env['ir.sequence'].next_by_code('acs.hospitalization') or 'Hospitalization#'
        return super().create(vals_list)

    def action_confirm(self):
        self.state = 'confirm'

    def action_reserve(self):
        History = self.env['patient.accommodation.history']
        for rec in self:
            rec.bed_id.sudo().write({'state': 'reserved'})
            rec.state = 'reserved'
            History.sudo().create({
                'hospitalization_id': rec.id,
                'patient_id': rec.patient_id.id,
                'ward_id': self.ward_id.id,
                'bed_id': self.bed_id.id,
                'extra_bed_id': self.extra_bed_id.id,
                'start_date': datetime.now(),
            })

    def action_hospitalize(self):
        History = self.env['patient.accommodation.history']
        for rec in self:
            if not self.allow_bed_reservation:
                History.sudo().create({
                    'hospitalization_id': rec.id,
                    'patient_id': rec.patient_id.id,
                    'ward_id': self.ward_id.id,
                    'bed_id': self.bed_id.id,
                    'extra_bed_id': self.extra_bed_id.id,
                    'start_date': datetime.now(),
                })
            rec.bed_id.sudo().write({'state': 'occupied'})
            rec.extra_bed_id.sudo().write({'state': 'occupied'})
            rec.state = 'hosp'
            rec.patient_id.write({'hospitalized': True})

    def action_discharge(self):
        print(self.treatment_ids,"--------------------------------------")
        for rec in self:
            rec.bed_id.sudo().write({'state': 'free'})
            rec.extra_bed_id.sudo().write({'state': 'free'})
            rec.state = 'discharged'
            rec.discharge_date = datetime.now()
            for history in rec.accommodation_history_ids:
                if rec.bed_id == history.bed_id and rec.extra_bed_id == history.extra_bed_id:
                    history.sudo().end_date = datetime.now()
            if rec.survey_id:
                get_form = rec.survey_id.action_send_survey()
                context = get_form['context']
                if not rec.patient_id.email:
                    raise ValidationError(_("Please add email in patient to send survey Form"))
                context['default_emails']= rec.patient_id.email
                survey_invite_id = self.env['survey.invite'].with_context(get_form['context']).create({})
                survey_invite_id.action_invite()


            rec.patient_id.write({'discharged': True})

    def action_done(self):
        self.state = 'done'
        self.consume_hopitalization_material()
        if not self.discharge_date:
            self.discharge_date = datetime.now()

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
            rec.bed_id.sudo().write({'state': 'free'}) 
            rec.extra_bed_id.sudo().write({'state': 'free'}) 

    def action_create_evaluation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_evaluation_popup")
        action['domain'] = [('patient_id','=',self.id)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_hospitalization_id': self.id}
        return action

    def action_draft(self):
        self.state = 'draft'

    def action_prescription(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_hms_prescription_order_view")
        action['domain'] = [('hospitalization_id', '=', self.id)]
        action['context'] = {
            'default_patient_id': self.patient_id.id,
            'default_physician_id':self.physician_id.id,
            'default_hospitalization_id': self.id,
            'default_ward_id': self.ward_id.id,
            'default_diseases_ids': [(6,0,self.diseases_ids.ids)],
            'default_bed_id': self.bed_id.id,
            }
        return action

    def action_accommodation_history(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms_hospitalization.action_accommodation_history")
        action['domain'] = [('hospitalization_id', '=', self.id)]
        action['context'] = {
            'default_patient_id': self.patient_id.id,
            'default_hospitalization_id': self.id}
        return action

    # def action_view_surgery(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("acs_hms_surgery.action_hms_surgery")
    #     action['domain'] = [('hospitalization_id', '=', self.id)]
    #     action['context'] = {
    #         'default_patient_id': self.patient_id.id,
    #         'default_hospitalization_id': self.id}
    #     return action

    def view_invoice(self):
        invoices = self.env['account.move'].search([('hospitalization_id', '=', self.id)])
        action = self.acs_action_view_invoice(invoices)
        return action

    def acs_get_consume_locations(self):
        if not self.company_id.acs_hospitalization_usage_location_id:
            raise UserError(_('Please define a location where the consumables will be used during the surgery in company.'))
        if not self.company_id.acs_hospitalization_stock_location_id:
            raise UserError(_('Please define a hospitalization location from where the consumables will be taken.'))

        dest_location_id  = self.company_id.acs_hospitalization_usage_location_id.id
        source_location_id  = self.company_id.acs_hospitalization_stock_location_id.id
        return source_location_id, dest_location_id

    def consume_hopitalization_material(self):
        for rec in self:
            source_location_id, dest_location_id = rec.acs_get_consume_locations()
            for line in rec.consumable_line_ids.filtered(lambda s: not s.move_id):
                if line.product_id.is_kit_product:
                    move_ids = []
                    for kit_line in line.product_id.acs_kit_line_ids:
                        if kit_line.product_id.tracking!='none':
                            raise UserError("In Consumable lines Kit product with component having lot/serial tracking is not allowed. Please remove such kit product from consumable lines.")
                        move = self.consume_material(source_location_id, dest_location_id,
                            {'product': kit_line.product_id, 'qty': kit_line.product_qty * line.qty})
                        move.hospitalization_id = rec.id
                        move_ids.append(move.id)
                    #Set move_id on line also to avoid issue
                    line.move_id = move.id
                    line.move_ids = [(6,0,move_ids)]
                else:
                    move = self.consume_material(source_location_id, dest_location_id,
                        {'product': line.product_id, 'qty': line.qty, 'lot_id': line.lot_id and line.lot_id.id or False,})
                    move.hospitalization_id = rec.id
                    line.move_id = move.id

    def get_accommodation_invoice_data(self, invoice_id=False):
        product_data = []
        num_days = (self.discharge_date - self.hospitalization_date).days
        print(num_days,"####################$$$$$$$$$$$$$$$$$$")
        accommodation_history_ids = []
        for line in self.accommodation_history_ids:
            if line.invoiced_rest_time < line.rest_time:
                accommodation_history_ids += [line]

        if accommodation_history_ids:
            product_data.append({
                'name': _("Customer Accommodation Charges"),
            })
            for bed_history in accommodation_history_ids:
                product_data.append({
                    'product_id': bed_history.bed_id.product_id,
                    'name': bed_history.bed_id.name,
                    'quantity': num_days,
                    'accommodation_history_id': bed_history,
                    
                })
        return product_data

    def get_extra_accommodation_invoice_data(self, invoice_id=False):
        product_data = []
        num_days = (self.discharge_date - self.hospitalization_date).days
        accommodation_history_ids = []
        for line in self.accommodation_history_ids:
            if line.invoiced_rest_time < line.rest_time:
                accommodation_history_ids += [line]

        if accommodation_history_ids:
            product_data.append({
                'name': _("Extra Customer Accommodation Charges"),
            })
            for bed_history in accommodation_history_ids:
                product_data.append({
                    'product_id': bed_history.extra_bed_id.product_id,
                    'name': bed_history.extra_bed_id.name,
                    'quantity': num_days,
                    'price_unit': bed_history.extra_bed_id.product_id.list_price / 2,
                    'accommodation_history_id': bed_history,
                    
                })
        return product_data

    def get_consumable_invoice_data(self, invoice_id=False):
        product_data = []
        consumable_line_ids = self.consumable_line_ids.filtered(lambda s: not s.invoice_id)
        if consumable_line_ids:
            product_data.append({
                'name': _("Consumed Product Charges"),
            })
            for consumable in consumable_line_ids:
                product_data.append({
                    'product_id': consumable.product_id,
                    'quantity': consumable.qty,
                    'date': consumable.date,
                    'lot_id': consumable.lot_id and consumable.lot_id.id or False,
                    'product_uom_id': consumable.product_uom_id.id,
                })
                if invoice_id:
                    consumable.invoice_id = invoice_id.id

        return product_data

    def get_surgery_invoice_data(self, invoice_id=False):
        product_data = []

        surgery_ids = self.surgery_ids.filtered(lambda s: not s.invoice_id)
        if surgery_ids:
            surgery_data = surgery_ids.get_surgery_invoice_data()
            product_data += surgery_data

            if invoice_id:
                surgery_ids.invoice_id = invoice_id.id

        return product_data

    def acs_hospitalization_physician_round_data(self, invoice_id=False):
        product_data = []
        ward_rounds_to_invoice = self.physician_ward_round_ids.filtered(lambda s: not s.invoice_id)
        if ward_rounds_to_invoice:
            ward_data = {}
            for ward_round in ward_rounds_to_invoice:
                if ward_round.physician_id.ward_round_service_id:
                    if ward_round.physician_id.ward_round_service_id in ward_data:
                        ward_data[ward_round.physician_id.ward_round_service_id] += 1
                    else:
                        ward_data[ward_round.physician_id.ward_round_service_id] = 1
            if ward_data:
                product_data.append({
                    'name': _("Physician Ward Round Charges"),
                })
            for product in ward_data:
                product_data.append({
                    'product_id': product,
                    'quantity': ward_data[product],
                })

            if invoice_id:
                ward_rounds_to_invoice.invoice_id = invoice_id.id
        return product_data

    def acs_hospitalization_prescription_data(self, invoice_id=False):
        pres_data = []
        installed_acs_hms_pharmacy = self.env['ir.module.module'].sudo().search([('name','=','acs_hms_pharmacy'),('state','=','installed')])
        if installed_acs_hms_pharmacy:
            prescription_ids = self.mapped('prescription_ids').filtered(lambda req: req.state=='prescription' and req.deliverd and not req.invoice_id)
            if prescription_ids:
                pres_data.append({'name': _("IP Medicine Charges")})
                for record in prescription_ids:
                    for line in record.prescription_line_ids:
                        pres_data.append({
                            'product_id': line.product_id,
                            'quantity': line.quantity,
                        })
                    if invoice_id:
                        record.invoice_id = invoice_id.id
        return pres_data

    #In lab module it get implemented.
    def acs_hospitalization_lab_data(self, invoice_id=False):
        return []

    #In radio module it get implemented.
    def acs_hospitalization_radiology_data(self, invoice_id=False):
        return []

    #In nursing module it get implemented.
    def acs_hospitalization_nurse_round_data(self, invoice_id=False):
        return []

    #Keep Sub methods for projection flow. Because it just return list of data. Do not create real invoice.
    def acs_hospitalization_invoicing(self, invoice_id=False):
        #consumable Invoicing
        consumable_data = self.get_consumable_invoice_data(invoice_id)

        #accomodation Invoicing
        accommodation_data = self.get_accommodation_invoice_data(invoice_id)

        #Extra 
        extra_accommodation_data = self.get_extra_accommodation_invoice_data(invoice_id)

        #Physician Rounds Invoicing
        physician_round_data = self.acs_hospitalization_physician_round_data(invoice_id)

        #Nurse Round Invoicing
        nurse_round_data = self.acs_hospitalization_nurse_round_data(invoice_id)

        #surgey Invoicing
        surgery_data = self.get_surgery_invoice_data(invoice_id)
        
        #Pharmacy Invoicing
        pres_data = self.acs_hospitalization_prescription_data(invoice_id)

        #Lab Invoicing
        lab_data = self.acs_hospitalization_lab_data(invoice_id)

        #Radiology Invoicing
        radiology_data = self.acs_hospitalization_radiology_data(invoice_id)

        #Treatment Invoicing
        treatment_data = self.get_treatment_invoice_data(invoice_id)


        data = consumable_data + accommodation_data + extra_accommodation_data + nurse_round_data + surgery_data + pres_data + lab_data + radiology_data + treatment_data + physician_round_data
        #create Invoice lines only if invocie is passed
        if invoice_id:
            for line in data:
                pricelist_id = line.get('pricelist_id',False)
                inv_line = self.with_context(acs_pricelist_id=pricelist_id).acs_create_invoice_line(line, invoice_id)
                #ACS: As on accomodation history we need to set inv line as special case it is managed here.
                if line.get('accommodation_history_id'):
                    bed_history = line.get('accommodation_history_id')
                    bed_history.account_move_line_ids = [(6, 0, [inv_line.id] + bed_history.account_move_line_ids.ids)]

        return data

    def action_create_invoice(self):
        product_data = []
        inv_data = {
            'ref_physician_id': self.ref_physician_id and self.ref_physician_id.id or False,
            'physician_id': self.physician_id and self.physician_id.id or False,
            'hospital_invoice_type': 'hospitalization',
        }
        acs_context = {'commission_partner_ids':self.physician_id.partner_id.id}
        invoice_id = self.with_context(acs_context).acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data=inv_data)
        invoice_id.hospitalization_id = self.id

        self.acs_hospitalization_invoicing(invoice_id)

        message = _('Invoice Created.')
        user = self.env.user.sudo()
        return {
            'effect': {
                'fadeout': 'slow',
                'message': message,
                'img_url': '/web/image/%s/%s/image_1024' % (user._name, user.id) if user.image_1024 else '/web/static/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def button_indoor_medication(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_hms_prescription_order_view")
        action['domain'] = [('hospitalization_id', '=', self.id)]
        action['views'] = [(self.env.ref('acs_hms.view_hms_prescription_order_form').id, 'form')]
        action['context'] = {
            'default_patient_id': self.patient_id.id,
            'default_physician_id':self.physician_id.id,
            'default_hospitalization_id': self.id,
            'default_ward_id': self.ward_id.id,
            'default_bed_id': self.bed_id.id}
        return action

    def acs_invoice_forecast(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms_hospitalization.action_acs_hospitalization_forecast")
        action['domain'] = [('hospitalization_id', '=', self.id)]
        rec_id = self.env['acs.hospitalization.forecast'].create({
            'hospitalization_id': self.id,
        })
        rec_id.onchange_hospitalization()
        action['res_id'] = rec_id.id
        return action

    def get_treatment_invoice_data(self, invoice_id=False):
        treatments = self.env['acs.patient.procedure'].search([('patient_id','=',self.patient_id.id)])
        treatment_data = []
        
        # Update the condition based on your requirement
        filtered_treatments = treatments.filtered(lambda s: not s.invoice_id)

        if filtered_treatments:
            treatment_data.append({'name': _("Treatment Charges")})
            for record in filtered_treatments:
                treatment_data.append({
                    'product_id': record.product_id,
                    'date': record.date,
                    'price_unit': record.price_unit,
                })
                if invoice_id:
                    record.invoice_id = invoice_id.id
        return treatment_data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: