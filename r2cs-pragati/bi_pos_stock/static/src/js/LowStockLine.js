odoo.define('bi_pos_stock.LowStockLine', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");

    class LowStockLine extends PosComponent {
        setup() {
            super.setup();
        }
    }
    LowStockLine.template = 'LowStockLine';

    Registries.Component.add(LowStockLine);

    return LowStockLine;
});
