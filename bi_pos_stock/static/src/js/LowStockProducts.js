odoo.define('bi_pos_stock.LowStockProducts', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");

    class LowStockProducts extends PosComponent {
        setup() {
            super.setup();
            this.state = {
                query: null,
                selectedProduct: this.props.partner,
            };
        }
        back() {
            this.props.resolve({ confirmed: false, payload: false });
            this.trigger('close-temp-screen');
        }
        get low_products(){
            return this.env.pos.low_stock_products
        }
    }


    LowStockProducts.template = 'LowStockProducts';
    Registries.Component.add(LowStockProducts);
    return LowStockProducts;

});
