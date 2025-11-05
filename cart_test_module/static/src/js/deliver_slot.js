$(document).ready(function() {
    // Function to update the total price when quantity is changed
    var updateTotalPrice = function(lineId, quantity) {
        $.ajax({
            url: '/shop/cart/update_json',
            type: 'POST',
            data: {
                line_id: lineId,
                quantity: quantity,
            },
            dataType: 'json',
            success: function(data) {
                // Update the total price in the cart view
                var totalAmountElement = $('#total_amount_' + lineId);
                if (totalAmountElement.length) {
                    totalAmountElement.text(data.total_amount);
                }
            },
            error: function() {
                console.log('Error occurred while updating quantity.');
            }
        });
    };

    // Event listener for quantity change
    $('input[name="quantity"]').change(function() {
        var lineId = $(this).closest('tr').data('line-id');
        var quantity = $(this).val();
        updateTotalPrice(lineId, quantity);
    });
});