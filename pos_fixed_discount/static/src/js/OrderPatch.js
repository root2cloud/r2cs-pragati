odoo.define('pos_fixed_discount.OrderPatch', function(require) {
    'use strict';

    const { Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const FixedDiscountOrder = (Order) => class extends Order {
        constructor(obj, options) {
            super(obj, options);
            this.fixed_discount_amount = 0;
        }

        get_fixed_discount_amount() {
            return this.fixed_discount_amount || 0;
        }

        apply_fixed_discount(amount) {
            // Reset all line discounts first to prevent compounding
            this.get_orderlines().forEach(line => line.set_discount(0));

            if (amount <= 0) {
                this.fixed_discount_amount = 0;
                return;
            }

            const orderlines = this.get_orderlines();
            if (orderlines.length === 0) {
                return;
            }

            // Get the base total with tax
            const base_total = this.get_total_with_tax();

            if (amount >= base_total) {
                // Apply maximum discount (100% on all lines)
                orderlines.forEach(line => line.set_discount(100));
                this.fixed_discount_amount = base_total;
            } else {
                // Calculate the global discount percentage
                let discount_pct = (amount / base_total) * 100;

                // CRITICAL FIX: Round to exactly 2 decimal places to match Odoo's strict database schema.
                // This guarantees the frontend and backend calculate the exact same final invoice total.
                let rounded_pct = parseFloat(discount_pct.toFixed(2));

                // Apply the exact same 2-decimal percentage to all lines
                orderlines.forEach(line => line.set_discount(rounded_pct));

                this.fixed_discount_amount = amount;
            }
        }

        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.fixed_discount_amount = this.fixed_discount_amount;
            return json;
        }

        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.fixed_discount_amount = json.fixed_discount_amount || 0;
            if (this.fixed_discount_amount > 0) {
                // Reapply the discount when loading from JSON
                this.apply_fixed_discount(this.fixed_discount_amount);
            }
        }
    };

    Registries.Model.extend(Order, FixedDiscountOrder);

    return Order;
});