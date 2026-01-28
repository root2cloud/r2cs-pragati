from odoo import models, fields, api
from odoo.tools import date_utils
from datetime import datetime, date


class CouponReport(models.AbstractModel):
    _name = 'report.coupon_issue_pragati.coupon_report_template'
    _description = 'Coupon Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['coupon.issue'].browse(docids)

        # Calculate statistics
        total_issued = len(docs)
        total_redeemed = 0
        total_value = 0

        for doc in docs:
            total_value += doc.coupon_value or 0
            # Check if coupon is redeemed
            redeem = self.env['coupon.redeem'].search([
                ('coupon_issue_id', '=', doc.id),
                ('state', '=', 'redeemed')
            ], limit=1)
            if redeem:
                total_redeemed += 1

        return {
            'doc_ids': docids,
            'doc_model': 'coupon.issue',
            'docs': docs,
            'total_issued': total_issued,
            'total_redeemed': total_redeemed,
            'total_value': total_value,
            'current_date': fields.Date.today(),
        }