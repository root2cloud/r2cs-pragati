from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    on_hand_qty = fields.Float(
        string="On Hand Quantity",
        compute="_compute_on_hand_qty",
        store=False
    )

    destination_location_qty = fields.Float(
        string="On Hand Destination Quantity",
        compute="_compute_destination_location_qty",
        store=False
    )

    @api.depends('product_id', 'location_id')
    def _compute_on_hand_qty(self):
        """Fetch On-Hand Quantity from stock.quant based on the selected From Location (location_id)."""
        for line in self:
            if line.product_id and line.location_id:
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_id.id)  # Fetching stock from From Location
                ], limit=1)

                line.on_hand_qty = quant.quantity if quant else 0.0
            else:
                line.on_hand_qty = 0.0

    @api.depends('product_id', 'location_dest_id')
    def _compute_destination_location_qty(self):
        """Fetch Destination Location Quantity from stock.quant."""
        for line in self:
            if line.product_id and line.location_dest_id:
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_dest_id.id)
                ], limit=1)

                line.destination_location_qty = quant.quantity if quant else 0.0
            else:
                line.destination_location_qty = 0.0

    historical_cost_price = fields.Float(
        string='Cost Price',
        compute='_compute_historical_prices',
        store=True,
        digits='Product Price'
    )

    historical_sale_price = fields.Float(
        string='Sale Price',
        compute='_compute_historical_prices',
        store=True,
        digits='Product Price'
    )

    @api.depends('state', 'move_id.stock_valuation_layer_ids')
    def _compute_historical_prices(self):
        for line in self:
            # 1. Guard Clause: Only process finished moves
            if line.state != 'done':
                line.historical_cost_price = 0.0
                line.historical_sale_price = 0.0
                continue

            # 2. COST PRICE LOGIC
            valuation_layers = line.move_id.stock_valuation_layer_ids
            if valuation_layers:
                # Sort to get the absolute latest layer for this move
                layer = valuation_layers.sorted('create_date', reverse=True)[0]
                line.historical_cost_price = abs(layer.unit_cost)
            else:
                # Fallback for Internal Transfers & Manual History
                # Using with_company() is what fixed your 0.00 issue
                company = line.move_id.company_id or self.env.company
                product_ctx = line.product_id.with_company(company)

                cost = product_ctx.standard_price
                if not cost and product_ctx.product_tmpl_id:
                    cost = product_ctx.product_tmpl_id.standard_price
                line.historical_cost_price = cost or 0.0

            # 3. SALE PRICE LOGIC
            sale_line = line.move_id.sale_line_id
            if sale_line:
                line.historical_sale_price = sale_line.price_unit
            else:
                line.historical_sale_price = line.product_id.lst_price or 0.0

    # --- TAX AND TOTAL FIELDS ---
    historical_cgst_amount = fields.Monetary(string='CGST Amount', compute='_compute_historical_taxes', store=True,
                                             currency_field='company_currency_id')
    historical_sgst_amount = fields.Monetary(string='SGST Amount', compute='_compute_historical_taxes', store=True,
                                             currency_field='company_currency_id')
    historical_igst_amount = fields.Monetary(string='IGST Amount', compute='_compute_historical_taxes', store=True,
                                             currency_field='company_currency_id')

    historical_sale_price_incl = fields.Float(string='Sale Price (Incl)', compute='_compute_historical_taxes',
                                              store=True, digits='Product Price')
    historical_total_sale_excl = fields.Monetary(string='Total Sale (Excl)', compute='_compute_historical_taxes',
                                                 store=True, currency_field='company_currency_id')
    historical_total_sale_incl = fields.Monetary(string='Total Sale (Incl)', compute='_compute_historical_taxes',
                                                 store=True, currency_field='company_currency_id')

    company_currency_id = fields.Many2one('res.currency', related='move_id.company_id.currency_id',
                                          string="Company Currency", readonly=True)

    @api.depends('state', 'move_id.sale_line_id.tax_id', 'product_id.taxes_id', 'product_id.supplier_taxes_id',
                 'historical_sale_price', 'qty_done')
    def _compute_historical_taxes(self):
        for line in self:
            # 1. Reset all amounts to 0.0
            line.historical_cgst_amount = 0.0
            line.historical_sgst_amount = 0.0
            line.historical_igst_amount = 0.0
            line.historical_sale_price_incl = 0.0
            line.historical_total_sale_excl = 0.0
            line.historical_total_sale_incl = 0.0

            # SAFEST CHECK: Ensure we have a state and it is 'done'
            current_state = getattr(line, 'state', False)
            if current_state != 'done':
                continue

            # 2. GET THE BASE VALUE (Fix applied here: line.qty_done)
            qty = line.qty_done or 0.0
            base_amount = (line.historical_sale_price or 0.0) * qty

            # 3. IDENTIFY TAXES
            taxes = self.env['account.tax']
            company = line.move_id.company_id or self.env.company

            # Check direct source documents
            if line.move_id.sale_line_id:
                taxes = line.move_id.sale_line_id.tax_id
            elif hasattr(line.move_id, 'purchase_line_id') and line.move_id.purchase_line_id:
                taxes = line.move_id.purchase_line_id.taxes_id

            if not taxes:
                # Use sudo() here during upgrade to avoid permission-based cache misses
                product_ctx = line.product_id.with_company(company)
                taxes = product_ctx.taxes_id | product_ctx.supplier_taxes_id

            # 4. CALCULATE CURRENCY AMOUNTS & TOTALS
            cgst_amt = sgst_amt = igst_amt = 0.0

            if taxes and base_amount > 0:
                all_taxes = taxes.flatten_taxes_hierarchy()
                cgst_perc = sgst_perc = igst_perc = 0.0

                for tax in all_taxes:
                    if tax.amount_type == 'group': continue
                    name = (tax.name or '').upper()

                    if 'IGST' in name:
                        igst_perc = max(igst_perc, tax.amount)
                    elif 'CGST' in name:
                        cgst_perc = max(cgst_perc, tax.amount)
                    elif 'SGST' in name:
                        sgst_perc = max(sgst_perc, tax.amount)

                cgst_amt = (base_amount * cgst_perc) / 100.0
                sgst_amt = (base_amount * sgst_perc) / 100.0
                igst_amt = (base_amount * igst_perc) / 100.0

            # Assign Tax Values
            line.historical_cgst_amount = cgst_amt
            line.historical_sgst_amount = sgst_amt
            line.historical_igst_amount = igst_amt

            # 5. ASSIGN TOTALS AND INCLUSIVE PRICES
            line.historical_total_sale_excl = base_amount
            total_tax = cgst_amt + sgst_amt + igst_amt
            line.historical_total_sale_incl = base_amount + total_tax

            if qty > 0:
                line.historical_sale_price_incl = line.historical_total_sale_incl / qty
            else:
                line.historical_sale_price_incl = line.historical_sale_price
