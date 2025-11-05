odoo.define('appsfolio_website_minimum_cart_value.min_cart_value', function (require) {
	'use strict';

	var WebsiteSale = require('website_sale.website_sale');
	var publicWidget = require('web.public.widget');
	var wSaleUtils = require('website_sale.utils');
	var session = require('web.session');
	var VariantMixin = require('sale.VariantMixin');

	publicWidget.registry.WebsiteSale.include({
    	 events: _.extend({}, VariantMixin.events || {}, {
	        'change form .js_product:first input[name="add_qty"]': '_onChangeAddQuantity',
	        'mouseup .js_publish': '_onMouseupPublish',
	        'touchend .js_publish': '_onMouseupPublish',
	        'change .oe_cart input.js_quantity[data-product-id]': '_onChangeCartQuantity',
	        'click .oe_cart a.js_add_suggested_products': '_onClickSuggestedProduct',
	        'click a.js_add_cart_json': '_onClickAddCartJSON',
	        'click .a-submit': '_onClickSubmit',
	        'change form.js_attributes input, form.js_attributes select': '_onChangeAttribute',
	        'mouseup form.js_add_cart_json label': '_onMouseupAddCartLabel',
	        'touchend form.js_add_cart_json label': '_onMouseupAddCartLabel',
	        'click .show_coupon': '_onClickShowCoupon',
	        'submit .o_wsale_products_searchbar_form': '_onSubmitSaleSearch',
	        'change select[name="country_id"]': '_onChangeCountry',
	        'change #shipping_use_same': '_onChangeShippingUseSame',
	        'click .toggle_summary': '_onToggleSummary',
	        'click #add_to_cart, #buy_now, #products_grid .o_wsale_product_btn .a-submit': 'async _onClickAdd',
	        'click input.js_product_change': 'onChangeVariant',
	        'change .js_main_product [data-attribute_exclusions]': 'onChangeVariant',
	        'change oe_optional_products_modal [data-attribute_exclusions]': 'onChangeVariant',
	        'click .cart_update': '_onchangepricetarget',
	        'click .js_delete_product' : '_onchangepricetarget',
	        'change input.js_quantity' : '_onchangepricetarget',
    	}),

    	_onchangepricetarget: function () {
    	// Delay execution for 750 milliseconds
			setTimeout(function(){
			// Retrieve and parse the values of price and amount_total
    			var price = this.$('.company_price').val();
    			var prices = parseFloat(price)
				var amount_total = this.$('.amount_total').val();
				var amount_totals = parseFloat(amount_total)
				if (amount_totals >= prices){
	                $(".d-xl-inline-block").attr('style', 'display:none')
	                $(".warning-grater-value").hide()
	            }
	            else {
	                $(".d-xl-inline-block").attr('style', 'display:none !important')
	                $(".warning-grater-value").show()
	            }
    			location.reload();
    		}, 750);
		},
	});
});
