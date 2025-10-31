# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class PestRequests(models.Model):
    _name = 'pest.request'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Pest Apply'
    _rec_name = 'reference'

    def _get_default_picking_type_id(self):
        domain = [('name', '=', "Issued Quantity")]
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

    reference = fields.Char(string='Reference', required=True, copy=False,
                            readonly=True, tracking=True,
                            default=lambda self: _('New'))
    request_date = fields.Date(string='Request Date',
                               default=fields.Date.context_today, required=True,
                               tracking=True)
    crop_id = fields.Many2one('crop.requests', string='Crop', required=True,
                              tracking=True)
    disease = fields.Many2one('disease.details', string='Disease', tracking=True, required=True)
    note = fields.Text(string='Note', tracking=True)
    state = fields.Selection([('draft','Draft'),('submit','Submitted')],string='Status', default='draft', tracking=True)
    farmer_emp = fields.Many2one("res.partner", string="Farmer", related='location_dest_id.farmer_emp_id')
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        store=True, readonly=False,required=True,default=_get_default_location_id)
    location_dest_id = fields.Many2one(
        'stock.location', "Cost Center", store=True, readonly=False, required=True, compute='_compute_location_dest_id')
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
         readonly=False, index=True,default=_get_default_picking_type_id)
    stock_change_pest = fields.Float(string="Pest qty")
    cust_char = fields.Char("Customer name")
    product_id_pest = fields.Many2one(
        'product.product', 'Pest',required=True,domain=[('check_product_is_menure_pest', '=', 'pest')])
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking ID')
    product_uom_id = fields.Many2one(
        'uom.uom', string="Unit of Measure",
        compute="_compute_product_uom_id", store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id_pest.uom_id.category_id')
    zone_ids = fields.Many2many(
    'stock.location', 
    string="Zone area", 
    relation='crop_pest_zone_rel',  # Modify the relation name
    column1='pest_line_id', 
    column2='zone_id',
    # compute="_onchange_crop_pest_id",
    # readonly=False
    )

    beds_ids = fields.Many2many(
    'stock.location', 
    string="Beds",
    relation='crop_pest_beds_rel',  # Modify the relation name
    column1='pest_line_id', 
    column2='bed_id',
    # compute="_onchange_crop_pest_id",
    # readonly=False
    )
    uom_name = fields.Char(string='Uom name', related='product_id_pest.uom_name')
    pest_zone = fields.Char(string="pest zone")
    pest_bed = fields.Char(string="pest bed")
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

    @api.depends('product_id_pest')
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id_pest.uom_id


    # @api.onchange('crop_id')
    # def _onchange_crop_id(self):
    #     for record in self:
    #         if record.crop_id:
    #             if record.crop_id.state in ['draft','yeild','cancel']:
    #                 raise ValidationError(_("Unable to add pest to this crop as it is in Draft/Yeild stage or it has been already Cancelled"))
    #             else:
    #                 location_dest_id = record.crop_id.location_dest_id.id
    #                 record.location_dest_id = location_dest_id
    #                 farmer_emp = record.crop_id.farmer_emp.id
    #                 record.farmer_emp = farmer_emp
    #                 record.zone_ids = record.crop_id.crop_plan_id.zone_ids.ids
    #                 record.beds_ids = record.crop_id.crop_plan_id.beds_ids.ids


    @api.onchange('crop_id')
    def _onchange_crop_pest_id(self):
        for record in self:
            if record.crop_id:
                if record.crop_id.state in ['draft','yeild','cancel']:
                    raise ValidationError(_("Unable to add pest to this crop as it is in Draft/Yeild stage or it has been already Cancelled"))
                else:
                    location_dest_id = record.crop_id.location_dest_id.id
                    record.location_dest_id = location_dest_id
                    farmer_emp = record.crop_id.farmer_emp.id
                    record.farmer_emp = farmer_emp
                    record.zone_ids = record.crop_id.zone_ids.ids
                    record.beds_ids = record.crop_id.beds_ids.ids
                    # record.approve_pest()


    @api.constrains('stock_change_pest')
    def _check_stock_change_pest(self):
        for record in self:
            if record.stock_change_pest <= 0:
                raise ValidationError("Please Update the Menure Quantity")

    

    def action_draft(self):
        self.state = 'draft'

    def approve_pest(self):
        self.state = 'submit'
        # ************
        for rec in self:
            for bed in rec.beds_ids:
                if bed.location_confirm:
                    bed.pest_id = [(4, rec.id, 0)]
        # ***************

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
            self.crop_id.write({'pest_used_for_crop':self.stock_change_pest})
            self.crop_id.write({'pest_name_crop':self.product_id_pest.name})
            self.write({'stock_picking_id':picking.id})

            stock_move = self.env['stock.move'].create({
                'name': 'New Stock Move',
                'product_id': self.product_id_pest.id,
                'product_uom_qty': self.stock_change_pest,
                'product_uom': self.product_id_pest.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'picking_id': picking.id,
            })

            # Reserve the stock
            stock_move.write({
                'state': 'done',
                'move_line_ids': [(0, 0, {
                    'product_id': self.product_id_pest.id,
                    'product_uom_id': self.product_id_pest.uom_id.id,
                    'qty_done': self.stock_change_pest,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                })]
            })


    @api.model_create_multi
    def create(self, values_list): # !create is overrided by adding create_multi
        for values in values_list:

            if values.get('reference', _('New')) == _('New'):
                values['reference'] = self.env['ir.sequence'].next_by_code(
                'pest.request') or _('New')
                res = super(PestRequests, self).create(values)
        return res

