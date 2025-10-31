from odoo import models, fields, api
from datetime import datetime

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    # Fields
    po_delay_days = fields.Integer(string="PO Delay (Days)", compute="_compute_gap_days")
    mrn_delay_days = fields.Integer(
        string="MRN Delay Days", compute="_compute_mrn_days", store=True
    )

    is_used = fields.Boolean(string="Used in PO", default=False)
    pr_confirmation = fields.Boolean(string='PR Confirmed', default=False)

    delay_days = fields.Integer(string="Delay_days")



    # Compute PO Delay Days
    @api.depends("order_date", "po_dates")
    def _compute_gap_days(self):
        for record in self:
            if record.order_date and record.po_dates:
                delta_days = (record.order_date - record.po_dates).days
                record.po_delay_days = abs(delta_days)
            else:
                record.po_delay_days = 0

    @api.depends("expect_arrival", "mrn_dates")
    def _compute_mrn_days(self):
        for record in self:
            if record.expect_arrival and record.mrn_dates:
                # Ensure dates are in the correct format (date objects)
                expect_arrival_date = record.expect_arrival.date() if isinstance(record.expect_arrival,
                                                                                 datetime) else record.expect_arrival
                mrn_date = record.mrn_dates

                if isinstance(mrn_date, datetime):
                    mrn_date = mrn_date.date()  # Convert to date if it's a datetime object

                # Calculate the difference in days
                delta_days = (expect_arrival_date - mrn_date).days
                record.mrn_delay_days = abs(delta_days)
            else:
                record.mrn_delay_days = 0
    #
    # # Compute MRN Delay Days
