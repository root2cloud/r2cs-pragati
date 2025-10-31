odoo.define('pos_extension.OrderSummary', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.OrderSummary');
    const Registries = require('point_of_sale.Registries');
    const { float_is_zero } = require('web.utils');

    class OrderSummary extends PosComponent {

        getSubTotalPrice() {
            let subtotal = 0.0
            
            for (let i=0; i < this.props.order.orderlines.length; i++){
                // console.log("kkkkkkkkkkkkkkkkkkkkkkkkk",mrp_prices)
                // let product = this.props.order.orderlines[i].product;
                // console.log("LLLLLLLLLLLLLLLLLLLLLLLL",products,product,product.mrp_price,product.lst_price,product.total_included)
                // let price_without_tax = product.lst_price
                // let tax = product.taxes_id.amount

                if(this.props.order.orderlines[i].product.id !== this.props.order.pos.config['discount_product_id'][0]){
                    subtotal += this.props.order.orderlines[i].price * this.props.order.orderlines[i].quantity
                    // mrp_prices += product.mrp_price * this.props.order.orderlines[i].quantity;
                }
            }
            console.log("llllllllllllllllll",subtotal)
            return this.env.pos.format_currency(subtotal)
        }
        getMrpPrice() {
            let mrp_prices = 0.0
            for (let i=0; i < this.props.order.orderlines.length; i++){
                mrp_prices += this.props.order.orderlines[i].get_price_with_tax_before_discount();

            }
            console.log("MMMMMMMMRRRRRPPPPPPPPP",mrp_prices)
            return this.env.pos.format_currency(mrp_prices)
        }

    }
    OrderSummary.template = 'OrderSummary';

    Registries.Component.add(OrderSummary);

    return OrderSummary;
});
