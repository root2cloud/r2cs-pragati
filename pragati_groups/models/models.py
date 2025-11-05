
from odoo import fields, api, models,_
from odoo.exceptions import UserError, ValidationError
import qrcode
import base64
from io import BytesIO


class ResUsers(models.Model):
    _inherit = 'res.users'

    phone_number = fields.Char()
# class LoyaltyGenerateWizard(models.TransientModel):
#     _inherit = 'loyalty.generate.wizard'

#     coupon_qty = fields.Integer('quantity')

# class Coupon(models.Model):
#     _inherit = 'sale.coupon'

#     sequence_id = fields.Many2one(string='Sequence')

#     @api.model
#     def create(self, vals):
#         if vals.get('sequence', 'New') == 'New':
#             vals['sequence'] = self.env['ir.sequence'].next_by_id('sale.coupon.sequence') or '/'
#             # sequence = self.env['ir.sequence'].browse(vals['sequence_id'])
#             # vals['code'] = sequence.next_by_id()
#         return super(Coupon,self).create(vals)

# class LoyaltyCard(models.Model):
#     _inherit = 'loyalty.card'


#     code = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('loyalty.card.number'))

class LoyaltyCard(models.Model):
    _inherit = "loyalty.card"

    salesperson_id = fields.Many2one('res.users', 'Salesperson')
    price_unit = fields.Float(string="Unit Price")
    qr_code = fields.Binary("QR Code", compute='generate_qr_code')
    seq_name = fields.Char(string='Seq Name', default='New')

    def create(self, vals):
        for v in vals:
            if not v.get('seq_name') or v['seq_name'] == _('New'):
                v['seq_name'] = self.env['ir.sequence'].next_by_code('loyalty.card') or _('New')
        return super(LoyaltyCard, self).create(vals)

    def get_coupon_code_status(self, code):
        vals = {}
        coupon = self.env['loyalty.card'].search([('code', '=', code)])
        if not coupon or not coupon.program_id.active or not coupon.program_id.reward_ids:
            vals['error'] = f'This code is invalid ({code})'
        elif coupon.expiration_date and coupon.expiration_date < fields.Date.today():
            vals['error'] = 'This coupon is expired.'
        elif coupon.points < min(coupon.program_id.reward_ids.mapped('required_points')):
            vals['error'] = 'This coupon has already been used.'
        program = coupon.program_id

        if not program or not program.active:
            vals['error'] = f'This code is invalid ({code})'
        elif (program.limit_usage and program.total_order_count >= program.max_usage) or \
                (program.date_to and program.date_to < fields.Date.context_today(self)):
            vals['error'] = f'This code is expired ({code})'
        sale_order_line = self.env['sale.order.line'].sudo().search([('coupon_id', '=', coupon.id)])
        if len(sale_order_line) > 1:
            vals['error'] = 'This code has already been used.'
        return vals
    def generate_qr_code(self):
        for rec in self:
            qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=3,
                    border=4,
                )
            qr.add_data("Coupon No :")
            qr.add_data(rec.code)
            vals = self.get_coupon_code_status(rec.code)
            qr.add_data(", Status :")
            if "error" in vals and vals.get('error'):
                qr.add_data(vals.get('error'))
            else:
                qr.add_data('Valid')
            qr.add_data(", Valid Till :")
            if rec.expiration_date:
                qr.add_data(str(rec.expiration_date))
            else:
                qr.add_data("Always ")
            discount_amount = self.env['loyalty.reward'].sudo().search([('program_id', '=', rec.program_id.id)], limit=1)
            if discount_amount:
                if discount_amount.program_id.coupon_value:
                    qr.add_data(", Coupon Value :")
                    qr.add_data(discount_amount.program_id.coupon_value)
                else:
                    if discount_amount.reward_type == 'product':
                        qr.add_data(", Complementary:")
                        qr.add_data(discount_amount.reward_product_id.name)
                    if discount_amount.reward_type == 'discount':
                        if discount_amount.discount_mode in ['per_order', 'per_point']:
                            qr.add_data(", Discount Amount :")
                            qr.add_data(discount_amount.discount)
                            qr.add_data("/-")
                        if discount_amount.discount_mode in ['percent']:
                            qr.add_data(", Discount % :")
                            qr.add_data(discount_amount.discount)
                            qr.add_data("%")
            else:
                qr.add_data(", Discount Amount :")
                qr.add_data(0.0)

            # qr.add_data(rec.code)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            rec.qr_code = qr_image


class LoyaltyReward(models.Model):
    _inherit = "loyalty.reward"


    reward_type = fields.Selection([
        ('product', 'Complementary'),
        ('discount', 'Discount')],
        default='discount', required=True,
    )

    values = fields.Integer(string="Value")

    def _compute_description(self):
        for reward in self:
            reward_string = ""
            if reward.program_type == 'gift_card':
                reward_string = _("Gift Card")
            elif reward.program_type == 'ewallet':
                reward_string = _("eWallet")
            elif reward.reward_type == 'product':
                products = reward.reward_product_ids
                if len(products) == 0:
                    reward_string = _('Complementary')
                elif len(products) == 1:
                    reward_string = _('Complementary - %s', reward.reward_product_id.name)
                else:
                    reward_string = _('Complementary - [%s]', ', '.join(products.mapped('name')))
            elif reward.reward_type == 'discount':
                format_string = '%(amount)g %(symbol)s'
                if reward.currency_id.position == 'before':
                    format_string = '%(symbol)s %(amount)g'
                formatted_amount = format_string % {'amount': reward.discount, 'symbol': reward.currency_id.symbol}
                if reward.discount_mode == 'percent':
                    reward_string = _('%g%% on ', reward.discount)
                elif reward.discount_mode == 'per_point':
                    reward_string = _('%s per point on ', formatted_amount)
                elif reward.discount_mode == 'per_order':
                    reward_string = _('%s per order on ', formatted_amount)
                if reward.discount_applicability == 'order':
                    reward_string += _('your order')
                elif reward.discount_applicability == 'cheapest':
                    reward_string += _('the cheapest product')
                elif reward.discount_applicability == 'specific':
                    product_available = self.env['product.product'].search(reward._get_discount_product_domain(), limit=2)
                    if len(product_available) == 1:
                        reward_string += product_available.name
                    else:
                        reward_string += _('specific products')
                if reward.discount_max_amount:
                    format_string = '%(amount)g %(symbol)s'
                    if reward.currency_id.position == 'before':
                        format_string = '%(symbol)s %(amount)g'
                    formatted_amount = format_string % {'amount': reward.discount_max_amount, 'symbol': reward.currency_id.symbol}
                    reward_string += _(' (Max %s)', formatted_amount)
            reward.description = reward_string


class LoyaltyGenerateRequest(models.Model):
    _name = 'loyalty.generate.request'
    _description = 'Generate Coupons Request'

    coupon_qty = fields.Integer('Quantity', readonly=True)
    salesperson_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    price_unit = fields.Float(string="Unit Price", readonly=True)
    program_id = fields.Many2one('loyalty.program', string='Program', readonly=True)
    mode = fields.Selection([
        ('anonymous', 'Anonymous Customers'),
        ('selected', 'Selected Customers')],
        string='For', default='anonymous', readonly=True
    )
    customer_ids = fields.Many2many('res.partner', string='Customers', readonly=True)
    customer_tag_ids = fields.Many2many('res.partner.category', string='Customer Tags', readonly=True)
    coupon_qty = fields.Integer('Quantity', readonly=True)
    points_granted = fields.Float('Grant', readonly=True)
    points_name = fields.Char(readonly=True)
    valid_until = fields.Date(readonly=True)
    status = fields.Selection([('draft', 'Draft'), ('cancel', 'Cancel'), ('reject', 'Reject'), ('approve', 'Approve')], default='draft', readonly=True)
    # is_admin_user = fields.Boolean('Is Admin User', compute='get_login_user')
    is_ajay_user = fields.Boolean('Is Ajay User', compute='_compute_is_ajay_user')

    def _compute_is_ajay_user(self):
        """Show approve button only for Ajay"""
        for rec in self:
            rec.is_ajay_user = (self.env.user.login == 'ajay@pragatigroup.com')


    #
    # def get_login_user(self):
    #     if self.env.user.id == self.env.ref('base.user_admin').id:
    #         self.is_admin_user = True
    #     else:
    #         self.is_admin_user = False

    def action_reject(self):
        for rec in self:
            rec.status = 'reject'

    def action_approve(self):
        for rec in self:
            # 🔒 Only Ajay can approve
            if self.env.user.login != 'ajay@pragatigroup.com':
                raise UserError(_("You are not authorized to approve this request."))

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
                "valid_until": rec.valid_until
            }

            self.env.user = self.create_uid
            self.env.uid = self.create_uid.id
            result = self.env['loyalty.generate.wizard'].sudo().create(vals)
            if result:
                result.generate_coupons()
                rec.status = 'approve'

    def action_approve(self):
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
                "valid_until": rec.valid_until
            }
            self.env.user = self.create_uid
            self.env.uid = self.create_uid.id
            result = self.env['loyalty.generate.wizard'].sudo().create(vals)
            if result:
                result.generate_coupons()
                rec.status = 'approve'

    def action_draft(self):
        for rec in self:
            rec.status = 'draft'

    def action_cancel(self):
        for rec in self:
            rec.status = 'cancel'


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        rec = super().button_validate()
        try:
            if self.sale_id:
                for line in self.sale_id.order_line:
                    if line.loyalty_program_id:
                        vals = {
                            "coupon_qty": line.product_uom_qty,
                            "salesperson_id": self.sale_id.salesperson_id.id,
                            "mode": "selected",
                            "program_id": line.loyalty_program_id.id,
                            "customer_ids": [(6, 0, [self.sale_id.partner_id.id])],
                            "points_granted": 1,
                            "valid_until": self.sale_id.valid_until
                        }
                        self.env.user = self.sale_id.create_uid
                        self.env.uid = self.sale_id.create_uid.id
                        result = self.env['loyalty.generate.wizard'].sudo().create(vals)
                        if result:
                            result.generate_coupons()
        except Exception as e:
            print(str(e))
        return rec


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    coupon_value = fields.Float('Coupon Value')







# from odoo import fields, api, models, _
# from odoo.exceptions import UserError, ValidationError
# import qrcode
# import base64
# from io import BytesIO
#
#
# class ResUsers(models.Model):
#     _inherit = 'res.users'
#
#     phone_number = fields.Char()
#
#
# class LoyaltyCard(models.Model):
#     _inherit = "loyalty.card"
#
#     salesperson_id = fields.Many2one('res.users', 'Salesperson')
#     price_unit = fields.Float(string="Unit Price")
#     qr_code = fields.Binary("QR Code", compute='generate_qr_code')
#     seq_name = fields.Char(string='Seq Name', default='New')
#
#     def create(self, vals):
#         if not vals.get('seq_name') or vals['seq_name'] == _('New'):
#             vals['seq_name'] = self.env['ir.sequence'].next_by_code('loyalty.card') or _('New')
#         return super(LoyaltyCard, self).create(vals)
#
#     def get_coupon_code_status(self, code):
#         vals = {}
#         coupon = self.env['loyalty.card'].search([('code', '=', code)])
#         if not coupon or not coupon.program_id.active or not coupon.program_id.reward_ids:
#             vals['error'] = f'This code is invalid ({code})'
#         elif coupon.expiration_date and coupon.expiration_date < fields.Date.today():
#             vals['error'] = 'This coupon is expired.'
#         elif coupon.points < min(coupon.program_id.reward_ids.mapped('required_points')):
#             vals['error'] = 'This coupon has already been used.'
#
#         program = coupon.program_id
#         if not program or not program.active:
#             vals['error'] = f'This code is invalid ({code})'
#         elif (program.limit_usage and program.total_order_count >= program.max_usage) or \
#                 (program.date_to and program.date_to < fields.Date.context_today(self)):
#             vals['error'] = f'This code is expired ({code})'
#
#         sale_order_line = self.env['sale.order.line'].sudo().search([('coupon_id', '=', coupon.id)])
#         if len(sale_order_line) > 1:
#             vals['error'] = 'This code has already been used.'
#         return vals
#
#     def generate_qr_code(self):
#         for rec in self:
#             qr = qrcode.QRCode(
#                 version=1,
#                 error_correction=qrcode.constants.ERROR_CORRECT_L,
#                 box_size=3,
#                 border=4,
#             )
#             qr.add_data("Coupon No :")
#             qr.add_data(rec.code)
#             vals = self.get_coupon_code_status(rec.code)
#             qr.add_data(", Status :")
#             qr.add_data(vals.get('error', 'Valid'))
#             qr.add_data(", Valid Till :")
#             qr.add_data(str(rec.expiration_date) if rec.expiration_date else "Always")
#
#             discount_amount = self.env['loyalty.reward'].sudo().search(
#                 [('program_id', '=', rec.program_id.id)], limit=1
#             )
#             if discount_amount:
#                 if discount_amount.program_id.coupon_value:
#                     qr.add_data(", Coupon Value :")
#                     qr.add_data(discount_amount.program_id.coupon_value)
#                 else:
#                     if discount_amount.reward_type == 'product':
#                         qr.add_data(", Complementary:")
#                         qr.add_data(discount_amount.reward_product_id.name)
#                     elif discount_amount.reward_type == 'discount':
#                         if discount_amount.discount_mode in ['per_order', 'per_point']:
#                             qr.add_data(", Discount Amount :")
#                             qr.add_data(discount_amount.discount)
#                             qr.add_data("/-")
#                         elif discount_amount.discount_mode == 'percent':
#                             qr.add_data(", Discount % :")
#                             qr.add_data(discount_amount.discount)
#                             qr.add_data("%")
#             else:
#                 qr.add_data(", Discount Amount :")
#                 qr.add_data(0.0)
#
#             qr.make(fit=True)
#             img = qr.make_image()
#             temp = BytesIO()
#             img.save(temp, format="PNG")
#             rec.qr_code = base64.b64encode(temp.getvalue())
#
#
# class LoyaltyReward(models.Model):
#     _inherit = "loyalty.reward"
#
#     reward_type = fields.Selection([
#         ('product', 'Complementary'),
#         ('discount', 'Discount')],
#         default='discount', required=True,
#     )
#     values = fields.Integer(string="Value")
#
#     def _compute_description(self):
#         for reward in self:
#             reward_string = ""
#             if reward.program_type == 'gift_card':
#                 reward_string = _("Gift Card")
#             elif reward.program_type == 'ewallet':
#                 reward_string = _("eWallet")
#             elif reward.reward_type == 'product':
#                 products = reward.reward_product_ids
#                 if not products:
#                     reward_string = _('Complementary')
#                 elif len(products) == 1:
#                     reward_string = _('Complementary - %s') % reward.reward_product_id.name
#                 else:
#                     reward_string = _('Complementary - [%s]') % ', '.join(products.mapped('name'))
#             elif reward.reward_type == 'discount':
#                 format_string = '%(amount)g %(symbol)s' if reward.currency_id.position == 'after' else '%(symbol)s %(amount)g'
#                 formatted_amount = format_string % {'amount': reward.discount, 'symbol': reward.currency_id.symbol}
#                 if reward.discount_mode == 'percent':
#                     reward_string = _('%g%% on ') % reward.discount
#                 elif reward.discount_mode == 'per_point':
#                     reward_string = _('%s per point on ') % formatted_amount
#                 elif reward.discount_mode == 'per_order':
#                     reward_string = _('%s per order on ') % formatted_amount
#                 if reward.discount_applicability == 'order':
#                     reward_string += _('your order')
#                 elif reward.discount_applicability == 'cheapest':
#                     reward_string += _('the cheapest product')
#                 elif reward.discount_applicability == 'specific':
#                     product_available = self.env['product.product'].search(
#                         reward._get_discount_product_domain(), limit=2
#                     )
#                     if len(product_available) == 1:
#                         reward_string += product_available.name
#                     else:
#                         reward_string += _('specific products')
#                 if reward.discount_max_amount:
#                     max_amount = format_string % {'amount': reward.discount_max_amount, 'symbol': reward.currency_id.symbol}
#                     reward_string += _(' (Max %s)') % max_amount
#             reward.description = reward_string
#
#
# class LoyaltyGenerateRequest(models.Model):
#     _name = 'loyalty.generate.request'
#     _description = 'Generate Coupons Request'
#
#     coupon_qty = fields.Integer('Quantity', readonly=True)
#     salesperson_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
#     price_unit = fields.Float(string="Unit Price", readonly=True)
#     program_id = fields.Many2one('loyalty.program', string='Program', readonly=True)
#     mode = fields.Selection([
#         ('anonymous', 'Anonymous Customers'),
#         ('selected', 'Selected Customers')],
#         string='For', default='anonymous', readonly=True
#     )
#     customer_ids = fields.Many2many('res.partner', string='Customers', readonly=True)
#     customer_tag_ids = fields.Many2many('res.partner.category', string='Customer Tags', readonly=True)
#     points_granted = fields.Float('Grant', readonly=True)
#     points_name = fields.Char(readonly=True)
#     valid_until = fields.Date(readonly=True)
#     status = fields.Selection([('draft', 'Draft'), ('cancel', 'Cancel'), ('reject', 'Reject'), ('approve', 'Approve')],
#                               default='draft', readonly=True)
#     is_ajay_user = fields.Boolean('Is Ajay User', compute='_compute_is_ajay_user')
#
#     def _compute_is_ajay_user(self):
#         for rec in self:
#             rec.is_ajay_user = self.env.user.login == 'ajay@pragatigroup.com'
#
#     def action_reject(self):
#         for rec in self:
#             rec.status = 'reject'
#
#     def action_approve(self):
#         for rec in self:
#             if self.env.user.login != 'ajay@pragatigroup.com':
#                 raise UserError(_("You are not authorized to approve this request."))
#             vals = {
#                 "coupon_qty": rec.coupon_qty,
#                 "salesperson_id": rec.salesperson_id.id,
#                 "price_unit": rec.price_unit,
#                 "mode": rec.mode,
#                 "program_id": rec.program_id.id,
#                 "customer_ids": [(6, 0, rec.customer_ids.ids)],
#                 "customer_tag_ids": [(6, 0, rec.customer_tag_ids.ids)],
#                 "points_granted": rec.points_granted,
#                 "points_name": rec.points_name,
#                 "valid_until": rec.valid_until
#             }
#             result = self.env['loyalty.generate.wizard'].sudo().create(vals)
#             if result:
#                 result.generate_coupons()
#                 rec.status = 'approve'
#
#     def action_draft(self):
#         for rec in self:
#             rec.status = 'draft'
#
#     def action_cancel(self):
#         for rec in self:
#             rec.status = 'cancel'
#
#
# class StockPicking(models.Model):
#     _inherit = 'stock.picking'
#
#     def button_validate(self):
#         rec = super().button_validate()
#         try:
#             if self.sale_id:
#                 for line in self.sale_id.order_line:
#                     if line.loyalty_program_id:
#                         vals = {
#                             "coupon_qty": line.product_uom_qty,
#                             "salesperson_id": self.sale_id.salesperson_id.id,
#                             "mode": "selected",
#                             "program_id": line.loyalty_program_id.id,
#                             "customer_ids": [(6, 0, [self.sale_id.partner_id.id])],
#                             "points_granted": 1,
#                             "valid_until": self.sale_id.valid_until
#                         }
#                         result = self.env['loyalty.generate.wizard'].sudo().create(vals)
#                         if result:
#                             result.generate_coupons()
#         except Exception as e:
#             print(str(e))
#         return rec
#
#
# class LoyaltyProgram(models.Model):
#     _inherit = 'loyalty.program'
#
#     coupon_value = fields.Float('Coupon Value')




