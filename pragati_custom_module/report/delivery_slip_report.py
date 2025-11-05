from odoo import models

class DeliverySlipReport(models.AbstractModel):
    _inherit = 'report.stock.report_deliveryslip'

    def get_report_values(self, docids, data=None):
        report = super().get_report_values(docids, data)
        orders = self.env['stock.picking'].browse(docids)
        report.update({
            'orders': orders,
        })
        return report