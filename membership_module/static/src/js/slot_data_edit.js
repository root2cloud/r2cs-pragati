
odoo.define('membership_module.slot_data_edit', function (require) {
    var core = require('web.core');
    var _t = core._t;
    var ajax = require('web.ajax');
    var session = require('web.session');
    var QWeb = core.qweb;

     $(document).ready(function () {

        function processButtonAction(button,isBuyButton,callback) {

            var slotId = button.data("slot-id");
            var quantityCell = button.closest('.o_kanban_sub_sub_container_record').find('.quantity-cell');
                    
            // Extract product data from the updated UI
            var productData = [];

            quantityCell.each(function () {

                var $quantityCell = $(this);
                var productId = $(this).find('.edit-quantity-input').data('product-id');
                var quantityValue;

                if (isBuyButton) {
                    // Use the default quantity value when clicking "Slot Buy"
                    quantityValue = $quantityCell.find('.quantity-value').text();
                    // console.log(quantityValue)
                } else{ 
                    var quantityValue = $(this).find('.edit-quantity-input').val();
                    $quantityCell.find('.quantity-value').text(quantityValue);
                    $quantityCell.find('.edit-quantity-input').hide();
                    $quantityCell.find('.quantity-value').show();
                }
                

                productData.push({
                    'product_id': productId,
                    'quantity': quantityValue,
                    });
                });    

                console.log('AJAX Request Data:', {
                    'slot_id': slotId,
                    'product_data': JSON.stringify(productData),
                });

                ajax.jsonRpc("/your_custom_route/create_sale_order", 'call', {
                    'slot_id': slotId,
                    'product_data': JSON.stringify(productData),
                }).then(function (response) {
                    if (response.success) {
                        // console.log(response);
                        console.log('Sale order created successfully');
                        // console.log(typeof callback);

                        if (typeof callback === 'function') {
                            callback(response.sale_order_id,slotId);
                            console.log('Callback executed');
                        }
                            
                    } else {
                        console.error('Failed to create sale order');
                          
                    }
                });

        }

        function displaySaleOrderMessage(saleOrderId,slotId) {
            var message = 'Your slot sale order is created successfully'
            // // Replace this with your actual logic to show the message to the user (e.g., in an alert, modal, or updating an HTML element)
            // console.log(message);

            ajax.jsonRpc("/your_custom_route/get_sale_order_info", 'call', {
                'sale_order_id': saleOrderId,
            }).then(function (response) {
                if (response.success) {
                    console.log('Sale order number:', response.sale_order_number);
                    message += ' with the Sale Order Number: ' + response.sale_order_number

                    var storageKey = 'saleOrderMessageSlot' + slotId;
                    localStorage.setItem(storageKey, message);

                    showMessage(message, true,slotId);

                } else {
                    console.error('Failed to fetch sale order information');
                }
            });
        }

        
        function showMessage(message, isSuccess,slotId) {

            var elementId = 'messageSlot' + slotId;
            var pElement = document.getElementById(elementId);
            console.log(pElement)

            if (pElement) {

                var storageKey = 'saleOrderMessageSlot' + slotId;
                var storedMessage = localStorage.getItem(storageKey);
                if(storedMessage){
                    pElement.innerText = storedMessage;

                if (isSuccess) {
                    pElement.style.color = 'green'; 
                } 

                pElement.style.display = 'block';

                localStorage.removeItem(storageKey);

                }
                

                
            } else {
                console.error('Element not found with ID:', elementId);
            }
       }

        $(".edit-btn").click(function () {
        var slotId = $(this).data("slot-id");
        var quantityCell = $(this).closest('.o_kanban_sub_sub_container_record').find('.quantity-cell');

        $(this).hide();
        $(this).siblings('.save-btn').show();

        // Enable editing for the quantity
        quantityCell.each(function () {
            var $quantityCell = $(this);
            $quantityCell.find('.quantity-value').hide();
            $quantityCell.find('.edit-quantity-input').show();
            });
        });

        $(".save-btn").click(function () {
            var button = $(this);
            processButtonAction(button,false,displaySaleOrderMessage);
        
            // Hide "Save" button and show "Slot Edit" button
            $(this).hide();
            $(this).siblings('.edit-btn').show();

        });

        $(".buy-btn").click(function () {
            var button = $(this);
            processButtonAction(button,true,displaySaleOrderMessage);

        });
        
    });

});  