
odoo.define('membership_module.slot_sale_order_creation', function (require) {
    var core = require('web.core');
    var _t = core._t;
    var ajax = require('web.ajax');
    var session = require('web.session');
    var QWeb = core.qweb;

    $(document).ready(function () {
        function createSaleOrder(button) {
            var slotId = button.data('unique-slot-id'); // Accessing data-slot-id attribute
            var productLines = []; // Ar,ray to store product details
            
            console.log(slotId)
            // Loop through each product line in the table and collect product details
            $('#slot_detail_templates tbody tr').each(function(index, element) {

                var $row = $(element); // Convert the current row to a jQuery object
                var productId = $row.data('product-id');
                var quantity = $row.find('.editable-quantity').text();
                var uomName = $row.find('td:nth-child(3)').text();
                var unitPrice = $row.find('td:nth-child(4)').text().trim(); // Fetch the price text using nth-child
                // var priceSubtotal = parseFloat($row.find('.price-subtotal').text());


                // var productId = $(this).data('product-id');
                // var quantity = $(this).find('.editable-quantity').text();
                // var uomName = $(this).find('.uom').text(); // Assuming there's a class 'uom' for UOM
                // var unitPrice = $(this).find('.unit-price').text(); // Assuming there's a class 'unit-price' for unit price
                // console.log(unitPrice)
                // var priceSubtotal = parseFloat($(this).find('.price-subtotal').text());

                if (!productId || !quantity || !uomName || isNaN(unitPrice)) {
                    return; // Skip this product line
                }else{

                    productLines.push({
                    'product_id': productId,
                    'quantity': quantity,
                    'uom_name': uomName,
                    'price_unit': unitPrice,
                   })

                }

                
            });
            console.log(productLines)

            console.log('AJAX Request Data:', {
                    'slot_id': slotId,
                    'product_data': JSON.stringify(productLines),
                });

            ajax.jsonRpc("/create_sale_order", 'call', {
                    'slot_id': slotId,
                    'product_data': JSON.stringify(productLines),
                }).then(function (response) {
                    if (response.success) {
                        // console.log(response);
                        console.log('Sale order created successfully');
                        // console.log(typeof callback);
                            
                    } else {
                        console.error('Failed to create sale order');
                          
                    }
                });

            // Send an AJAX request to create the sales order
            // $.ajax({
            //     url: '/create_sale_order', // URL for the server endpoint to handle the request
            //     type: 'POST',
            //     dataType: 'json',
            //     data: {
            //         'slot_id': slotId,
            //         'product_lines': JSON.stringify(productLines)
            //     },
            //     success: function(response) {
            //         // Handle success response
            //         alert('Sales order created successfully!');
            //     },
            //     error: function(xhr, status, error) {
            //         // Handle error response
            //         alert('Error: ' + error);
            //     }
            // });
        }

        $(".buys-btn").click(function () {
            var button = $(this);
            var slotId = button.data('unique-slot-id'); // Retrieve the unique slot ID from the button
            console.log("Slot ID:", slotId);
            createSaleOrder(button);

        });
    });
});


