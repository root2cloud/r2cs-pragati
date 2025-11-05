odoo.define("sh_pos_multi_warehouse.ProductScreen", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");

    const WHStockProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            setup() {
                super.setup()
            }
            get_warehouse_data(product_id) {
                var self = this;
                var quant_by_product_id = this.env.pos.db.quant_by_product_id[product_id];
                var product_warehouse = [];

                if (quant_by_product_id) {
                    $.each(quant_by_product_id, function (key, value) {
                        var warehouse = self.env.pos.db.warehouse_by_id[key];
                        if (warehouse) {
                            if (self.env.pos.config.sh_warehouse_tags.includes(warehouse.id) && self.env.pos.config.sh_enable_multi_warehouse) {
                                if (!self.env.pos.config.sh_negative_selling && self.env.pos.config.sh_enable_multi_warehouse) {
                                    if (self.env.pos.config.sh_stock_type == "available_quantity" && value.on_hand >= 0) {
                                        product_warehouse.push(warehouse);
                                    }
                                    if (self.env.pos.config.sh_stock_type == "available_quantity_unreserved" && value.un_reserved >= 0) {
                                        product_warehouse.push(warehouse);
                                    }
                                } else {
                                    product_warehouse.push(warehouse);
                                }
                            }
                        }
                    });
                }
                return product_warehouse;
            }
        };

    Registries.Component.extend(ProductScreen, WHStockProductScreen);
    return WHStockProductScreen

});