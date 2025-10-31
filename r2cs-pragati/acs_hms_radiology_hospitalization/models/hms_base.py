# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Hospitalization(models.Model):
    _inherit = "acs.hospitalization"

    def _rec_count(self):
        rec = super(Hospitalization, self)._rec_count()
        for rec in self:
            rec.radiology_request_count = len(rec.radiology_request_ids)
            rec.radiology_test_count = len(rec.radiology_test_ids)

    radiology_test_ids = fields.One2many('patient.radiology.test', 'hospitalization_id', string='Radiology Tests')
    radiology_request_ids = fields.One2many('acs.radiology.request', 'hospitalization_id', string='Radiology Requests')
    radiology_request_count = fields.Integer(compute='_rec_count', string='# Radiology Requests')
    radiology_test_count = fields.Integer(compute='_rec_count', string='#Radiology Radiology Tests')

    def action_radiology_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_radiology.hms_action_radiology_request")
        action['domain'] = [('id','in',self.radiology_request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id}
        action['views'] = [(self.env.ref('acs_radiology.patient_radiology_test_request_form').id, 'form')]
        return action

    def action_view_radiology_requests(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_radiology.hms_action_radiology_request")
        action['domain'] = [('id','in',self.radiology_request_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id}
        return action

    def action_view_radiology_test_results(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_radiology.action_radiology_result")
        action['domain'] = [('id','in',self.radiology_test_ids.ids)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_hospitalization_id': self.id}
        return action

    def acs_hospitalization_radiology_data(self, invoice_id=False):
        radiology_data = []
        request_ids = self.mapped('radiology_request_ids').filtered(lambda req: req.state=='to_invoice' and not req.invoice_id)
        if request_ids:
            radiology_data.append({'name': _("Radiology Charges")})
            for record in request_ids:
                pricelist_id = record.pricelist_id and record.pricelist_id.id or False
                for line in record.line_ids:
                    radiology_data.append({
                        'product_id': line.test_id.product_id,
                        'price_unit': line.sale_price,
                        'quantity': line.quantity,
                        'pricelist_id': pricelist_id,
                    })
                if invoice_id:
                    record.invoice_id = invoice_id.id
                    #ACS: it is possible that on hospitalization done we can mark record as done or we can do it on invoice validation also.
                    record.button_done()
        return radiology_data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
