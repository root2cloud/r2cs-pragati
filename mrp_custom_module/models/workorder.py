from odoo import models, fields

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'



    working_state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], string="Workcenter Status")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft')

    __last_update = fields.Datetime(string="Last Modified on")
    _barcode_scanned = fields.Char(string="Barcode Scanned")
    additional = fields.Boolean(string="Register additional product")
    allow_employee = fields.Boolean(string="Allow Employee")
    allow_producing_quantity_change = fields.Boolean(string="Allow Producing Quantity Change")
    allow_workorder_dependencies = fields.Boolean(string="Allow Work Order Dependencies")
    blocked_by_workorder_ids = fields.Many2many(
        'mrp.workorder', 'mrp_workorder_blocked_rel',
        'src_workorder_id', 'dest_workorder_id',
        string='Blocked By Work Orders'
    )

    check_ids = fields.One2many('mrp.check', 'workorder_id', string='Checks')  # Depends on 'mrp.check' model
    company_id = fields.Many2one(related='production_id.company_id', string='Company')
    consumption = fields.Selection(related='production_id.consumption', string='Consumption')
    costs_hour = fields.Float(string='Cost per hour', default=0.0, group_operator="avg")
    create_date = fields.Datetime(string="Created on")
    create_uid = fields.Many2one('res.users', string="Created by")

    # current_quality_check_id = fields.Many2one('quality.check', string="Current Quality Check", check_company=True)
    date_finished = fields.Datetime(string="End Date")
    date_planned_finished = fields.Datetime(string='Scheduled End Date')
    date_planned_start = fields.Datetime(string='Scheduled Start Date')
    date_start = fields.Datetime(string="Start Date")
    display_name = fields.Char(string="Display Name")
    duration = fields.Float(string="Real Duration")
    duration_expected = fields.Float(string="Expected Duration")
    duration_percent = fields.Integer(string="Duration Deviation (%)")
    duration_unit = fields.Float(string="Duration Per Unit")

    employee_analytic_account_line_ids = fields.Many2many(
        'account.analytic.line', string="Employee Analytic Account Line"
    )
    employee_id = fields.Many2one('hr.employee', string="Employee")
    employee_ids = fields.Many2many('hr.employee', string="Employees")
    employee_name = fields.Char(string="Employee Name")
    finished_lot_id = fields.Many2one('stock.lot', string="Lot/Serial Number")

    # finished_product_check_ids = fields.Many2many(
    #     'quality.check', 'mrp_workorder_finished_product_check_rel',
    #     'workorder_id', 'check_id', string="Finished Product Check"
    # )

    is_first_started_wo = fields.Boolean(string="Is The first Work Order")
    is_last_lot = fields.Boolean(string="Is Last Lot")
    is_last_unfinished_wo = fields.Boolean(string="Is Last Unfinished Workorder")
    is_planned = fields.Boolean(related='production_id.is_planned', string="Its Operations are Planned")
    is_produced = fields.Boolean(string="Has Been Produced")
    is_user_working = fields.Boolean(string="Is the Current User Working")
    json_popover = fields.Char(string="Popover Data JSON")

    last_working_user_id = fields.Many2many(
        'res.users', 'mrp_workorder_last_users_rel', 'workorder_id', 'user_id',
        string="Last Users"
    )
    leave_id = fields.Many2one('resource.calendar.leaves', string="Leave")
    lot_id = fields.Many2one('stock.lot', string="Lot/Serial")
    mo_analytic_account_line_id = fields.Many2one('account.analytic.line', string="Mo Analytic Account Line")
    move_finished_ids = fields.One2many('stock.move', 'workorder_id', string="Finished Moves")
    move_id = fields.Many2one('stock.move', string="Stock Move")
    move_line_id = fields.Many2one('stock.move.line', string="Stock Move Line")
    move_line_ids = fields.One2many('stock.move.line', 'workorder_id', string="Moves to Track")
    move_raw_ids = fields.One2many('stock.move', 'workorder_id', string="Raw Moves")
    name = fields.Char(string="Work Order")
    needed_by_workorder_ids = fields.Many2many(
        'mrp.workorder', 'mrp_workorder_needed_rel',
        'src_workorder_id', 'dest_workorder_id',
        string='Needed By Work Orders'
    )
    # priority = fields.Selection([
    #     ('0', 'Normal'),
    #     ('1', 'Important'),
    #     ('2', 'Urgent'),
    # ], string='Priority', default='0')
    operation_id = fields.Many2one('mrp.routing.workcenter', string="Operation")
    operation_note = fields.Html(string="Description")
    picture = fields.Binary(string="Picture")
    priority = fields.Selection([('0', 'Normal'), ('1', 'High')], string="Priority")
    product_id = fields.Many2one('product.product', string="Product")
    product_tracking = fields.Selection(related="product_id.tracking", string="Tracking")
    product_uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    production_availability = fields.Selection(
        string='Stock Availability',
        related='production_id.reservation_state'
    )
    production_bom_id = fields.Many2one('mrp.bom', string="Bill of Material")
    production_date = fields.Datetime(string="Production Date")
    production_id = fields.Many2one('mrp.production', string="Manufacturing Order")
    production_state = fields.Selection(string="Production State", related='production_id.state')
    progress = fields.Float(string="Progress Done (%)")
    qty_done = fields.Float(string="Done")
    qty_produced = fields.Float(string="Quantity")
    qty_producing = fields.Float(string="Currently Produced Quantity")
    qty_production = fields.Float(string="Original Production Quantity")
    qty_remaining = fields.Float(string="Quantity To Be Produced")
    qty_reported_from_previous_wo = fields.Float(string="Carried Quantity")
    quality_alert_count = fields.Integer(string="Quality Alert Count")

    # quality_alert_ids = fields.One2many('quality.alert', 'workorder_id', string="Quality Alert")
    quality_check_fail = fields.Boolean(string="Quality Check Fail")
    quality_check_todo = fields.Boolean(string="Quality Check Todo")
    quality_point_count = fields.Integer(string="Steps")

    # quality_point_ids = fields.Many2many(
    #     'quality.point', 'mrp_workorder_quality_point_rel',
    #     'workorder_id', 'point_id', string="Quality Point"
    # )
    # quality_state = fields.Char(string="Quality state")
    scrap_count = fields.Integer(string="Scrap Move")
    scrap_ids = fields.One2many('stock.scrap', 'workorder_id', string="Scrap")
    show_json_popover = fields.Boolean(string="Show Popover?")
    test_type = fields.Char(string="Technical name")

    # test_type_id = fields.Many2one('quality.test', string="Test Type")
    time_ids = fields.One2many('mrp.workcenter.productivity', 'workorder_id', string="Time")
    user_id = fields.Many2one('res.users', string="Responsible")
    wc_analytic_account_line_id = fields.Many2one('account.analytic.line', string="Wc Analytic Account Line")
    workcenter_id = fields.Many2one('mrp.workcenter', string="Work Center")
    working_user_ids = fields.Many2many(
        'res.users', 'mrp_workorder_working_users_rel',
        'workorder_id', 'user_id', string='Working Users'
    )
    worksheet = fields.Binary(string="Worksheet")
    worksheet_google_slide = fields.Char(string="Worksheet URL")
    worksheet_page = fields.Text(string="Worksheet Page")
    worksheet_type = fields.Selection([
        ('pdf', 'PDF'),
        ('url', 'Google Slide URL'),
        ('text', 'Text')
    ], string="Worksheet Type", default='pdf')
    write_date = fields.Datetime(string="Last Updated on")
    write_uid = fields.Many2one('res.users', string="Last Updated by")
    quality_state = fields.Selection(
        [
            ('none', 'None'),
            ('pass', 'Passed'),
            ('fail', 'Failed')
        ],
        string='Quality State',
        default='none'
    )


