odoo.define("sh_pos_multi_warehouse.RefundButton", function (require) {
    "use strict";


    const RefundButton = require("point_of_sale.RefundButton");
    const Registries = require("point_of_sale.Registries");

    const WHStockRefundButton = (RefundButton) =>
        class extends RefundButton {
            _onClick() {
                this.env.pos.is_ticket_screen_show = true;
                super._onClick()
            }
        };
        Registries.Component.extend(RefundButton, WHStockRefundButton);

});