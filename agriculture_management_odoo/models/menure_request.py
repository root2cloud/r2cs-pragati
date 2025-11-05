from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class MenureRequest(models.Model):
    _name = "menure.request"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Menure Apply'
    _rec_name = 'ref'

    def _get_default_picking_type_id(self):
        domain = [('name', '=', "Internal Transfers")]
        picking_type = self.env['stock.picking.type'].search(domain, limit=1)
        if picking_type:
            return picking_type.id
        return False

    def _get_default_location_id(self):
        domain = [('name', '=', "Stock")]
        location = self.env['stock.location'].search(domain, limit=1)
        if location:
            return location.id
        return False

   

    ref = fields.Char(string='Reference', required=True, copy=False,
                      readonly=True, tracking=True,
                      default=lambda self: _('New'))
    
    request_date = fields.Date(string='Request Date',
                               default=fields.Date.context_today, required=True,
                               tracking=True)
    crop_id = fields.Many2one('crop.requests', string='Crop', required=True,store=True,
                              tracking=True)
    farmer_emp = fields.Many2one("res.partner", string="Farmer", related='location_dest_id.farmer_emp_id')
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        store=True, readonly=False,required=True,default=_get_default_location_id)
    location_dest_id = fields.Many2one(
        'stock.location', "Cost Center", store=True, readonly=False, required=True, compute='_compute_location_dest_id')
    state = fields.Selection([('draft','Draft'),('submit','Submitted')],string='Status', default='draft', tracking=True)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True, readonly=False, index=True,default=_get_default_picking_type_id)
    stock_change_menure = fields.Float(string="menure qty")
    cust_char = fields.Char("Customer name")
    product_id_menure = fields.Many2one(
        'product.product', 'Menure',required=True,domain=[('check_product_is_menure_pest', '=', 'menure')])
    note = fields.Text(string='Note', tracking=True)
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking ID')
    product_uom_id = fields.Many2one(
        'uom.uom', string="Unit of Measure",
        compute="_compute_product_uom_id", store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id_menure.uom_id.category_id')
    location_dest_id = fields.Many2one('stock.location', "Cost Center", store=True, readonly=False, required=True)
    zone_ids = fields.Many2many(
    'stock.location', 
    string="Zone area", 
    relation='crop_menure_zone_rel',  
    column1='menure_line_id', 
    column2='zone_id',
    # compute='_onchange_crop_menure_id',
    # readonly=False


    )

    beds_ids = fields.Many2many(
    'stock.location', 
    string="Beds",
    relation='crop_menure_beds_rel', 
    column1='menure_line_id', 
    column2='bed_id',
    # compute='_onchange_crop_menure_id',
    # readonly=False
   

    )
    uom_name = fields.Char(string='Uom name', related='product_id_menure.uom_name')
    menure_zone = fields.Char(string="menure zone")
    menure_bed = fields.Char(string="menure bed")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id,
        help='The default company for this user.', context={'user_preference': True})

    
    @api.depends('location_id')
    def _compute_location_dest_id(self):
        for record in self:
            if record.location_id:
                sublocations = self.env['stock.location'].search([('location_id', '=', record.location_id.id)])
                record.location_dest_id = sublocations and sublocations[0]  # Set the first sublocation as location_dest_id
            else:
                record.location_dest_id = False  # Clear the location_dest_id field if no location is selected

    @api.onchange('location_dest_id')
    def _onchange_location_dest_id(self):
        for record in self:
            if record.location_dest_id:
                crop_requests = self.env['crop.requests'].search([('location_dest_id', '=', record.location_dest_id.id)])
                return {'domain': {'crop_id': [('id', 'in', crop_requests.ids)]}}
            else:
                record.crop_id = False  # Clear the crop_id field

    @api.depends('product_id_menure')
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id_menure.uom_id

    @api.constrains('stock_change_menure')
    def _check_stock_change_menure(self):
        for record in self:
            if record.stock_change_menure <= 0:
                raise ValidationError("Please Update the Menure Quantity")

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if values.get('ref', _('New')) == _('New'):
                values['ref'] = self.env['ir.sequence'].next_by_code(
                'menure.request') or _('New')
                res = super(MenureRequest, self).create(values)
        return res

    # @api.onchange('crop_id')
    # def _onchange_crop_id(self):
    #     for record in self:
    #         if record.crop_id:
    #             if record.crop_id.state in ['draft','yeild','cancel']:
    #                 raise ValidationError(_("Unable to add Menure to this crop as it is in Draft/Yeild stage or it has been already Cancelled"))
    #             else:
    #                 location_dest_id = record.crop_id.location_dest_id.id
    #                 record.location_dest_id = location_dest_id
    #                 farmer_emp = record.crop_id.farmer_emp.id
    #                 record.farmer_emp = farmer_emp
    #                 record.zone_ids = record.crop_id.crop_plan_id.zone_ids.ids
    #                 record.beds_ids = record.crop_id.crop_plan_id.beds_ids.ids


    @api.onchange('crop_id')
    def _onchange_crop_menure_id(self):
        for record in self:
            if record.crop_id:
                if record.crop_id.state in ['draft','yeild','cancel']:
                    raise ValidationError(_("Unable to add Menure to this crop as it is in Draft/Yeild stage or it has been already Cancelled"))
                else:
                    location_dest_id = record.crop_id.location_dest_id.id
                    record.location_dest_id = location_dest_id
                    farmer_emp = record.crop_id.farmer_emp.id
                    record.farmer_emp = farmer_emp
                    zone_ids = record.crop_id.zone_ids.ids
                    record.zone_ids = [(6, 0, zone_ids)]
                    beds_ids = record.crop_id.beds_ids.ids
                    record.beds_ids = [(6, 0, beds_ids)]
                    # record.approve_menure()


    def action_draft(self):
        self.state = 'draft'

    def approve_menure(self):
        self.state = 'submit'

        # ******************
         
        for rec in self:
            for bed in rec.beds_ids:
                print("PFFFFFFFFFFFFFGGGGGGGGGGGGGGGGG",rec.beds_ids)
                if bed.location_confirm:
                    bed.menure_id = [(4, rec.id, 0)]
            
        # **************************

        if self.stock_picking_id:
            pass
            # raise ValidationError(_("The record already submitted, Please check Stock Picking ID"))

        else:
            picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'partner_id': self.farmer_emp.id,
            'scheduled_date': self.request_date,
            'origin': self.cust_char,
            'note': self.note,
            })
            self.crop_id.write({'menure_used_for_crop':self.stock_change_menure})
            self.crop_id.write({'menure_name_crop':self.product_id_menure.name})
            self.write({'stock_picking_id':picking.id})

            stock_move = self.env['stock.move'].create({
                'name': 'New Stock Move',
                'product_id': self.product_id_menure.id,
                'product_uom_qty': self.stock_change_menure,
                'product_uom': self.product_id_menure.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'picking_id': picking.id,
            })

            # Reserve the stock
            stock_move.write({
                'state': 'done',
                'move_line_ids': [(0, 0, {
                    'product_id': self.product_id_menure.id,
                    'product_uom_id': self.product_id_menure.uom_id.id,
                    'qty_done': self.stock_change_menure,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                })]
            })

