# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class CropRequests(models.Model):
    '''Details to create Crop Requests'''
    _name = 'crop.requests'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Agriculture Management"
    _rec_name = 'ref'


    def _get_default_picking_type_id(self):
        domain = [('sequence_id', '=', "GFT - Production Store Sequence internal")]
        picking_type = self.env['stock.picking.type'].search(domain, limit=1)
        if picking_type:
            return picking_type.id
        return False

    def _get_default_location_id(self):
        domain = [('name', '=', "Gaddipati Family Trust")]
        location = self.env['stock.location'].search(domain, limit=1)
        if location:
            return location.id
        return False

    ref = fields.Char(string='Reference', required=True, copy=False,
                      readonly=True, tracking=True,
                      default=lambda self: _('New'))
    request_date = fields.Datetime(string='Sowing/Transplantation Date',
                               default=fields.Date.context_today, required=True,
                               tracking=True)
    harvest_date  = fields.Datetime(string='Harvest Date')
    end_date  = fields.Datetime(string='Crop end date')
    land_prepare_date  = fields.Datetime(string='Land Preparation Date')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'),
         ('growing', 'Growing'),
         ('harvest', 'Daily Harvest'),
         ('yeild','Yeild Completed'),
         ('cancel', 'Cancel')],
        string='Status', default='draft', tracking=True,
        group_expand='_group_expand_states')
    user_id = fields.Many2one('res.users', string='Responsible user',
                              default=lambda self: self.env.user)


    farmer_emp = fields.Many2one("res.partner", string="Farmer",required=True, related='location_dest_id.farmer_emp_id')
    location_id = fields.Many2one(
        'stock.location', "Source Location", default=_get_default_location_id,
        store=True, readonly=False,required=True,)
    location_dest_id = fields.Many2one(
        'stock.location', "Selection Area", store=True, readonly=False, required=True,)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True, readonly=False, index=True,default=_get_default_picking_type_id)
    stock_change = fields.Float(string="Seed qty",required=True)
    cust_char = fields.Char("Source Document")
    product_seed_id = fields.Many2one(
        'product.product', 'Seed Name',required=True,tracking=True,store=True,domain=[('categ_id.name', '=', 'Seeds & Seedlings')])
    product_id = fields.Many2one(
        'product.product', 'Crop Name',required=True,tracking=True,store=True)
    product_name = fields.Char(string='Product', related='product_id.name')
    note_reason = fields.Text(string='Reason of cancellation', tracking=True)
    crop_line_ids = fields.One2many('crop.request.line','crop_id',string='Crop lines')
    pest_used_for_crop = fields.Float(string='Pest Qty',store=True,readonly=True)
    pest_name_crop = fields.Char(string='Pest Used',store=True,readonly=True)
    menure_used_for_crop = fields.Float(string='Menure Qty',store=True,readonly=True)
    menure_name_crop = fields.Char(string='Menure Used',store=True,readonly=True)
    on_hand_qty = fields.Float(string='On Hand Quantity', compute='_compute_on_hand_qty',store=True)
    menure_line_ids = fields.One2many('menure.request','crop_id',string='Menure Lines')
    pest_line_ids = fields.One2many('pest.request','crop_id',string='Pest Lines')
    total_beds = fields.Integer(string="Total Beds")
    total_quantity = fields.Float(string="Total Quantity(Kgs)", compute='_compute_total_crop_quantity')
    crop_plan_id = fields.Many2one('crop.planning', string='Planning ID', domain=[('state','=','confirm')])
    zone_ids = fields.Many2many(
        'stock.location',
        string="Zone area",
        relation='crop_request_table_zone_rel',  # Modify the relation name
        column1='crop_req_id',  # Corrected column name
        column2='zone_id',
        domain="[('location_id', '=', location_dest_id)]"
    )
    beds_ids = fields.Many2many(
        'stock.location', 
        string="Beds",
        relation='crop_request_table_beds_rel',
        column1='crop_req_id', 
        column2='bed_id',
        domain="[('location_id', 'in', zone_ids),('location_confirm','=',False)]",
  
    )
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id,
        help='The default company for this user.', context={'user_preference': True})
    user_id = fields.Many2one('res.users', string='Responsible user',
                              default=lambda self: self.env.user)


    # def name_get(self):
    #     res = []
    #     for rec in self:
    #         res.append((rec.id, '[%s] - [%s]' % (rec.ref, rec.product_name)))
    #     return res

    def name_get(self):
        res = []
        for rec in self:
            name = '[%s] - [%s] - [%s]' % (rec.ref, rec.product_name, rec.state)
            res.append((rec.id, name))
        return res


    @api.onchange('crop_plan_id')
    def _onchange_crop_plan_id(self):
        for record in self:
            if record.crop_plan_id:
                record.product_seed_id = record.crop_plan_id.product_id.id
                record.request_date = record.crop_plan_id.sowing_date
                record.beds_ids = record.crop_plan_id.beds_ids.ids
                record.location_dest_id = record.crop_plan_id.select_area_id.id
                record.stock_change = record.crop_plan_id.no_seeds_required
                record.harvest_date = record.crop_plan_id.harvest_date
                record.end_date = record.crop_plan_id.crop_end_date
                record.land_prepare_date = record.crop_plan_id.land_prepare_date


    @api.depends('product_seed_id', 'location_id')
    def _compute_on_hand_qty(self):
        for record in self:
            if record.product_seed_id and record.location_id:
                product = record.product_seed_id
                location = record.location_id
                stock_quant = self.env['stock.quant'].search([
                    ('product_id', '=', product.id),
                    ('location_id', '=', location.id)
                ])
                on_hand_qty = sum(stock_quant.mapped('quantity'))
                record.on_hand_qty = on_hand_qty
            else:
                record.on_hand_qty = 0.0

    @api.depends('crop_line_ids.quantity')
    def _compute_total_crop_quantity(self):
        for order in self:
            order.total_quantity = sum(order.crop_line_ids.mapped('quantity'))



    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if values.get('ref', _('New')) == _('New'):
                values['ref'] = self.env['ir.sequence'].next_by_code(
                'crop.requests') or _('New')
                res = super(CropRequests, self).create(values)
        return res
    
    

    def action_draft(self):
        self.state = 'draft'

    def action_confirm(self):
        self.state = 'confirm'
        for rec in self:
            for bed in rec.beds_ids:
                print("dddddddddddddd",bed,bed.location_confirm)
                # if not bed.location_confirm:
                bed.write({'location_confirm': True, 'planning_id': self.id})


    def action_growing(self):
        self.state = 'growing'
        self.crop_plan_id.state = 'execute'

        picking = self.env['stock.picking'].create({
        'picking_type_id': self.picking_type_id.id,
        'location_id': self.location_id.id,
        'location_dest_id': self.location_dest_id.id,
        'partner_id': self.farmer_emp.id,
        'scheduled_date': self.request_date,
        'origin': self.cust_char,
        'note': self.note_reason,
        })

        stock_move = self.env['stock.move'].create({
            'name': 'New Stock Move',
            'product_id': self.product_seed_id.id,
            'product_uom_qty': self.stock_change,
            'product_uom': self.product_seed_id.uom_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'picking_id': picking.id,
        })

        # Reserve the stock
        stock_move.write({
            'state': 'done',
            'move_line_ids': [(0, 0, {
                'product_id': self.product_seed_id.id,
                'product_uom_id': self.product_seed_id.uom_id.id,
                'qty_done': self.stock_change,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })]
        })

    def action_harvest(self):
        self.state = 'harvest'


    def confirm_harvest(self):
        self.state = 'yeild'


    def action_cancel(self):
        # self.state = 'cancel'
        return {
            'name': _('Cancel Crop'),
            'view_mode': 'form',
            'res_model': 'cancel.crop.wizard',
            'view_id': self.env.ref('agriculture_management_odoo.cancel_crop_view_form').id,
            'type': 'ir.actions.act_window',
            # 'context': {'default_order_id': self.id},
            'target': 'new'
        }
        return self.action_cancel()
    
    def damage_crop_record(self):
        self.state="cancel"

    def _group_expand_states(self, states, domain, order):
        return [key for
                key, val in type(self).state.selection]


    @api.onchange('product_seed_id')
    def _onchange_product_seed_id(self):
        if self.product_seed_id:
            # Split the product_seed_id before the word 'Seeds'
            seed_name_parts = self.product_seed_id.name.split(' Seeds', 1)
            
            # Search for products that match the first part of the split seed name
            product_domain = [('name', 'ilike', seed_name_parts[0])]
            products = self.env['product.product'].search(product_domain, limit=1)
            
            if products:
                self.product_id = products[0].id
            else:
                self.product_id = False
        else:
            self.product_id = False




    

class CropRequestLine(models.Model):
    _name = 'crop.request.line'
    _description = 'Crop Request Line for Daily Harvesting'

    def _get_default_picking_type(self):
        domain = [('name', '=', "Receipts")]
        picking_type = self.env['stock.picking.type'].search(domain, limit=1)
        if picking_type:
            return picking_type.id
        return False

    crop_id = fields.Many2one('crop.requests',string='Crop ID')
    product_id = fields.Many2one(
        'product.product', 'Crop Name',required=True, domain="['|' ,('radio_field', '=', 'leafy'),('radio_field', '=', 'normal')]")
    product_name = fields.Char(string='ProductName', related='product_id.name', store=True)
    quantity = fields.Float(string='Quantity(Kgs)',required=True)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type', readonly=False, index=True,default=_get_default_picking_type)
    location_id = fields.Many2one('stock.location','Net House/ Open Area')
    location_dest_id = fields.Many2one(
        'stock.location', 
        string="WareHouse", 
        domain=[('usage', '=', 'internal'), ('replenish_location', '=', True)]
    )
    date = fields.Date(string='Date', default=fields.Date.context_today)
    farmer_emp = fields.Many2one("res.partner", string="Farmer")
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking ID')
    state = fields.Selection(string='Status',related='crop_id.state',store=True)
    product_uom_id = fields.Many2one(
        'uom.uom', string="Unit of Measure",
        compute="_compute_product_uom_id", store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    zone_ids = fields.Many2many(
    'stock.location', 
    string="Zone area", 
    relation='crop_request_zone_rel',  # Modify the relation name
    column1='request_line_id', 
    column2='zone_id',
    domain="[('location_id', '=', location_id)]",
    # compute="_onchange_crop_id",
    # readonly=False,
    )

    beds_ids = fields.Many2many(
    'stock.location', 
    string="Beds",
    relation='crop_request_beds_rel',  # Modify the relation name
    column1='request_line_id', 
    column2='bed_id',
    domain="[('location_id', 'in', zone_ids)]",
    # compute="_onchange_crop_id",
    # readonly=False,
    )
    state = fields.Selection([('draft','Draft'),('done','Done')], default='draft')
    harvest_zone = fields.Char(string="harvest zone")
    harvest_bed = fields.Char(string="harvest bed")
    harvest_crop_id = fields.Char(string="harvest crop id ",)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id,
        help='The default company for this user.', context={'user_preference': True})
    user_id = fields.Many2one('res.users', string='Responsible user',
                              default=lambda self: self.env.user)


    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '[%s] - [%s]' % (rec.product_id.name, rec.date)))
        return res

    # @api.onchange('location_id')
    # def _onchange_location_id(self):
    #     for record in self:
    #         if record.location_id:
    #             record.farmer_emp = record.location_id.farmer_emp_id.id
    #             crop_requests = self.env['crop.requests'].search([
    #                 ('location_dest_id', '=', record.location_id.id),
    #                 ('product_id', '=', record.product_id.id),
    #                 ('state', '=', 'harvest') 
    #             ])
    #             return {'domain': {'crop_id': [('id', 'in', crop_requests.ids)]}}
    #         else:
    #             record.crop_id = False  

    #  # ***************************changed this*******************************************

    @api.onchange('location_id','harvest_crop_id')
    def _onchange_location_id(self):
        for record in self:
            if record.location_id :
                print("PPPPPPPPPPPPPPPPPPPPPPPPPP###################",record.location_id,record.harvest_crop_id)
                record.farmer_emp = record.location_id.farmer_emp_id.id
                crop_requests = self.env['crop.requests'].search([
                    ('location_dest_id', '=', record.location_id.id),
                    ('product_id', '=', record.product_id.id),
                    ('state', '=', 'harvest')  
                ])
                print("lllllllllllllllllllllllllll",crop_requests,crop_requests.ids)
                return  {'domain':{'crop_id': [('id', 'in', crop_requests.ids)]}}
           
    # **********************************************************************

    




    @api.onchange('product_id', 'location_dest_id')
    def _onchange_fields(self):
        for record in self:
            domain = []
            if record.product_id:
                crop_requests = self.env['crop.requests'].search([('product_id', '=', record.product_id.id)])
                product_locations = crop_requests.mapped('location_dest_id')
                domain += [('id', 'in', product_locations.ids)]

            # if record.location_dest_id:
            #     # Fetch all child locations of the selected warehouse (location_dest_id)
            #     child_locations = self.env['stock.location'].search([('location_id', '=', record.location_dest_id.id)])
            #     # Add the child locations to the domain
            #     domain += [('id', 'in', child_locations.ids)]

            return {'domain': {'location_id': domain}}


    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id

    @api.constrains('date')
    def _check_date(self):
        for record in self:
            if record.date and record.date != date.today():
                raise ValidationError("Date should be today's date.")

    @api.constrains('quantity')
    def _check_crop_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError("Please Update the Crop Quantity")
    @api.model
    def default_get(self, fields):
        res = super(CropRequestLine, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        crop = self.env['crop.requests'].browse(active_id)
        res['crop_id'] = crop.id
        return res

    # @api.onchange('crop_id')
    # def _onchange_crop_id(self):
    #     for record in self:
    #         if record.crop_id and record.crop_id.crop_plan_id:
    #             record.zone_ids = record.crop_id.crop_plan_id.zone_ids.ids
    #             record.beds_ids = record.crop_id.crop_plan_id.beds_ids.ids
    #         else:
    #             record.zone_ids = [(5, 0, 0)]  # Clearing the Many2many field
    #             record.beds_ids = [(5, 0, 0)]  # Clearing the Many2many field
      # **************************************below*************************

    @api.onchange('crop_id')
    def _onchange_crop_id(self):
        for record in self:
            print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",record.crop_id)
            if record.crop_id :
                record.zone_ids = record.crop_id.zone_ids.ids
                record.beds_ids = record.crop_id.beds_ids.ids
                
            else:
                record.zone_ids = [(5, 0, 0)]  
                record.beds_ids = [(5, 0, 0)]  

    #     ******************************************changed*****************************



    def daily_harvest_button(self):

        if self.stock_picking_id:
            pass
            # raise ValidationError(_("The record already submitted, Please check Stock Picking ID"))

        else:
            picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'partner_id': self.farmer_emp.id,
            'scheduled_date': self.date,
            'origin': self.crop_id.ref,
            })

            self.write({'stock_picking_id':picking.id})

            stock_move = self.env['stock.move'].create({
                'name': 'New Stock Move',
                'product_id': self.product_id.id,
                'product_uom_qty': self.quantity,
                'product_uom': self.product_id.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'picking_id': picking.id,
            })

            # Reserve the stock
            stock_move.write({
                'state': 'done',
                'move_line_ids': [(0, 0, {
                    'product_id': self.product_id.id,
                    'product_uom_id': self.product_id.uom_id.id,
                    'qty_done': self.quantity,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                })]
            })
            self.state = 'done'


