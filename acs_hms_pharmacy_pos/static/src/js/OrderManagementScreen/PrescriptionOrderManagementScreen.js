odoo.define('pos_prescription.PrescriptionOrderManagementScreen', function (require) {
    'use strict';

    const { sprintf } = require('web.utils');
    const { parse } = require('web.field_utils');
    const { useListener } = require("@web/core/utils/hooks");
    const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const Registries = require('point_of_sale.Registries');
    const PrescriptionOrderFetcher = require('pos_prescription.PrescriptionOrderFetcher');
    const IndependentToOrderScreen = require('point_of_sale.IndependentToOrderScreen');
    const contexts = require('point_of_sale.PosContext');
    const { Orderline } = require('point_of_sale.models');

    const { onMounted, onWillUnmount, useState } = owl;

    class PrescriptionOrderManagementScreen extends ControlButtonsMixin(IndependentToOrderScreen) {
        setup() {
            super.setup();
            useListener('close-screen', this.close);
            useListener('click-prescription-order', this._onClickPrescriptionOrder);
            useListener('next-page', this._onNextPage);
            useListener('prev-page', this._onPrevPage);
            useListener('search', this._onSearch); 

            PrescriptionOrderFetcher.setComponent(this);
            this.orderManagementContext = useState(contexts.orderManagement);

            onMounted(this.onMounted);
            onWillUnmount(this.onWillUnmount);
        }
        onMounted() {
            PrescriptionOrderFetcher.on('update', this, this.render);

            // calculate how many can fit in the screen.
            // It is based on the height of the header element.
            // So the result is only accurate if each row is just single line.
            const flexContainer = this.el.querySelector('.flex-container');
            const cpEl = this.el.querySelector('.control-panel');
            const headerEl = this.el.querySelector('.header-row');
            const val = Math.trunc(
                (flexContainer.offsetHeight - cpEl.offsetHeight - headerEl.offsetHeight) /
                    headerEl.offsetHeight
            );
            PrescriptionOrderFetcher.setNPerPage(val);

            // Fetch the order after mounting so that order management screen
            // is shown while fetching.
            setTimeout(() => PrescriptionOrderFetcher.fetch(), 0);
        }
        onWillUnmount() {
            PrescriptionOrderFetcher.off('update', this);
        }
        get selectedPartner() {
            const order = this.orderManagementContext.selectedOrder;
            return order ? order.get_partner() : null;
        }
        get orders() {
            return PrescriptionOrderFetcher.get();
        }
        async _setNumpadMode(event) {
            const { mode } = event.detail;
            this.numpadMode = mode;
            NumberBuffer.reset();
        }
        _onNextPage() {
            PrescriptionOrderFetcher.nextPage();
        }
        _onPrevPage() {
            PrescriptionOrderFetcher.prevPage();
        }
        _onSearch({ detail: domain }) {
            PrescriptionOrderFetcher.setSearchDomain(domain);
            PrescriptionOrderFetcher.setPage(1);
            PrescriptionOrderFetcher.fetch();
        }
        async _onClickPrescriptionOrder(event) {
            const clickedOrder = event.detail;
            const { confirmed, payload: selectedOption } = await this.showPopup('SelectionPopup',
                {
                    title: this.env._t('What do you want to do?'),
                    list: [
                        //{id:"0", label: this.env._t("Apply a down payment"), item: false}, 
                        {id:"1", label: this.env._t("Settle the order"), item: true}],
                });

            if(confirmed){
              let currentPOSOrder = this.env.pos.get_order();
              let prescription_order = await this._getPrescriptionOrder(clickedOrder.id);
              try {
                await this.env.pos.load_new_partners();
              }
              catch (_error){
              }
              let order_partner = this.env.pos.db.get_partner_by_id(prescription_order.partner_id[0])
              if(order_partner){
                currentPOSOrder.set_partner(order_partner);
              } else {
                try {
                    await this.env.pos._loadPartners([prescription_order.partner_id[0]]);
                }
                catch (_error){
                    const title = this.env._t('Customer loading error');
                    const body = _.str.sprintf(this.env._t('There was a problem in loading the %s customer.'), prescription_order.partner_id[1]);
                    await this.showPopup('ErrorPopup', { title, body });
                }
                currentPOSOrder.set_partner(this.env.pos.db.get_partner_by_id(prescription_order.partner_id[0]));
              }
              let orderFiscalPos = prescription_order.fiscal_position_id ? this.env.pos.fiscal_positions.find(
                  (position) => position.id === prescription_order.fiscal_position_id[0]
              )
              : false;
              if (orderFiscalPos){
                  currentPOSOrder.fiscal_position = orderFiscalPos;
              }
              let orderPricelist = prescription_order.pricelist_id ? this.env.pos.pricelists.find(
                  (pricelist) => pricelist.id === prescription_order.pricelist_id[0]
              )
              : false;
              if (orderPricelist){
                  currentPOSOrder.set_pricelist(orderPricelist);
              }

              if (selectedOption){
                // settle the order
                let lines = prescription_order.prescription_line_ids;
                let product_to_add_in_pos = lines.filter(line => !this.env.pos.db.get_product_by_id(line.product_id[0])).map(line => line.product_id[0]);
                if (product_to_add_in_pos.length){
                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                        title: this.env._t('Products not available in POS'),
                        body:
                            this.env._t(
                                'Some of the products in your Prescription Order are not available in POS, do you want to import them?'
                            ),
                        confirmText: this.env._t('Yes'),
                        cancelText: this.env._t('No'),
                    });
                    if (confirmed){
                        await this.env.pos._addProducts(product_to_add_in_pos);
                    }

                }

                /**
                 * This variable will have 3 values, `undefined | false | true`.
                 * Initially, it is `undefined`. When looping thru each prescription.line,
                 * when a line comes with lots (`.lot_names`), we use these lot names
                 * as the pack lot of the generated pos.order.line. We ask the user
                 * if he wants to use the lots that come with the prescription.lines to
                 * be used on the corresponding pos.order.line only once. So, once the
                 * `useLoadedLots` becomes true, it will be true for the succeeding lines,
                 * and vice versa.
                 */
                let useLoadedLots;

                for (var i = 0; i < lines.length; i++) {
                    let line = lines[i];
                    if (!this.env.pos.db.get_product_by_id(line.product_id[0])){
                        continue;
                    }

                    let new_line = Orderline.create({}, {
                        pos: this.env.pos,
                        order: this.env.pos.get_order(),
                        product: this.env.pos.db.get_product_by_id(line.product_id[0]),
                        description: line.name,
                        price: line.price_unit,
                        tax_ids: orderFiscalPos ? undefined : line.tax_id,
                        price_manually_set: true,
                        prescription_order_origin_id: clickedOrder,
                        prescription_order_line_id: line,
                        customer_note: line.customer_note,
                    });

                    if (
                        new_line.get_product().tracking !== 'none' &&
                        (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots) &&
                        line.lot_names.length > 0
                    ) {
                        // Ask once when `useLoadedLots` is undefined, then reuse it's value on the succeeding lines.
                        const { confirmed } =
                            useLoadedLots === undefined
                                ? await this.showPopup('ConfirmPopup', {
                                      title: this.env._t('SN/Lots Loading'),
                                      body: this.env._t(
                                          'Do you want to load the SN/Lots linked to the Prescriptions Order?'
                                      ),
                                      confirmText: this.env._t('Yes'),
                                      cancelText: this.env._t('No'),
                                  })
                                : { confirmed: useLoadedLots };
                        useLoadedLots = confirmed;
                        if (useLoadedLots) {
                            new_line.setPackLotLines({
                                modifiedPackLotLines: [],
                                newPackLotLines: (line.lot_names || []).map((name) => ({ lot_name: name })),
                            });
                        }
                    }
                    new_line.setQuantityFromSOL(line);
                    new_line.set_unit_price(line.price_unit);
                    new_line.set_discount(line.discount);
                    this.env.pos.get_order().add_orderline(new_line);
                }
              }

              //currentPOSOrder.trigger('change');
              this.close();
            }

        }

        async _getPrescriptionOrder(id) {
            let prescription_order = await this.rpc({
                model: 'prescription.order',
                method: 'read', 
                args: [[id],['prescription_line_ids', 'patient_id', 'partner_id', 'pricelist_id', 'fiscal_position_id', 'amount_total', 'amount_untaxed']],
                context: this.env.session.user_context,
              });

            let prescription_line_ids = await this._getSOLines(prescription_order[0].prescription_line_ids);
            prescription_order[0].prescription_line_ids = prescription_line_ids;

            return prescription_order[0];
        }

        async _getSOLines(ids) {
          let so_lines = await this.rpc({
              model: 'prescription.line',
              method: 'read_converted',
              args: [ids],
              context: this.env.session.user_context,
          });
          return so_lines;
        }

    }
    PrescriptionOrderManagementScreen.template = 'PrescriptionOrderManagementScreen';
    PrescriptionOrderManagementScreen.hideOrderSelector = true;

    Registries.Component.add(PrescriptionOrderManagementScreen);

    return PrescriptionOrderManagementScreen;
});
