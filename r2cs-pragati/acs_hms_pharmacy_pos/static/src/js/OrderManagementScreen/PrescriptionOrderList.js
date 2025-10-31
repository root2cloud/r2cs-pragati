odoo.define('pos_prescription.PrescriptionOrderList', function (require) {
    'use strict';

    const { useListener } = require("@web/core/utils/hooks");
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    const { useState } = owl;

    /**
     * @props {models.Order} [initHighlightedOrder] initially highligted order
     * @props {Array<models.Order>} orders
     */
    class PrescriptionOrderList extends PosComponent {
        setup() {
            super.setup();
            useListener('click-order', this._onClickOrder);
            this.state = useState({ highlightedOrder: this.props.initHighlightedOrder || null });
        }
        get highlightedOrder() {
            return this.state.highlightedOrder;
        }
        _onClickOrder({ detail: order }) {
            this.state.highlightedOrder = order;
        }
    }
    PrescriptionOrderList.template = 'PrescriptionOrderList';

    Registries.Component.add(PrescriptionOrderList);

    return PrescriptionOrderList;
});
