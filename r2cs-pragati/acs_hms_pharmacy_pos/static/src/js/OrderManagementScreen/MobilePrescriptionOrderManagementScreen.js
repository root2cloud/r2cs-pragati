odoo.define('point_of_sale.MobilePrescriptionOrderManagementScreen', function (require) {
    const PrescriptionOrderManagementScreen = require('pos_prescription.PrescriptionOrderManagementScreen');
    const Registries = require('point_of_sale.Registries');

    const { useListener } = require("@web/core/utils/hooks");
    const { useState } = owl;

    const MobilePrescriptionOrderManagementScreen = (PrescriptionOrderManagementScreen) => {
        class MobilePrescriptionOrderManagementScreen extends PrescriptionOrderManagementScreen {
            setup() {
                super.setup();
                useListener('click-order', this._onShowDetails)
                this.mobileState = useState({ showDetails: false });
            }
            _onShowDetails() {
                this.mobileState.showDetails = true;
            }
        }
        MobilePrescriptionOrderManagementScreen.template = 'MobilePrescriptionOrderManagementScreen';
        return MobilePrescriptionOrderManagementScreen;
    };

    Registries.Component.addByExtending(MobilePrescriptionOrderManagementScreen, PrescriptionOrderManagementScreen);

    return MobilePrescriptionOrderManagementScreen;
});