from odoo import fields, api, models,_


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('request', 'Request'), ('reject','Reject')])
    loyalty_program_id = fields.Many2one('loyalty.program', string = "Program Name")
    is_admin_user = fields.Boolean('Is Admin User', compute='get_login_user')
    salesperson_id = fields.Many2one('res.users', 'Salesperson')
    valid_until = fields.Date()
    mobile = fields.Char(string='Mobile')
    location = fields.Char(string = 'location')
    is_program_available = fields.Boolean(string='Is Program Available', default=False)

    @api.onchange('partner_id')
    def _onchange_partner_id_mobile(self):
        for order in self:
            order.mobile = order.partner_id.mobile if order.partner_id else ""

    # @api.onchange('partner_id')
    # def _onchange_partner_id_location(self):
    #     for order in self:
    #         order.location = order.partner_id.location if order.partner_id else ""


    def get_login_user(self):
        if self.env.user.id == self.env.ref('base.user_admin').id:
            self.is_admin_user = True
        else:
            self.is_admin_user = False
        for order in self:
            for line in order.order_line:
                temp = False
                if line.loyalty_program_id:
                    temp = True
                order.is_program_available = temp

    def request_for_approval(self):
        for rec in self:
            rec.state = 'request'

    def request_for_reject(self):
        for rec in self:
            rec.state = 'reject'

    def request_for_approve(self):
        for rec in self:
            rec.action_confirm()

    def action_confirm(self):
        res = super().action_confirm()
        try:
            for line in self.order_line:
                vals = {
                    'product_id': line.product_id.id,
                    'order_id': line.order_id.id,
                    'partner_id': self.partner_id.id,
                    'date': self.date_order,
                    'qty': line.product_uom_qty,
                    'mobile': self.mobile,
                    'location': self.location,
                    'salesperson_id':self.salesperson_id.id
                }
                if line.loyalty_program_id:
                    vals['loyalty_program_id'] = line.loyalty_program_id.id
                if line.coupon_id:
                    vals['used_coupon_code'] = line.coupon_id.code
                self.env['loyalty.sale.report'].sudo().create(vals)
        except Exception as e:
            print(str(e))
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_default_product_id(self):
        domain = [('name', 'ilike', "coupon")]
        product_id = self.env['product.product'].search(domain,limit=1)
        if product_id:
            return product_id.id
        return False

    
    loyalty_program_id = fields.Many2one('loyalty.program', string = "Program Name")
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        change_default=True, ondelete='restrict', check_company=True, index='btree_not_null',
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",default=_get_default_product_id)

    @api.onchange('loyalty_program_id')
    def _onchange_loyalty_program_id(self):
        for line in self:
            if line.loyalty_program_id:
                line.order_id.sudo().write({'is_program_available': True})
