odoo.define("sh_pos_multi_warehouse.ProductQtyPopup", function (require) {
    "use strict";

    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const Registries = require("point_of_sale.Registries");
    const { onMounted } = owl;

    class ProductQtyPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup()
            onMounted(this.onMounted);
        }
        myFunction(event) {
            var self = this;
            if (!self.env.pos.config.sh_negative_selling && self.env.pos.config.sh_enable_multi_warehouse) {
                var qty_available = $(event.currentTarget).closest("tr").find(".data_qty")[0].innerText;
                if (parseInt($(event.currentTarget)[0].value) > parseInt(qty_available)) {
                    $(event.currentTarget)[0].classList.add("more_qty");
                    $(event.currentTarget)[0].value = "";
                } else {
                    $(event.currentTarget)[0].classList.remove("more_qty");
                }
            }
        }
        onMounted(){
            var self = this;
            if($('.qty_input_tag') && $('.qty_input_tag')[0] ){
                $($('.qty_input_tag')[0]).focus()
            }
            jQuery('.qty_input_tag').keyup(function () {     
                this.value = this.value.replace(/[^0-9\.]/g,'');
            });
        }
        add_to_cart() {
            var self = this;
            var selectedOrder = self.env.pos.get_order();
            var all_line = [];
            _.each($("input.qty_input_tag"), function (each_input_value) {
                if (each_input_value.value) {
                    var product = self.env.pos.db.get_product_by_id(self.props.product_id);
                    if (product) {
                        product["is_added"] = true;
                        selectedOrder.sh_temp = true;
                        all_line.push(product);
                        selectedOrder.add_product(product, {
                            quantity: each_input_value.value,
                            location_id: each_input_value.closest("tr").attributes[0].value,
                            merge: false,
                        });

                        product["sh_temp"] = false;
                    }
                }
            });
            self.env.pos.get_order().sh_temp = false;
            this.cancel()
        }
    }
    ProductQtyPopup.template = "ProductQtyPopup";

    Registries.Component.add(ProductQtyPopup);
    return ProductQtyPopup
});
