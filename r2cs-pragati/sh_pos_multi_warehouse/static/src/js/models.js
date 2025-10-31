odoo.define("sh_pos_order_warehouse.models", function (require) {
    "use strict";

    const { PosGlobalState, Order, Orderline } = require('point_of_sale.models');
    var DB = require("point_of_sale.DB");
    const Registries = require("point_of_sale.Registries"); 
    const { Gui } = require("point_of_sale.Gui");

    const shWarehousePosGlobalState = (PosGlobalState) => class shWarehousePosGlobalState extends PosGlobalState {

        async _processData(loadedData) {
            await super._processData(...arguments);
            var self = this
            var  warehouses= loadedData['stock.warehouse'] || [];
            self.db.add_warehouse(warehouses);

            var  locations= loadedData['stock.location'] || [];
            self.db.add_location(locations);

            var  quants= loadedData['stock.quant'] || [];
            self.db.add_quant(quants);
        }
        
    }

    Registries.Model.extend(PosGlobalState, shWarehousePosGlobalState);

    const shWarehousePosOrder = (Order) => class shWarehousePosOrder extends Order {
        
        add_product(product, options) {
            var self = this;
            if(self && self.pos && self.pos.config && self.pos.config.sh_enable_multi_warehouse){
                if (product.detailed_type == "product" && self.get_warehouse_data(product.id).length == 0 && !self.pos.config.sh_negative_selling && self.pos.config.sh_enable_multi_warehouse) {
                    alert("Quantity Not Available");
                } else {
                    if (product.detailed_type == "product" && !product["is_added"]) {
                        var product_id = product.id;
                        var quant_by_product_id = this.pos.db.quant_by_product_id[product_id];
                        var total_qty = 0;
                        var product_warehouse;
                        var product_warehouse_data = [];
                        var warehouse_ids = []
                        if (quant_by_product_id) {
                            var warehouse_list = []
                            if (self.pos.config.sh_negative_selling && self.pos.config.sh_enable_multi_warehouse) {
                                _.each(self.pos.config.sh_warehouse_tags, function (each_warehouse_id) {
                                    if (warehouse_list.indexOf(each_warehouse_id) == (-1)) {
                                        var warehouse = self.pos.db.warehouse_data_by_id[each_warehouse_id];
                                        if (self.pos.db.quant_by_product_id[product_id] && !self.pos.db.quant_by_product_id[product_id][warehouse.lot_stock_id]) {
    
                                            self.pos.db.quant_by_product_id[product_id][warehouse.lot_stock_id] = {}
                                            if (self.pos.config.sh_stock_type == 'available_quantity') {
                                                self.pos.db.quant_by_product_id[product_id][warehouse.lot_stock_id] = { 'on_hand': 0 }
                                            }
                                            if (self.pos.config.sh_stock_type == 'available_quantity_unreserved') {
                                                self.pos.db.quant_by_product_id[product_id][warehouse.lot_stock_id] = { 'un_reserved': 0 }
                                            }
                                        }
                                    }
                                });
                            }
                            $.each(quant_by_product_id, function (key, value) {
                                var warehouse = self.pos.db.warehouse_by_id[key];
                                product_warehouse = warehouse;
                                if (warehouse) {
                                    if (self.pos.config.sh_warehouse_tags.includes(warehouse.id) && self.pos.config.sh_enable_multi_warehouse) {
                                        if (self.pos.config.sh_stock_type == "available_quantity") {
                                            total_qty += parseInt(value["on_hand"]);
                                            product_warehouse_data.push({ lot_stock_id: warehouse.lot_stock_id, warehouse_name: warehouse["name"], value: value["on_hand"], warehouse_id: warehouse.id });
                                            warehouse_ids.push(warehouse.id)
                                        }
                                        if (self.pos.config.sh_stock_type == "available_quantity_unreserved") {
                                            total_qty += parseInt(value["un_reserved"]);
                                            product_warehouse_data.push({ lot_stock_id: warehouse.lot_stock_id, warehouse_name: warehouse["name"], value: value["un_reserved"], warehouse_id: warehouse.id });
                                            warehouse_ids.push(warehouse.id)
                                        }
                                    }
                                }
                            });
                        } else {
                            if (self.pos.config.sh_negative_selling && self.pos.config.sh_enable_multi_warehouse) {
                                _.each(self.pos.config.sh_warehouse_tags, function (each_warehouse_id) {
                                    var warehouse = self.pos.db.warehouse_data_by_id[each_warehouse_id];
                                    product_warehouse_data.push({ lot_stock_id: warehouse.lot_stock_id, warehouse_name: warehouse["name"], value: 0 });
                                });
                            }
                        }
                        var product_warehouse_data_total = { total: total_qty };
                        Gui.showPopup("ProductQtyPopup", { 'title': product.display_name, 'product_id': product.id, 'product_warehouse_data': product_warehouse_data, 'product_warehouse_data_total': product_warehouse_data_total });
                    } else {
                        product["is_added"] = false;
                        super.add_product(product,options)
                    }
                }    
            }else{
                super.add_product(product,options)
            }
            
        }

        set_orderline_options(orderline, options) {
            if (options.location_id !== undefined) {
                orderline.set_location(options.location_id);
            }
           super.set_orderline_options(orderline, options)
            
        }
        get_warehouse_data(product_id) {
            var self = this;
            var quant_by_product_id = this.pos.db.quant_by_product_id[product_id];
            var product_warehouse = [];

            if (quant_by_product_id) {
                $.each(quant_by_product_id, function (key, value) {
                    var warehouse = self.pos.db.warehouse_by_id[key];
                    if (warehouse) {
                        if (self.pos.config.sh_warehouse_tags.includes(warehouse.id) && self.pos.config.sh_enable_multi_warehouse) {
                            if (!self.pos.config.sh_negative_selling && self.pos.config.sh_enable_multi_warehouse) {
                                if (self.pos.config.sh_stock_type == "available_quantity" && value.on_hand >= 0) {
                                    product_warehouse.push(warehouse);
                                }
                                if (self.pos.config.sh_stock_type == "available_quantity_unreserved" && value.un_reserved >= 0) {
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
    }

    Registries.Model.extend(Order, shWarehousePosOrder);

    const shWarehousePosOrderLine = (Orderline) => class shWarehousePosOrderLine extends Orderline {
        constructor(obj, options) {
            super(...arguments);
            this.location_id = false;
        }
        set_location (location_id) {
            this.location_id = location_id;
        }
        get_location () {
            return this.location_id || false;
        }

        export_as_JSON () {
            var json = super.export_as_JSON(...arguments);
            json.location_id = parseInt(this.location_id);
            return json;
        }
        set_quantity(quantity, keep_price) {
            var self = this;
            var class1 = $('article[data-product-id=' + self.product.id + ']').find('.sh_warehouse_display')
            if (self.quantity && (quantity || quantity == 0) && self.product && self.product.id && self.location_id && self.pos.db.quant_by_product_id && self.pos.db.quant_by_product_id[self.product.id] && ((self.pos.db.quant_by_product_id[self.product.id][self.location_id]) || (self.pos.db.quant_by_product_id[self.product.id][self.location_id] == 0)) && self.pos.get_order() && !self.pos.get_order().sh_temp && self.pos.config.sh_enable_multi_warehouse) {
                if (self.pos.config.sh_stock_type == 'available_quantity') {
                    self.pos.db.quant_by_product_id[self.product.id][self.location_id]['on_hand'] = self.pos.db.quant_by_product_id[self.product.id][self.location_id]['on_hand'] + self.quantity
                    var total_quantity = parseFloat(class1.text())
                    total_quantity = total_quantity + self.quantity
                    if (class1.length > 0) {
                        class1.text(parseFloat(total_quantity))
                    }
                } else if (self.pos.config.sh_stock_type == 'available_quantity_unreserved') {
                    self.pos.db.quant_by_product_id[self.product.id][self.location_id]['un_reserved'] = self.pos.db.quant_by_product_id[self.product.id][self.location_id]['un_reserved'] + self.quantity
                    var total_quantity = parseFloat(class1.text())
                    total_quantity = total_quantity + self.quantity
                    if (class1.length > 0) {
                        class1.text(parseFloat(total_quantity))
                    }
                }
            }
            var quantity = super.set_quantity(quantity, keep_price)
            if(self.pos.config.sh_enable_multi_warehouse){
                
                if (self.pos.config.sh_warehouse_tags && self.pos.config.sh_warehouse_tags.length > 0 && self.product && this.product.detailed_type == "product" && self.pos.db.quant_by_product_id && self.pos.db.quant_by_product_id[self.product.id] && self.location_id && self.pos.db.quant_by_product_id[self.product.id][self.location_id]) {
                    if (self.pos.config.sh_stock_type == 'available_quantity') {
                        self.pos.db.quant_by_product_id[self.product.id][self.location_id]['on_hand'] = self.pos.db.quant_by_product_id[self.product.id][self.location_id]['on_hand'] - self.quantity
                        var total_quantity = parseFloat(class1.text())
                        total_quantity = total_quantity - self.quantity
                        if (class1.length > 0) {
                            class1.text(parseFloat(total_quantity))
                            if(self.pos.db.get_product_by_id(self.product.id)){
                                self.pos.db.get_product_by_id(self.product.id)['sh_pos_stock'] = total_quantity
                            }
                        }
                    } else if (self.pos.config.sh_stock_type == 'available_quantity_unreserved') {
                        self.pos.db.quant_by_product_id[self.product.id][self.location_id]['un_reserved'] = self.pos.db.quant_by_product_id[self.product.id][self.location_id]['un_reserved'] - self.quantity
                        var total_quantity = parseFloat(class1.text())
                        total_quantity = total_quantity - self.quantity
                        if (class1.length > 0) {
                            class1.text(parseFloat(total_quantity))
                        }
                    }
                }
            }
            return quantity
        }
    }
    Registries.Model.extend(Orderline, shWarehousePosOrderLine);

});
