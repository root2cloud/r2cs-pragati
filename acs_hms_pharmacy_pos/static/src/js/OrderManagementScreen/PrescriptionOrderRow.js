odoo.define('pos_prescription.PrescriptionOrderRow', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const utils = require('web.utils');

    /**
     * @props {models.Order} order
     * @props columns
     * @emits click-order
     */
    class PrescriptionOrderRow extends PosComponent {
        get order() {
            return this.props.order;
        }
        get highlighted() {
            const highlightedOrder = this.props.highlightedOrder;
            return !highlightedOrder ? false : highlightedOrder.backendId === this.props.order.backendId;
        }

        // Column getters //

        get name() {
            return this.order.name;
        }
        get date() {
            return moment(this.order.date_order).format('YYYY-MM-DD hh:mm A');
        }
        get partner() {
            const partner = this.order.patient_id;
            return partner ? partner[1] : null;
        }
        get total() {
            return this.env.pos.format_currency(this.order.amount_total);
        } 
        get state() {
            let state_mapping = {
              'draft': this.env._t('Draft'),
              'prescription': this.env._t('Prescribed'),
              'cancel': this.env._t('Cancelled'),
            };

            return state_mapping[this.order.state];
        }
        get prescriptionsman() {
            const prescriptionsman = this.order.physician_id;
            return prescriptionsman ? prescriptionsman[1] : null;
        }

        get posordercount() {
            return this.order.pos_order_count;
        }
        
    }
    PrescriptionOrderRow.template = 'PrescriptionOrderRow';

    Registries.Component.add(PrescriptionOrderRow);

    return PrescriptionOrderRow;
});
