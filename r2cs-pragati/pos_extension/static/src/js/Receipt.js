odoo.define('pos_extension.pos', function (require) {
"use strict";

var { Order } = require('point_of_sale.models');
var Registries = require('point_of_sale.Registries');

    const POSMOdel = (Order) => class POSMOdel extends Order {

        export_for_printing() {
        var result = super.export_for_printing(...arguments);
        result.sub_total = this.get_sub_total_price()
        result.mrp_price = this.get_mrp_Price()
        return result;
        }
        get_sub_total_price(){
            let subtotal = 0.0
            for (let i=0; i < this.pos.orders[0].orderlines.length; i++){
                if(this.pos.orders[0].orderlines[i].product.id !== this.pos.config['discount_product_id'][0]){
                    subtotal += this.pos.orders[0].orderlines[i].price * this.pos.orders[0].orderlines[i].quantity
                    }
                }
            return subtotal
        }
        get_mrp_Price() {
            let mrp_prices = 0.0
            for (let i=0; i < this.pos.orders[0].orderlines.length; i++){
                mrp_prices += this.pos.orders[0].orderlines[i].get_price_with_tax_before_discount();
            }
            return mrp_prices
        }
    }

Registries.Model.extend(Order, POSMOdel);

});
