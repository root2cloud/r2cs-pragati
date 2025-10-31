odoo.define('membership_module.membership_plans_script', function (require) {
    'use strict';

    var fetchSlotData = require('membership_module.membership_plans_fetch_data').fetchSlotData;
    var addToCart = require('membership_module.membership_plans_add_to_cart').addToCart;

    window.onClickBuyButton = function (slotId, productId, quantity) {
        console.log('Button clicked!');
        fetchSlotData(slotId, function (data) {
            var productLines = data.product_line_ids.map(function (line) {
                return {
                    'product_id': line.product_id,
                    'quantity': line.quantity
                };
            });
            addToCart(productLines, function (cartData) {
                // Handle success, you may want to update UI or show a message
                console.log('Products added to the cart:', cartData);
            }, function (error) {
                // Handle error, show an alert or log it
                console.error('Error adding products to the cart:', error);
            });
        }, function (error) {
            // Handle error, show an alert or log it
            console.error('Error fetching slot data:', error);
        });
    };

});