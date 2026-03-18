odoo.define('pos_fixed_discount.FixedDiscountButton', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    class FixedDiscountButton extends PosComponent {
        get currentOrder() {
            return this.env.pos.get_order();
        }
        get isOrderEmpty() {
            return !this.currentOrder || this.currentOrder.orderlines.length === 0;
        }
        async onClick() {
            if (this.isOrderEmpty) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('No Items in Order'),
                    body: this.env._t('Please add items to the order before applying a discount.'),
                });
                return;
            }

            const currentDiscount = this.currentOrder.get_fixed_discount_amount() || 0;

            const { confirmed, payload: amount } = await this.showPopup('NumberPopup', {
                title: this.env._t('Fixed Discount Amount'),
                startingValue: currentDiscount,
                isInputSelected: true,
            });

            if (confirmed) {
                const discountAmount = parseFloat(amount) || 0;
                this.currentOrder.apply_fixed_discount(discountAmount);
            }
        }
    }

    FixedDiscountButton.template = 'pos_fixed_discount.FixedDiscountButton';
    Registries.Component.add(FixedDiscountButton);

    // Add control button to ProductScreen
    ProductScreen.addControlButton({
        name: 'FixedDiscountButton',
        component: 'FixedDiscountButton',
        condition: function() {
            return this.env.pos && this.env.pos.get_order();
        },
        position: ['after', 'SetCustomerButton'],
    });

    return FixedDiscountButton;
});