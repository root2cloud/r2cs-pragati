odoo.define('bi_pos_stock.ProductLowStock', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');

	class ProductLowStock extends PosComponent {
		
		setup() {
            super.setup();
        }
        show_products(){
            var self = this;
			let low_stock=self.env.pos.config.low_stock
			self.rpc({
				model: 'product.product',
				method: 'get_low_stock_products',
				args: [0,low_stock],
			  }).then(function (data) {
					self.env.pos.low_stock_products = [];
					for(var k=0;k<data.length;k++){
							let product= self.env.pos.db.get_product_by_id(data[k]);
							if (product){
								self.env.pos.low_stock_products.push(product);
							}
					}
				  	self.showTempScreen('LowStockProducts');
			  });
		}
		
	}
	ProductLowStock.template = 'ProductLowStock';

	Registries.Component.add(ProductLowStock);

	return ProductLowStock;
});
