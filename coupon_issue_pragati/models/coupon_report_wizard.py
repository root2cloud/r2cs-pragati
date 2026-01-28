from odoo import models, fields, api
from odoo.exceptions import UserError


class CouponReportWizard(models.TransientModel):
    _name = 'coupon.report.wizard'
    _description = 'Coupon Report Wizard'

    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True, default=fields.Date.today())
    state = fields.Selection([
        ('all', 'All'),
        ('draft', 'Draft'),
        ('level1', 'Waiting Level 1'),
        ('level2', 'Waiting Level 2'),
        ('level3', 'Waiting Level 3'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Status", default='all')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from > record.date_to:
                raise UserError("From Date cannot be greater than To Date!")

    def action_generate_report(self):
        self.ensure_one()

        # Build domain based on filters
        domain = [
            ('issue_date', '>=', self.date_from),
            ('issue_date', '<=', self.date_to)
        ]

        if self.state != 'all':
            domain.append(('state', '=', self.state))

        coupons = self.env['coupon.issue'].search(domain)

        if not coupons:
            raise UserError("No coupons found for the selected criteria!")

        # Generate PDF report
        return self.env.ref('coupon_issue_pragati.action_coupon_report').report_action(coupons)