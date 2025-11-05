odoo.define("sh_pos_order_warehouse.db", function (require) {
    "use strict";

    var DB = require("point_of_sale.DB");

    DB.include({
        init: function (options) {
            this._super(options);
            this.warehouse_by_id = {};
            this.location_by_id = {};
            this.quant_by_id = {};
            this.quants = [];
            this.quant_by_product_id = {};
            this.lot_stock_list = [];
            this.warehouse_data_by_id = {};
        },
        add_warehouse: function (warehouses) {
            for (var i = 0, len = warehouses.length; i < len; i++) {
                var warehouse = warehouses[i];
                this.warehouse_by_id[warehouse.lot_stock_id] = warehouse;
                this.lot_stock_list.push(warehouse.lot_stock_id);
                this.warehouse_data_by_id[warehouse.id] = warehouse;
            }
        },
        add_location: function (locations) {
            for (var i = 0, len = locations.length; i < len; i++) {
                var location = locations[i];
                this.location_by_id[location.id] = location;
            }
        },
        add_quant: function (quants) {
            for (var i = 0, len = quants.length; i < len; i++) {
                var quant = quants[i];
                this.quants.push(quant);
                this.quant_by_id[quant.id] = quant;

                if (quant.product_id in this.quant_by_product_id) {
                    var tmp_loc_dic = this.quant_by_product_id[quant.product_id];
                    if (quant.location_id in tmp_loc_dic) {
                        var tmp_qt = tmp_loc_dic[quant.location_id];
                        tmp_loc_dic[quant.location_id] = { on_hand: quant.quantity + tmp_qt, un_reserved: quant.quantity + tmp_qt - quant.reserved_quantity };
                    } else {
                        tmp_loc_dic[quant.location_id] = { on_hand: quant.quantity, un_reserved: quant.quantity - quant.reserved_quantity };
                    }
                    this.quant_by_product_id[quant.product_id] = tmp_loc_dic;
                } else {
                    var location_qty_dic = {};
                    location_qty_dic[quant.location_id] = { on_hand: quant.quantity, un_reserved: quant.quantity - quant.reserved_quantity };
                    this.quant_by_product_id[quant.product_id] = location_qty_dic;
                }


            }
        },
    });
});
