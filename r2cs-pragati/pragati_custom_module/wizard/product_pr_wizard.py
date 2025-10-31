from odoo import fields, models, api, _

class ProductSelectionWizard(models.TransientModel):
    _name = 'product.selection.wizard'
    _description = 'Product Selection Wizard'


    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    product_wizard_line_ids = fields.One2many('product.selection.wizard.line', 'product_wizard_id', string='Wizard lines')
    select_all = fields.Boolean(string='Select All')

    @api.model
    def default_get(self, fields):
        res = super(ProductSelectionWizard, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        po = self.env['purchase.order'].browse(active_id)
        res['purchase_order_id'] = po.id

        if res['purchase_order_id']:
            # Clear existing lines only if the wizard is not in 'Select All' mode
            if not res.get('select_all'):
                res['product_wizard_line_ids'] = [(5, 0, 0)]  # Clear existing lines

            product_quantity_dict = {}  # To track quantities for each product

            for line in po.pr_request_ids.pr_request_line_ids:
                product_id = line.product_id.id
                if product_id not in product_quantity_dict:
                    product_quantity_dict[product_id] = {
                        'name': line.product_id.name,
                        'product_id': product_id,
                        'product_uom': line.product_uom_id.id,
                        'quantity': line.quantity,
                    }
                else:
                    product_quantity_dict[product_id]['quantity'] += line.quantity

            for product_data in product_quantity_dict.values():
                res['product_wizard_line_ids'].append((0, 0, product_data))

        return res

    @api.onchange('select_all')
    def _onchange_select_all(self):
        for rec in self:
            if rec.product_wizard_line_ids and rec.select_all:
                for line in rec.product_wizard_line_ids:
                    line.select_record = True
            elif rec.product_wizard_line_ids and not rec.select_all:
                for line in rec.product_wizard_line_ids:
                    line.select_record = False
                    
    def button_submit(self):
        selected_lines = self.product_wizard_line_ids.filtered('select_record')
        purchase_order = self.purchase_order_id
        pr_link_ids = self.purchase_order_id.pr_request_ids.ids

        # Clear existing order lines
        purchase_order.write({'order_line': [(5, 0, 0)]})

        # Create new order lines based on selected records
        order_lines = []
        for line in selected_lines:
            order_line = {
                'name': line.name or '',  # Set a default value for the name field
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_qty': line.quantity,
            }
            order_lines.append((0, 0, order_line))

        purchase_order.write({'order_line': order_lines})

        # Close the wizard
        return {'type': 'ir.actions.act_window_close'}


class ProductSelectionWizardLine(models.TransientModel):
    _name = 'product.selection.wizard.line'
    _description = 'Product Selection Wizard Line'

    name = fields.Char(string='Description')
    product_wizard_id = fields.Many2one('product.selection.wizard', string='Product Wizard Id')
    product_id = fields.Many2one('product.product', string='Products')
    quantity = fields.Float(string='Quantity')
    product_uom = fields.Many2one('uom.uom', string='UOM')
    select_record = fields.Boolean(string='Select', default=False)