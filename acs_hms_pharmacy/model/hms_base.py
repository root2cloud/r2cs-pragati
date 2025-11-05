# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PrescriptionLine(models.Model):
    _inherit = 'prescription.line'

    @api.depends('quantity', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        """
        Compute the amounts of the line.
        """
        for line in self:
            if not line.display_type:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, line.quantity, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
            else:
                line.price_tax = 0
                line.price_total = 0
                line.price_subtotal = 0

    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)
    price_unit = fields.Float(string='Unit Price', store=True)
    discount = fields.Float('% Discount')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes Amount', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    currency_id = fields.Many2one(related='prescription_id.company_id.currency_id', store=True, string='Currency', readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    move_id = fields.Many2one('stock.move', 'Stock Move', readonly=True)
    move_ids = fields.Many2many('stock.move', 'prescription_line_stock_move_rel', 'move_id', 'prescription_line_id', 'Kit Stock Moves', readonly=True)

    @api.onchange('product_id','dosage_uom_id')
    def onchange_product_uom(self):
        self.price_unit = self.product_id._get_tax_included_unit_price(
            self.prescription_id.company_id,
            self.prescription_id.currency_id,
            self.prescription_id.prescription_date,
            'sale',
            product_uom=self.dosage_uom_id or ''
        )

class Prescription(models.Model):
    _inherit = 'prescription.order'

    @api.depends('picking_ids')
    def _compute_delivery(self):
        for rec in self:
            rec.deliverd = True if len(rec.picking_ids) else False

    @api.model
    def _get_default_warehouse(self):
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        return warehouse_id

    def get_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.sudo().picking_ids)

    @api.depends('prescription_line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the order.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.prescription_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.company_id.currency_id.round(amount_untaxed),
                'amount_tax': order.company_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False, groups="account.group_account_invoice")
    picking_ids = fields.One2many('stock.picking', 'prescription_id', 'Pickings', groups="stock.group_stock_user")
    picking_count = fields.Integer(compute="get_picking_count", string='#Pickings', groups="stock.group_stock_user")
    deliverd = fields.Boolean(compute='_compute_delivery', store=True, groups="stock.group_stock_user")
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', default=_get_default_warehouse, groups="stock.group_stock_user")
    currency_id = fields.Many2one("res.currency", related='company_id.currency_id', string="Currency", readonly=True, required=True)
    invoice_ids = fields.One2many("account.move", "prescription_id", string="Invoices", groups="account.group_account_invoice")

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=True, currency_field="currency_id")
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all', currency_field="currency_id")
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', tracking=True, currency_field="currency_id")

    def get_prescription_invoice_data(self):
        product_data = [{
            'name': _("Medicine Charges"),
        }]
        for rec in self:
            for line in rec.prescription_line_ids:
                product_data.append({
                    'product_id': line.product_id,
                    'quantity': line.quantity,
                    'name': line.name,
                    'display_type': line.display_type,
                    'product_uom_id': line.dosage_uom_id.id,
                })
        return product_data

    def create_invoice(self):
        if not self.prescription_line_ids:
            raise UserError(_("Please add prescription lines first."))
        product_data = self.get_prescription_invoice_data()
        
        inv_data = {
            'physician_id': self.physician_id and self.physician_id.id or False,
            'hospital_invoice_type': 'pharmacy',
        }
        acs_context = {'commission_partner_ids':self.physician_id.partner_id.id}
        invoice = self.with_context(acs_context).acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data=inv_data)
        invoice.write({
            'create_stock_moves': False if self.deliverd else True,
            'prescription_id': self.id,
        })
        invoice.onchange_warehouse()
        invoice.onchange_picking_type()

        self.sudo().invoice_id = invoice.id

        #Chekc if insurace module is installed.
        installed_acs_hms_insurance = self.env['ir.module.module'].sudo().search([('name','=','acs_hms_insurance'),('state','=','installed')])
        if installed_acs_hms_insurance:
            if self.invoice_id and self.insurance_id and (self.insurance_id.pha_insurance_limit >= self.invoice_id.amount_total or self.insurance_id.pha_insurance_limit==0):
                insurace_invoice = self.invoice_id.acs_create_insurace_invoice(self.insurance_id, self.insurance_id.pha_insurance_type, 
                    self.insurance_id.pha_insurance_amount, self.insurance_id.pha_insurance_percentage, 
                    self, 'pharmacy', 'prescription_id', self.insurance_id.pha_create_claim)
                if insurace_invoice and insurace_invoice.claim_id:
                    self.claim_id = insurace_invoice.claim_id.id

    def view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.acs_action_view_invoice(invoices)
        return action

    def acs_get_consume_locations(self):
        location_id = self.warehouse_id.lot_stock_id
        location_dest_id = self.patient_id.partner_id.property_stock_customer
        return location_id, location_dest_id

    def acs_create_delivery(self):
        StockMove = self.env['stock.move']
        picking_type_id = self.warehouse_id.out_type_id
        location_id, location_dest_id = self.acs_get_consume_locations()
        picking = self.env['stock.picking'].create({
            'partner_id': self.patient_id.partner_id.id,
            'patient_id': self.patient_id.id,
            'prescription_id': self.id,
            'date': fields.datetime.now(), 
            'company_id': self.company_id.id,
            'picking_type_id': picking_type_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'move_type': 'direct',
            'origin': self.name,
        })

        for line in self.prescription_line_ids:
            if line.product_id and line.product_id.type!='service':
                if line.product_id.is_kit_product:
                    move_ids = []
                    for kit_line in line.product_id.acs_kit_line_ids:
                        if kit_line.product_id.type!='service':
                            move = StockMove.create({
                                'product_id': kit_line.product_id.id,
                                'product_uom_qty': kit_line.product_qty,
                                'product_uom': kit_line.product_id.uom_id.id,
                                'date': fields.datetime.now(),
                                'picking_id': picking.id,
                                'picking_type_id': picking.picking_type_id.id,
                                'state': 'draft',
                                'name': kit_line.product_id.name,
                                'location_id': location_id.id,
                                'location_dest_id': location_dest_id.id,
                            })
                            line.move_id = move.id
                            move_ids.append(move.id)
                    line.move_ids = [(6,0,move_ids)]
                else:
                    move = StockMove.create({
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.quantity,
                        'product_uom': line.product_id.uom_id.id,
                        'date': fields.datetime.now(),
                        'picking_id': picking.id,
                        'picking_type_id': picking.picking_type_id.id,
                        'state': 'draft',
                        'name': line.product_id.name,
                        'location_id': location_id.id,
                        'location_dest_id': location_dest_id.id,
                    })
                    line.move_id = move.id
                    line.move_ids = [(6,0,[move.id])]
        return self.acs_view_delivery()

    def acs_view_delivery(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_ready")
        action['domain'] = [('prescription_id', '=', self.id)]
        if len(self.picking_ids) == 1:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = self.picking_ids[0].id
        return action
    
    #method to create get invoice data and set passed invoice id.
    def acs_common_invoice_prescription_data(self, invoice_id=False):
        data = []
        if self.ids:
            data = self.get_prescription_invoice_data()
            if invoice_id:
                self.invoice_id = invoice_id.id
        return data


class AccountMove(models.Model):
    _inherit = "account.move"

    prescription_id = fields.Many2one('prescription.order',  string='Prescription')

    #ACS: Stock move is not linked with related prescription line becase line is not even linked with invoice
    @api.model 
    def move_line_from_invoice_lines(self, picking, location_id, location_dest_id):
        StockMoveL = self.env['stock.move.line']
        for line in self.invoice_line_ids:
            if line.product_id and line.product_id.type!='service':
                if line.product_id.is_kit_product:
                    for kit_line in line.product_id.acs_kit_line_ids:
                        if kit_line.product_id.type!='service':

                            StockMoveL.with_context(default_immediate_transfer=True).create({
                                'product_id': kit_line.product_id.id,
                                'product_uom_id': kit_line.product_id.uom_id.id,
                                'date': fields.datetime.now(),                    
                                'picking_id': picking.id,
                                'picking_type_id': picking.picking_type_id.id,
                                'state': 'assigned',
                                'location_id': location_id.id,
                                'location_dest_id': location_dest_id.id,
                                'acs_account_move_line_id': line.id, 
                                'qty_done': kit_line.product_qty,
                                'company_id': picking.company_id.id,
                                'package_level_id': False,
                            })
                else:
                    StockMoveL.with_context(default_immediate_transfer=True).create({
                        'product_id': line.product_id.id,
                        #'product_uom_qty': line.quantity,
                        'product_uom_id': line.product_uom_id.id,
                        'date': fields.datetime.now(),                    
                        'picking_id': picking.id,
                        'picking_type_id': picking.picking_type_id.id,
                        'state': 'assigned',
                        'location_id': location_id.id,
                        'location_dest_id': location_dest_id.id,
                        'lot_id': line.acs_lot_id and line.acs_lot_id.id or False, 
                        'lot_name': line.acs_lot_id and line.acs_lot_id.name or '', 
                        'acs_account_move_line_id': line.id, 
                        'qty_done': line.quantity,
                        'company_id': picking.company_id.id,
                        'package_level_id': False,
                    })


class StockPicking(models.Model):
    _inherit = "stock.picking"

    prescription_id = fields.Many2one('prescription.order',  string='Prescription')
    patient_id = fields.Many2one('hms.patient', string='Patient')


class HmsAppointment(models.Model):
    _inherit = "hms.appointment"

    #Method to collect common invoice related records data
    def acs_appointment_common_data(self, invoice_id):
        data = super().acs_appointment_common_data(invoice_id)
        prescription_ids = self.mapped('prescription_ids').filtered(lambda req: req.state=='prescription' and req.deliverd and not req.invoice_id)
        data += prescription_ids.acs_common_invoice_prescription_data(invoice_id)
        return data
