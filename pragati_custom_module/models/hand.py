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

    # @api.depends('state', 'move_id.stock_valuation_layer_ids', 'move_id.company_id')
    # def _compute_historical_prices(self):
    #     for line in self:
    #         if line.state == 'done':
    #
    #             # 1. COST PRICE LOGIC
    #             val_layers = line.move_id.stock_valuation_layer_ids
    #             if val_layers:
    #                 # Priority: Automated Valuation Layer (Receipts/Deliveries)
    #                 line.historical_cost_price = abs(val_layers[0].unit_cost)
    #             else:
    #                 # Priority: Internal Transfers / Manual History
    #                 # THE FIX: Explicitly pass the company context to read standard_price
    #                 company = line.move_id.company_id or self.env.company
    #                 cost = line.product_id.with_company(company).standard_price
    #                 line.historical_cost_price = cost
    #
    #             # 2. SALE PRICE LOGIC
    #             sale_line = line.move_id.sale_line_id
    #             if sale_line:
    #                 line.historical_sale_price = sale_line.price_unit
    #             else:
    #                 line.historical_sale_price = line.product_id.lst_price
    #         else:
    #             line.historical_cost_price = 0.0
    #             line.historical_sale_price = 0.0

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

    historical_cgst_percent = fields.Float(string='CGST %', compute='_compute_historical_taxes', store=True)
    historical_sgst_percent = fields.Float(string='SGST %', compute='_compute_historical_taxes', store=True)
    historical_igst_percent = fields.Float(string='IGST %', compute='_compute_historical_taxes', store=True)
    historical_other_percent = fields.Float(string='Other Tax %', compute='_compute_historical_taxes', store=True)

    @api.depends('state', 'move_id.sale_line_id.tax_id', 'product_id.taxes_id', 'product_id.supplier_taxes_id')
    def _compute_historical_taxes(self):
        for line in self:
            # 1. Reset all columns to 0.0
            line.historical_cgst_percent = 0.0
            line.historical_sgst_percent = 0.0
            line.historical_igst_percent = 0.0
            line.historical_other_percent = 0.0

            if line.state != 'done':
                continue

            # 2. IDENTIFY TAXES WITH COMPANY CONTEXT
            taxes = self.env['account.tax']
            company = line.move_id.company_id or self.env.company

            # Check direct source documents first
            if line.move_id.sale_line_id:
                taxes = line.move_id.sale_line_id.tax_id
            elif hasattr(line.move_id, 'purchase_line_id') and line.move_id.purchase_line_id:
                taxes = line.move_id.purchase_line_id.taxes_id

            # If no source document, fallback to the Product Card
            if not taxes:
                # CRITICAL FIX: Apply company context so Odoo actually reads the tabs
                product_ctx = line.product_id.with_company(company)

                # Merge both Customer and Vendor tabs. This guarantees we find IGST
                # regardless of which tab you typed it into on the product card.
                taxes = product_ctx.taxes_id | product_ctx.supplier_taxes_id

            # 3. EXTRACT PERCENTAGES WITHOUT DOUBLING
            if taxes:
                all_taxes = taxes.flatten_taxes_hierarchy()

                # Using local variables to track the highest percentage found
                cgst = sgst = igst = other = 0.0

                for tax in all_taxes:
                    if tax.amount_type == 'group':
                        continue

                    name = (tax.name or '').upper()

                    # CRITICAL FIX: Using max() ensures that if 'GST 2.5%' is on BOTH
                    # the Sales and Purchase tabs, it stays 2.5% and doesn't become 5.0%.
                    if 'IGST' in name:
                        igst = max(igst, tax.amount)
                    elif 'CGST' in name:
                        cgst = max(cgst, tax.amount)
                    elif 'SGST' in name:
                        sgst = max(sgst, tax.amount)
                    else:
                        other = max(other, tax.amount)

                # Assign the final clean values
                line.historical_cgst_percent = cgst
                line.historical_sgst_percent = sgst
                line.historical_igst_percent = igst
                line.historical_other_percent = other
