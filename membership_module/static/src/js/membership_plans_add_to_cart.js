odoo.define('membership_module.membership_plans_add_to_cart', function (require) {
    'use strict';

    var ajax = require('web.ajax');

    var addToCart = function (productLines, successCallback, errorCallback) {
        ajax.jsonRpc("/membership_module/add_to_cart", 'call', {
            product_lines: productLines,
        }).then(function (data) {
            successCallback(data);
        }).catch(function (error) {
            errorCallback('Error adding products to the cart: ' + JSON.stringify(error));
        });
    };

    return {
        addToCart: addToCart,
    };
});