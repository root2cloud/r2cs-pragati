/** @odoo-module **/

import * as BarcodeScanner from '@web/webclient/barcode/barcode_scanner';
import { bus } from 'web.core';
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const { Component, onMounted, onWillUnmount, onWillStart, useState } = owl;

export class MainMenu extends Component {
    setup() {
        const user = useService('user');
        this.home = useService("home_menu");
        this.notificationService = useService("notification");
        this.rpc = useService('rpc');
        this.mobileScanner = BarcodeScanner.isBarcodeScannerSupported();
        this.state = useState({
            giftCardData: null,
            showGiftCardData: false,
        });

        onMounted(() => {
            bus.on('barcode_scanned', this, this._onBarcodeScanned);
        });
        onWillUnmount(() => {
            bus.off('barcode_scanned', this, this._onBarcodeScanned);
        });
    }

    async openMobileScanner() {
        const barcode = await BarcodeScanner.scanBarcode();
        if (barcode){
            this._onBarcodeScanned(barcode);
            if ('vibrate' in window.navigator) {
                window.navigator.vibrate(100);
            }
        } else {
            this.notificationService.add(this.env._t("Please, Scan again !"), { type: 'warning' });
        }
    }

    async _onBarcodeScanned(qrcode) {
        const res = await this.rpc('/pragati_coupon_scanner/scan', { qrcode });
        if (res.data) {
            this.state.giftCardData = res.data;
            this.state.showGiftCardData = true;  // Set it to true here
        } else {
            this.notificationService.add(res.warning, { type: 'danger' });
            this.state.showGiftCardData = false;  // Set it to false here (if needed)
        }
}

}
MainMenu.template = 'pragati_coupon_scanner.MainMenu';

registry.category('actions').add('scan_reward_rcode', MainMenu);
