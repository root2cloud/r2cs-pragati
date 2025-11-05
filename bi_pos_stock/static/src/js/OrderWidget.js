odoo.define('bi_pos_stock.OrderWidgetExtended', function(require){
	'use strict';

	const OrderWidget = require('point_of_sale.OrderWidget');
	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');

	const OrderWidgetExtended = (OrderWidget) =>
		class extends OrderWidget {
			
			get orderlines(){
				let order = this.env.pos.get_order();
                var orderlines = order.get_orderlines();
				return orderlines;
			}
            get product_total(){
                let order = this.env.pos.get_order();
                var orderlines = order.get_orderlines();
                return orderlines.length;
            }

		};

	Registries.Component.extend(OrderWidget, OrderWidgetExtended);
	return OrderWidget;

});