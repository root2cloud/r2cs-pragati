from odoo import models, fields, api, _


class PurchaseRequisitionCreateAlternative(models.TransientModel):
    _inherit = 'purchase.requisition.create.alternative'


    def _get_alternative_values(self):
        vals = super(PurchaseRequisitionCreateAlternative, self)._get_alternative_values()
        vals.update({
            'pr_request_id': self.origin_po_id.pr_request_id.ids,
        })
        return vals