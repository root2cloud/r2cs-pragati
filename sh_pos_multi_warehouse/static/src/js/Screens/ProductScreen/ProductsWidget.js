odoo.define("sh_pos_multi_warehouse.ProductsWidget", function (require) {
    "use strict";

    const ProductsWidget = require("point_of_sale.ProductsWidget");
    const Registries = require("point_of_sale.Registries");

    const WHStockProductsWidget = (ProductsWidget) =>
        class extends ProductsWidget {
            get productsToDisplay() {

                var list = super.productsToDisplay
                var self= this
                for(var i=0;i<list.length;i++){

                    var product = list[i]
                    var location_dic = self.env.pos.db.quant_by_product_id[product.id];
                    if (location_dic) {
                        
                        if(!('sh_pos_stock' in product)){
                            product["sh_pos_stock"] = 0;
                            for (var key in location_dic) {
                               
                                    var warehouse = self.env.pos.db.warehouse_by_id[key];
                                    if (warehouse) {
                                        if (self.env.pos.config.sh_warehouse_tags.includes(warehouse.id) && self.env.pos.config.sh_enable_multi_warehouse) {
                                            if (self.env.pos.config.sh_stock_type == "available_quantity") {
                                                product["sh_pos_stock"] =  product["sh_pos_stock"] + location_dic[key]["on_hand"];
                                                
                                            }
                                            if (self.env.pos.config.sh_stock_type == "available_quantity_unreserved") {
                                                product["sh_pos_stock"] = product["sh_pos_stock"] + location_dic[key]["un_reserved"];
                                            }
                                        }
                                    }
                                }
                        }
                        
                    } 
                }
                return list
            }
        };

    Registries.Component.extend(ProductsWidget, WHStockProductsWidget);
   
});
