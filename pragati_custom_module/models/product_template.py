from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @tools.ormcache()
    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('product.product_category_all')

    product_ref = fields.Char(
        string='Product S.NO:', required=True, copy=False, readonly=True, tracking=True,
        default=lambda self: _('New'))
    tracking = fields.Selection(tracking=True)
    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True)
    radio_field = fields.Selection([('none', 'None'), ('leafy', 'Leafy'), ('normal', 'Normal')], string="Radio Field",
                                   default='none')
    # detailed_type = fields.Selection(
    #     selection=[('consu', 'Consumable'), ('service', 'Service'), ('non_stockable', 'Non-stockable'), ('asset', 'Asset')],
    #     string='Detailed Type',
    #     default='consu',
    #     ondelete={'non_stockable': 'cascade', 'asset': 'cascade'},
    # )
    unit_cost = fields.Float(string='Unit Cost')
    unit_name_value = fields.Char(string='Unit Value')
    product_uom_name = fields.Char(related='uom_id.name', string="Product UOM", store=True)
    # website_ribbon_id = fields.Many2one('product.ribbon', string='Ribbon', compute='_compute_website_ribbon_id')

    website_ribbon_id = fields.Many2one('product.ribbon', string='Ribbon', related='ribbon_domain_id', store=True,
                                        readonly=False)

    ribbon_domain_id = fields.Many2one('product.ribbon', compute='_compute_ribbon_domain_id', store=True)

    @api.depends('qty_available')
    def _compute_ribbon_domain_id(self):
        for rec in self:
            if rec.qty_available < 2:
                rec.ribbon_domain_id = rec.env['product.ribbon'].search([('html', '=', 'Out of stock')], limit=1)
                rec.allow_out_of_stock_order = False
            else:
                rec.ribbon_domain_id = False
                rec.allow_out_of_stock_order = True

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            new_name = values.get('name')
            existing_product = self.env['product.template'].search([('name', 'ilike', new_name)])

            if existing_product:
                for existing in existing_product:
                    if existing.name.lower() == new_name.lower():
                        raise ValidationError(_(f"A product with the same name already exists: {existing.name}"))

            if values.get('product_ref', _('New')) == _('New'):
                # Get the name of the category
                category_name = values.get('categ_id') and self.env['product.category'].browse(
                    values['categ_id']).name or ''

                # Get the next sequence number
                sequence_number = self.env["ir.sequence"].next_by_code("product.template")

                # Construct the product_ref with category_name and sequence number
                product_ref = f'{category_name[:3].upper()}/{sequence_number}'

                values['product_ref'] = product_ref

        return super(ProductTemplate, self).create(values_list)

    # @api.model
    # def create(self, values):
    #     new_name = values.get('name')
    #     existing_product = self.env['product.template'].search([('name', 'ilike', new_name)])

    #     if existing_product:
    #         for existing in existing_product:
    #             if existing.name.lower() == new_name.lower():
    #                 raise ValidationError(_(f"A product with the same name already exists: {existing.name}"))

    #     if values.get('product_ref', _('New')) == _('New'):
    #         # Get the name of the category
    #         category_name = values.get('categ_id') and self.env['product.category'].browse(values['categ_id']).name or ''

    #         # Get the next sequence number
    #         sequence_number = self.env["ir.sequence"].next_by_code("product.template")

    #         # Construct the product_ref with category_name and sequence number
    #         product_ref = f'{category_name[:3].upper()}/{sequence_number}'

    #         values['product_ref'] = product_ref

    #     return super(ProductTemplate, self).create(values)

    @api.constrains('l10n_in_hsn_code')
    def _check_hsn_code(self):
        for record in self:
            if not record.l10n_in_hsn_code:
                raise UserError("Please Update the HSN Code")

    @api.onchange('list_price')
    def _onchange_unit_cost(self):
        kg_uom = self.env['uom.uom'].search([('name', '=', 'kg')], limit=1)

        for record in self:
            if (
                    record.uom_id
                    and record.uom_id == kg_uom
                    and record.radio_field == 'normal'
            ):
                record.write({'unit_cost': record.list_price / 4, 'unit_name_value': '250 Grams'})
            elif (
                    record.uom_id
                    and record.uom_id == kg_uom
                    and record.radio_field == 'leafy'
            ):
                record.write({'unit_cost': record.list_price / 10, 'unit_name_value': '100 Grams'})
            else:
                record.write({'unit_cost': False, 'unit_name_value': False})


class ProductProduct(models.Model):
    _inherit = 'product.product'

    radio_field = fields.Selection(related='product_tmpl_id.radio_field', string="Radio Field", store=True)
    product_uom_name = fields.Char(related='product_tmpl_id.product_uom_name', string="Product UOM", store=True)
    unit_cost = fields.Float(string='Unit Cost', related='product_tmpl_id.unit_cost', store=True)
    unit_name_value = fields.Char(string='Unit Value', related='product_tmpl_id.unit_name_value', store=True)


class Website(models.Model):
    _inherit = 'website'

    def _get_combination_info(self, product_template_id, product_id, combination, add_qty, pricelist):
        res = super(WebsiteSale, self)._get_combination_info(
            product_template_id, product_id, combination, add_qty, pricelist)

        product = self.env['product.product'].browse(product_id) if product_id else None
        if product:
            res.update({
                'unit_cost': product.unit_cost,
                'unit_name_value': product.unit_name_value,
                'product_uom_name': product.product_uom_name,
            })

        return res
