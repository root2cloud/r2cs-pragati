odoo.define("wbl_limit_cart_quantity.website_sale", function (require) {
    "use strict";

    $('.js_quantity').on('change', function (ev) {
        var $input = $(ev.currentTarget);
        var inputQty = $input.val();
        var minQty = $input.attr('data-min');
        var maxQty = $input.attr('data-max');
        $('#wbl-min-max-qty-limit-error').empty();
        if (minQty && inputQty < minQty) {
            $input.val(minQty);
            var message = 'The fewest you may purchase is ' + minQty + '.';
            $('#wbl-min-max-qty-limit-error').html(message);
            $('#wbl-min-max-order-qty-modal').modal('show');
            setTimeout(function() {
                $('#wbl-min-max-order-qty-modal').modal('hide');
            }, 3000);
        }
        if (maxQty && inputQty > maxQty) {
            $input.val(maxQty);
            var message= "The requested qty exceeds the maximum qty allowed in shopping cart";
            $('#wbl-min-max-qty-limit-error').html(message);
            $('#wbl-min-max-order-qty-modal').modal('show');
            setTimeout(function() {
                $('#wbl-min-max-order-qty-modal').modal('hide');
            }, 3000);
        }
    });
    $('.wbl-close-modal').on('click', function(){
        $('#wbl-min-max-order-qty-modal').modal('hide');
    });
    $("input[name='add_qty']").on("change", function(ev) {
        var $input = $(ev.currentTarget);
        var inputQty = $input.val();
        var minQty = $("input[name='add_qty']").attr('data-min');
        var maxQty = $("input[name='add_qty']").attr('data-max');
        $('#wbl-min-max-qty-limit-error').empty();
        if (minQty && inputQty < minQty) {
            $input.val(minQty);
            var message = 'The fewest you may purchase is ' + minQty + '.';
            $('#wbl-min-max-qty-limit-error').html(message);
            $('#wbl-min-max-order-qty-modal').modal('show');
            setTimeout(function() {
                $('#wbl-min-max-order-qty-modal').modal('hide');
            }, 3000);
        }
        if (maxQty && inputQty > maxQty) {
            $input.val(maxQty);
            var message= "The requested qty exceeds the maximum qty allowed in shopping cart";
            $('#wbl-min-max-qty-limit-error').html(message);
            $('#wbl-min-max-order-qty-modal').modal('show');
            setTimeout(function() {
                $('#wbl-min-max-order-qty-modal').modal('hide');
            }, 3000);
        }
    });
    $(".js_add_cart_json").on("click", function(ev) {
        var link = $(ev.currentTarget);
        var input = link.parent().find('input[name="add_qty"]');
        var inputQty = input.val();
        var btnTitle = this.title;
        var minQty = $("input[name='add_qty']").attr('data-min');
        var maxQty = $("input[name='add_qty']").attr('data-max');
        $('#wbl-min-max-qty-limit-error').empty();
        if (btnTitle == 'Remove one') {
            if (minQty && inputQty == minQty) {
                var message = 'The fewest you may purchase is ' + minQty + '.';
                $('#wbl-min-max-qty-limit-error').html(message);
                $('#wbl-min-max-order-qty-modal').modal('show');
                setTimeout(function() {
                    $('#wbl-min-max-order-qty-modal').modal('hide');
                }, 3000);
            }
        } else if (btnTitle == 'Add one') {
            if (maxQty && inputQty == maxQty) {
                var message= "The requested qty exceeds the maximum qty allowed in shopping cart";
                $('#wbl-min-max-qty-limit-error').html(message);
                $('#wbl-min-max-order-qty-modal').modal('show');
                setTimeout(function() {
                    $('#wbl-min-max-order-qty-modal').modal('hide');
                }, 3000);
            }
        }
    });
});
