odoo.define('pos_extension.PaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const PosInvoiceRequired = (PaymentScreen) =>
        class extends PaymentScreen {

            async _isOrderValid(isForceValidate) {
                // MUST always return true so popup can be shown later
                return await super._isOrderValid(isForceValidate);
            }

            async _finalizeValidation() {
                if (!this.currentOrder) {
                    return false;
                }

                if (!this.currentOrder.is_to_invoice()) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Invoice Required'),
                        body: this.env._t(
                            'Invoice is mandatory before payment.\n\n' +
                            'Please click the Invoice button to continue.'
                        ),
                    });
                    return false; // BLOCK PAYMENT AFTER POPUP
                }

                return await super._finalizeValidation(...arguments);
            }
        };

    Registries.Component.extend(PaymentScreen, PosInvoiceRequired);
});
