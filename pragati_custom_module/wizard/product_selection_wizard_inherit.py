from odoo import models, api

class ProductSelectionWizardInherit(models.TransientModel):
    _inherit = 'product.selection.wizard'

    @api.model
    def default_get(self, fields):
        res = super(ProductSelectionWizardInherit, self).default_get(fields)
        if not res.get('purchase_order_id'):
            return res

        po = self.env['purchase.order'].browse(res['purchase_order_id'])
        wizard_lines = []

        for pr_line in po.pr_request_ids.mapped('pr_request_line_ids'):
            # Skip lines already used in a PO
            if pr_line.is_selected_in_po:
                continue

            wizard_lines.append((0, 0, {
                'name': pr_line.product_id.name,
                'product_id': pr_line.product_id.id,
                'product_uom': pr_line.product_uom_id.id,
                'quantity': pr_line.quantity,
            }))

        res['product_wizard_line_ids'] = wizard_lines
        return res

    def button_submit(self):
        selected_lines = self.product_wizard_line_ids.filtered('select_record')
        po = self.purchase_order_id
        order_lines = []

        for line in selected_lines:
            order_lines.append((0, 0, {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_qty': line.quantity,
            }))

            # ✅ FIXED: Use 'request_id' instead of 'purchase_request_id'
            pr_lines = self.env['purchase.request.line'].search([
                ('product_id', '=', line.product_id.id),
                ('request_id', 'in', po.pr_request_ids.ids),
                ('is_selected_in_po', '=', False)
            ])
            pr_lines.write({'is_selected_in_po': True})

        po.write({'order_line': [(5, 0, 0)] + order_lines})

        return {'type': 'ir.actions.act_window_close'}

