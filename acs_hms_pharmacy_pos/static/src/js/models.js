odoo.define('pos_prescription.models', function (require) {
    "use strict";

var { Order, Orderline } = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');

const PosSaleOrderline = (Orderline) => class PosSaleOrderline extends Orderline {
  constructor(obj, options) {
      super(...arguments);
      // It is possible that this orderline is initialized using `init_from_JSON`,
      // meaning, it is loaded from localStorage or from export_for_ui. This means
      // that some fields has already been assigned. Therefore, we only set the options
      // when the original value is falsy.
      this.prescription_order_origin_id = this.prescription_order_origin_id || options.prescription_order_origin_id;
      this.prescription_order_line_id = this.prescription_order_line_id || options.prescription_order_line_id;
      this.acs_kit_details = this.acs_kit_details || options.acs_kit_details;
      this.customerNote = this.customerNote || options.customer_note;
  }
  init_from_JSON(json) {
      super.init_from_JSON(...arguments);
      this.prescription_order_origin_id = json.prescription_order_origin_id;
      this.prescription_order_line_id = json.prescription_order_line_id;
      this.acs_kit_details = json.acs_kit_details && JSON.parse(json.acs_kit_details);
  }
  export_as_JSON() {
      const json = super.export_as_JSON(...arguments);
      json.prescription_order_origin_id = this.prescription_order_origin_id;
      json.prescription_order_line_id = this.prescription_order_line_id;
      json.acs_kit_details = this.acs_kit_details && JSON.stringify(this.acs_kit_details);
      return json;
  }
  get_prescription_order(){
      if(this.prescription_order_origin_id) {
        let value = { 
            'name': this.prescription_order_origin_id.name,
            'details': this.acs_kit_details || false,
            'is_kit_product': this.prescription_order_line_id && this.prescription_order_line_id.is_kit_product || false,
            'kit_product_name': this.prescription_order_line_id && this.prescription_order_line_id.kit_product_name || false,
            'kit_product_qty': this.prescription_order_line_id && this.prescription_order_line_id.kit_product_qty || false
        }
        return value;
      }
      return false;
  }

  export_for_printing() {
    var json = super.export_for_printing(...arguments);
    json.acs_kit_details =  this.acs_kit_details;
    if (this.prescription_order_origin_id) {
        json.so_reference = this.prescription_order_origin_id.name;
    }
    return json;
  }
  /**
   * Set quantity based on the give prescription order line.
   * @param {'prescription.line'} prescriptionOrderLine
   */
  setQuantityFromSOL(prescriptionOrderLine) {
      if (this.product.type === 'service') {
        this.set_quantity(prescriptionOrderLine.qty_to_invoice);
      } else {
        this.set_quantity(prescriptionOrderLine.product_uom_qty - Math.max(prescriptionOrderLine.qty_delivered, prescriptionOrderLine.qty_invoiced));
      }
  }
}
Registries.Model.extend(Orderline, PosSaleOrderline);

});
