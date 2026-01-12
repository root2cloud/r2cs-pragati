from odoo import fields, api, models,_
from odoo.exceptions import UserError, ValidationError


class LoyaltyGenerateWizard(models.TransientModel):
    _inherit = 'loyalty.generate.wizard'

    coupon_qty = fields.Integer('Quantity',readonly=False, store=True)
    salesperson_id = fields.Many2one('res.users', 'Salesperson')
    price_unit = fields.Float(string="Unit Price")

    mode = fields.Selection([
        ('anonymous', 'Anonymous Customers'),
        ('selected', 'Selected Customers')],
        string='For', required=True, default='anonymous'
    )

    def generate_coupons_request(self):
        for rec in self:
            vals = {
                "coupon_qty": rec.coupon_qty,
                "salesperson_id": rec.salesperson_id.id,
                "price_unit": rec.price_unit,
                "mode": rec.mode,
                "program_id": rec.program_id.id,
                "customer_ids": [(6, 0, rec.customer_ids.ids)],
                "customer_tag_ids": [(6, 0, rec.customer_tag_ids.ids)],
                "points_granted": rec.points_granted,
                "points_name": rec.points_name,
                "valid_until": rec.valid_until,
                "status": "draft"
            }
            self.env['loyalty.generate.request'].sudo().create(vals)

    @api.depends('customer_ids', 'customer_tag_ids', 'mode')
    def _compute_coupon_qty(self):
        for wizard in self:
            if wizard.mode == 'selected':
                return self.coupon_qty
                
            else:
                wizard.coupon_qty = wizard.coupon_qty or 0
    def _get_coupon_values(self, partner):
        self.ensure_one()
        return {
            'program_id': self.program_id.id,
            'points': self.points_granted,
            'expiration_date': self.valid_until,
            'price_unit':self.price_unit,
            'partner_id': partner.id if self.mode == 'selected' else False,
            'salesperson_id':self.salesperson_id.id,
            
        }

    def generate_coupons(self):
        if any(not wizard.program_id for wizard in self):
            raise ValidationError(_("Cannot generate coupons, no program is set."))
        if any(wizard.coupon_qty <= 0 for wizard in self):
            raise ValidationError(_("Invalid quantity."))
        coupon_create_vals = []
        for wizard in self:
            if wizard.mode == 'selected':
                customers = [partner for partner in wizard._get_partners()]
            elif wizard.mode == 'anonymous':
                customers = [self.env['res.partner']]
            for partner in customers:
                for i in range(wizard.coupon_qty):
                    coupon_create_vals.append(wizard._get_coupon_values(partner))
        self.env['loyalty.card'].create(coupon_create_vals)
        return True


class CustomLoyaltyReports(models.AbstractModel):
    _name = 'report.pragati_resorts.custom_loyalty_report'
    _description = 'Pragati Resorts Custom Loyalty Report'

    def _get_report_values(self, docids, data=None):
        doc = self.env['loyalty.card'].sudo().search([('id', 'in', docids)])
        return {
            'doc_ids': self.ids,
            'doc_model': 'wizard.wizard',
            'docs': doc
        }

