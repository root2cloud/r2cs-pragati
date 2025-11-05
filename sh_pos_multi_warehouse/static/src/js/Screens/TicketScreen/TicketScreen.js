odoo.define("sh_pos_multi_warehouse.TicketScreen", function (require) {
    "use strict";

    const TicketScreen = require("point_of_sale.TicketScreen");
    const Registries = require("point_of_sale.Registries");
    
    const POSTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            async _onDoRefund() {
                const order = this.getSelectedSyncedOrder();
                const partner = order.get_partner();
                const allToRefundDetails = this._getRefundableDetails(partner);
                for (const refundDetail of allToRefundDetails) {
                    const { qty, orderline } = refundDetail;
                    var product = this.env.pos.db.get_product_by_id(orderline.productId)
                    product['is_added'] = true
                }
                super._onDoRefund()
            }
            _getToRefundDetail(orderline) {
                var line = super._getToRefundDetail(orderline)
                if (orderline && orderline.location_id) {
                    line['orderline']['location_id'] = orderline.location_id
                }
                return line
            }
            
        }

    Registries.Component.extend(TicketScreen, POSTicketScreen);

    return POSTicketScreen
});
