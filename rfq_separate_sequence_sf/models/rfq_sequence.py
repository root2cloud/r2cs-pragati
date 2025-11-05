# -*- coding: utf-8 -*-
##############################################################################
#
#    Shinefy Technologies Pvt. Ltd.
#    Copyright (C) 2022 Shinefy Technologies.
#    Author: Shinefy Technologies
#    
#    For Module Support : shinefytech@gmail.com  or Skype : shinefytech@gmail.com
#
##############################################################################
from datetime import datetime
from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    

    sequence_name = fields.Char(string="Sequence", default='New')
    state = fields.Selection(selection_add=[('draft', 'RFQ / Draft PO'),('sent',)])
    select_req = fields.Selection([('rfq','RFQ'),('po', 'PO')], string="Choose RFQ/PO", default='rfq')
    select_req_bool = fields.Boolean(string="Select Req Bool", compute="_onchange_select_req" ,readonly=False)


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New') and vals.get('select_req') == 'rfq':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.rfq') or '/'
            vals['sequence_name'] = vals['name']

            fiscal_years = self.env['account.fiscal.year'].search([])

            if fiscal_years:
                for fiscal_year in fiscal_years:
                    start_date = fiscal_year.date_from
                    end_date = fiscal_year.date_to
                
                    if start_date <= datetime.now().date() <= end_date:
                        
                        if '/' not in vals['name']:
                            date_part = datetime.today().strftime('%Y/%m') 
                            series_number = vals['name'].split('/')[-1].lstrip('RFQ') 
                            year_range = "{}-{}".format(start_date.strftime('%y'), end_date.strftime('%y'))
                            vals['name'] = "RFQ/{}/{}".format(year_range, series_number.zfill(4))
                        break
                    
                        
            elif not fiscal_years:  
                series_number = vals['name'].split('/')[-1].lstrip('RFQ')
                date_part = datetime.today().strftime('%Y/%m')  
                vals['name'] = "RFQ/{}/{}".format(date_part,series_number.zfill(4))

            elif fiscal_years :
                for fiscal_year in fiscal_years:
                    start_date = fiscal_year.date_from
                    end_date = fiscal_year.date_to
                
                    
                    if not start_date <= datetime.now().date() <= end_date:
                        series_number = vals['name'].split('/')[-1].lstrip('RFQ')
                        date_part = datetime.today().strftime('%Y/%m')  
                        vals['name'] = "RFQ/{}/{}".format(date_part,series_number.zfill(4))



        elif vals.get('name', _('New')) == _('New') and vals.get('select_req') == 'po':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
            vals['sequence_name'] = vals['name']
            fiscal_years = self.env['account.fiscal.year'].search([])
            if fiscal_years:
                for fiscal_year in fiscal_years:
                    start_date = fiscal_year.date_from
                    end_date = fiscal_year.date_to
                    if start_date <= datetime.now().date() <= end_date:
                        if '/' not in vals['name']:
                            date_part = datetime.today().strftime('%Y/%m') 
                            series_number = vals['name'].split('/')[-1].lstrip('P')  # Extract the series number from the name
                            year_range = "{}-{}".format(start_date.strftime('%y'), end_date.strftime('%y'))
                            vals['name'] = "PO/{}/{}".format(year_range, series_number.zfill(4))  # Pad series number with leading zeros
     
                        break

                        
            elif not fiscal_years: 
                series_number = vals['name'].split('/')[-1].lstrip('P')
                date_part = datetime.today().strftime('%Y/%m')  
                vals['name'] = "PO/{}/{}".format(date_part,series_number.zfill(4))

            elif fiscal_years :
                for fiscal_year in fiscal_years:
                    start_date = fiscal_year.date_from
                    end_date = fiscal_year.date_to
                    if not start_date <= datetime.now().date() <= end_date:
                        series_number = vals['name'].split('/')[-1].lstrip('RFQ')
                        date_part = datetime.today().strftime('%Y/%m')  
                        vals['name'] = "PO/{}/{}".format(date_part,series_number.zfill(4))

        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.rfq') or '/'
            vals['sequence_name'] = vals['name']

            fiscal_years = self.env['account.fiscal.year'].search([])

            if fiscal_years:
                for fiscal_year in fiscal_years:
                    start_date = fiscal_year.date_from
                    end_date = fiscal_year.date_to
                
                    if start_date <= datetime.now().date() <= end_date:
                        
                        if '/' not in vals['name']:
                            date_part = datetime.today().strftime('%Y/%m') 
                            series_number = vals['name'].split('/')[-1].lstrip('RFQ') 
                            year_range = "{}-{}".format(start_date.strftime('%y'), end_date.strftime('%y'))
                            vals['name'] = "RFQ/{}/{}".format(year_range, series_number.zfill(4))
                        break
                    
                        
            elif not fiscal_years:  
                series_number = vals['name'].split('/')[-1].lstrip('RFQ')
                date_part = datetime.today().strftime('%Y/%m')  
                vals['name'] = "RFQ/{}/{}".format(date_part,series_number.zfill(4))

            elif fiscal_years :
                for fiscal_year in fiscal_years:
                    start_date = fiscal_year.date_from
                    end_date = fiscal_year.date_to
                
                    
                    if not start_date <= datetime.now().date() <= end_date:
                        series_number = vals['name'].split('/')[-1].lstrip('RFQ')
                        date_part = datetime.today().strftime('%Y/%m')  
                        vals['name'] = "RFQ/{}/{}".format(date_part,series_number.zfill(4))




        record = super(PurchaseOrder, self).create(vals)
        
        return record
    


    def button_confirm(self):
        for order in self:
            # Call the super method to perform the default confirmation actions
            if not order.name or not order.name.startswith('PO/'):
                fiscal_years = self.env['account.fiscal.year'].search([])
                if fiscal_years:
                    for fiscal_year in fiscal_years:
                        start_date = fiscal_year.date_from
                        end_date = fiscal_year.date_to
                        if start_date <= datetime.now().date() <= end_date:
                            sequence = self.env['ir.sequence'].next_by_code('purchase.order') or _('New')
                            sequence_number = sequence[2:] if sequence.startswith("P0") else sequence[1:]
                            year_range = "{}-{}".format(start_date.strftime('%y'), end_date.strftime('%y'))
                            order.name = "PO/{}/{}".format(year_range,sequence_number.zfill(4))
                       
                        
                            
                elif not fiscal_years:  
                    sequence = self.env['ir.sequence'].next_by_code('purchase.order') or _('New')
                    sequence_number = sequence[2:] if sequence.startswith("P0") else sequence[2:]
                    date_part = datetime.today().strftime('%Y/%m')  
                    order.name = "PO/{}/{}".format(date_part,sequence_number.zfill(4))

                elif fiscal_years :
                    for fiscal_year in fiscal_years:
                        start_date = fiscal_year.date_from
                        end_date = fiscal_year.date_to
                    
                        if not start_date <= datetime.now().date() <= end_date:                            
                            sequence = self.env['ir.sequence'].next_by_code('purchase.order') or _('New')
                            sequence_number = sequence[2:] if sequence.startswith("P0") else sequence[2:]

                            date_part = datetime.today().strftime('%Y/%m')  
                            order.name = "PO/{}/{}".format(date_part,sequence_number.zfill(4))


     

        res = super(PurchaseOrder, order).button_confirm()
        return res

    @api.depends('select_req')
    def _onchange_select_req(self):
        for rec in self:
            if rec.select_req == 'rfq':
                rec.select_req_bool = True

            elif rec.select_req == 'po':
                rec.select_req_bool = False
