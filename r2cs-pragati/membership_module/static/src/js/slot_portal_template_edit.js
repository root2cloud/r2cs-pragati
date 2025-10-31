odoo.define('membership_module.slot_portal_template_edit', function(require) {
	var core = require('web.core');
	var _t = core._t;
	var ajax = require('web.ajax');
	var QWeb = core.qweb;
    var session = require('web.session');

	$(document).ready(function(){
		// localStorage.clear()
        
        var portalBlock = document.querySelector('.o_portal_block');
	    var partnerIdText = document.getElementById('partner-id')
	    if (partnerIdText) {
	        var partnerId = partnerIdText.textContent.split(':')[1].trim();
	        console.log('Partner ID:', partnerId);
	    } 

	    

		console.log('Partner ID:', partnerId);
        var uniqueSlotId = $(".o_portal_block").attr("id");
        console.log("unique ID:", uniqueSlotId);
        // renderSlotSaleOrder(uniqueSlotId);
   

        var totalText = $('.total_amount').text().trim();
	    var totalAmounts = parseFloat(totalText);
        
        var templateSaved = JSON.parse(localStorage.getItem('templateSaved')) || {};

        function saveTemplateProducts(partnerId, slotId) {
        		console.log('save template')
			    var templateProducts = []; // Array to store template products

			    if (!templateSaved[partnerId]) {
			        templateSaved[partnerId] = {}; // Initialize if not already initialized
			    }

			    if (templateSaved[partnerId][slotId]) {
			    	console.log('Template already saved for partner', partnerId, 'and slot', slotId);
			    	return;
			    }

			    // Loop through the template product rows and gather data
			    $('#slot_detail_templates tbody tr').each(function(index, element) {

	                var $row = $(element); // Convert the current row to a jQuery object
	                var productId = $row.data('product-id');
	                var productName = $row.find('td:first').text().trim();
	                var quantity = $row.find('.editable-quantity').text();
	                var uomName = $row.find('td:nth-child(3)').text();
	                var unitPrice = $row.find('td:nth-child(4)').text().trim();
	      
	                // var partnerIdText = document.getElementById('partner-id')
	                // var partnerId = partnerIdText.textContent.split(':')[1].trim();

	                // var uniqueSlotId = $(".o_portal_block").attr("id");


	                if (!productId || !quantity || !uomName || isNaN(unitPrice)) {
	                    return; // Skip this product line
	                }else{

	                    templateProducts.push({
	                    'slot_id': slotId,
	                    'product_id': productId,
			            'name': productName,
                        'uomName': uomName,
			            'quantity': quantity,
			            'price': unitPrice
	                   })

	                }
			        console.log('666666666',templateProducts)
	            })

				    ajax.jsonRpc("/backend/save-template-products", 'call', {
		                    'slot_id': uniqueSlotId,
		                    'template_products': JSON.stringify(templateProducts),
		                     'partner_id' : partnerId
		                }).then(function (response) {
		                    if (response.success) {
		                        // console.log(response);
		                        console.log('Template products saved successfully:');
		                        // console.log(typeof callback);
		                        templateSaved[partnerId][slotId] = true;
		                        console.log('Template products saved successfully:',templateSaved[partnerId][slotId]);
		                        localStorage.setItem('templateSaved', JSON.stringify(templateSaved),{ sameSite: 'None', secure: true });
		                            
		                    } else {
		                        console.error('Error saving template products:');
		                          
		                    }
		                });
	        }

	    function hideExtraPaymentMessage(slotId,partnerId) {
                	console.log(partnerId)
				    $('#extra-amount-display').text('');
				    $('#extra-payment-button').remove();
				    var checkboxHtml = '<input type="checkbox" id="extra-amount-paid" checked disabled>';
				    $('#extra-amount-display').append(checkboxHtml);
				    $('#extra-amount-display').append('<label for="extra-amount-paid">Extra amount is paid</label>');

				    if (!templateSaved[partnerId]) {
				    	console.log('000000000000')
        				templateSaved[partnerId] = {}; // Initialize templateSaved object for the user if not already initialized
    				}

				    if (!templateSaved[partnerId][slotId]) {
				        saveTemplateProducts(partnerId, slotId); // Save the template only if not already saved
				        templateSaved[partnerId][slotId] = true; // Set the flag to indicate that the template is saved for the user and slot
				        console.log(templateSaved[partnerId][slotId])
				        localStorage.setItem('templateSaved', JSON.stringify(templateSaved),{ sameSite: 'None', secure: true });   
				    }

				    // Disable edit, delete, and add product buttons
				    $('.edit-button, .delete-icon, .btn-add-products').prop('disabled', true);

				    
				}
				

            function showExtraPaymentMessage(slotId,partnerId) {
				    var extraAmount = parseFloat($("#extra-amount").text());
				    
				    if (extraAmount > 0) {
				        $('#extra-amount-display').text('You have exceeded the slot maximum amount. So you need to pay extra amount.');
				        $('#extra-amount-display').append('<br>Extra amount: ' + extraAmount.toFixed(2) + ' rupees');
				        $('#extra-amount-display').append('<button type="button" class="btn btn-primary m-2" id="extra-payment-button">Pay Extra Amount</button>');
				    } else {
				        $('#extra-amount-display').text('');
				        $('#extra-amount').text('0.00');
				        $('#extra-payment-button').remove(); // Remove the extra payment button if not needed
				    }
				}	
    

	       
	    function hasSaleOrderForSlot(slotId) {
				    //Implementation to check if the slot has a sale order
				    //This could be an AJAX call to your backend to check if a sale order exists for the slot
				    console.log('backend calling---',slotId)
				    $.ajax({
				        url: '/backend/check-sale-order',
				        method: 'GET',
				        data: {slotId: slotId },
				        success: function(response) {
				            if (response.hasSaleOrder) {
				                // Sale order exists for the slot
				                hideExtraPaymentMessage(slotId,partnerId);
				            } else {
				                // No sale order exists for the slot
				                showExtraPaymentMessage(slotId,partnerId);
				            }
				        },
				        error: function(xhr, status, error) {
				            console.error('Error checking sale order:', error);
				        }
				    });
			   }    
	    
		
        
		function updateTotalAmount() {
			console.log(totalAmounts)
			    var totalAmount = 0;
			    $('.quantity-cell').each(function() {
			    	var $row = $(this).closest('tr');
			        var quantity = parseFloat($(this).find('.editable-quantity').text());
			        var price = parseFloat($(this).closest('tr').find('td:eq(3)').text());
			        var subtotal = quantity * price;
			        $row.find('td:eq(4)').text(subtotal.toFixed(2));
			        totalAmount += quantity * price;
			    });
			    $('.total_amount').text(totalAmount.toFixed(2));
			    var originalAmount = parseFloat($(".original_amount").text());
	            var extraAmount = totalAmount - originalAmount;
	            $("#extra-amount").text(extraAmount.toFixed(2));

	            // var partnerIdText = document.getElementById('partner-id')
                // var partnerId = partnerIdText.textContent.split(':')[1].trim();

	            var currentSlotId = uniqueSlotId;
                hasSaleOrderForSlot(currentSlotId)

                if (totalAmount < originalAmount) {
			        $('#add-products-message').text('Your amount is less than the slot original amount. So you need to add the products.');
                }
                else{
                	$('#add-products-message').text('');

                }

                // function hideExtraPaymentMessage(slotId,partnerId) {
                // 	console.log(partnerId)
				//     $('#extra-amount-display').text('');
				//     $('#extra-payment-button').remove();
				//     var checkboxHtml = '<input type="checkbox" id="extra-amount-paid" checked disabled>';
				//     $('#extra-amount-display').append(checkboxHtml);
				//     $('#extra-amount-display').append('<label for="extra-amount-paid">Extra amount is paid</label>');

				//     if (!templateSaved[partnerId]) {
				//     	console.log('000000000000')
        		// 		templateSaved[partnerId] = {}; // Initialize templateSaved object for the user if not already initialized
    			// 	}

				//     if (!templateSaved[partnerId][slotId]) {
				//         saveTemplateProducts(partnerId, slotId); // Save the template only if not already saved
				//         templateSaved[partnerId][slotId] = true; // Set the flag to indicate that the template is saved for the user and slot
				//         console.log(templateSaved[partnerId][slotId])
				//         localStorage.setItem('templateSaved', JSON.stringify(templateSaved),{ sameSite: 'None', secure: true });   
				//     }

				//     // Disable edit, delete, and add product buttons
				//     $('.edit-button, .delete-icon, .btn-add-products').prop('disabled', true);

				    
				// }
				

                // function showExtraPaymentMessage(slotId,partnerId) {
				// 	    var extraAmount = parseFloat($("#extra-amount").text());
					    
				// 	    if (extraAmount > 0) {
				// 	        $('#extra-amount-display').text('You have exceeded the slot maximum amount. So you need to pay extra amount.');
				// 	        $('#extra-amount-display').append('<br>Extra amount: ' + extraAmount.toFixed(2) + ' rupees');
				// 	        $('#extra-amount-display').append('<button type="button" class="btn btn-primary m-2" id="extra-payment-button">Pay Extra Amount</button>');
				// 	    } else {
				// 	        $('#extra-amount-display').text('');
				// 	        $('#extra-amount').text('0.00');
				// 	        $('#extra-payment-button').remove(); // Remove the extra payment button if not needed
				// 	    }
				// 	}	

			   //  function hasSaleOrderForSlot(slotId) {
			// 	    //Implementation to check if the slot has a sale order
			// 	    //This could be an AJAX call to your backend to check if a sale order exists for the slot
			// 	    console.log('backend calling---',slotId)
			// 	    $.ajax({
			// 	        url: '/backend/check-sale-order',
			// 	        method: 'GET',
			// 	        data: {slotId: slotId },
			// 	        success: function(response) {
			// 	            if (response.hasSaleOrder) {
			// 	                // Sale order exists for the slot
			// 	                hideExtraPaymentMessage(slotId,partnerId);
			// 	            } else {
			// 	                // No sale order exists for the slot
			// 	                showExtraPaymentMessage(slotId,partnerId);
			// 	            }
			// 	        },
			// 	        error: function(xhr, status, error) {
			// 	            console.error('Error checking sale order:', error);
			// 	        }
			// 	    });
			   // }


			    return totalAmount; 
		}

		function hideDeletedRows() {
		    var deletedProducts = localStorage.getItem('deletedProducts');
		    deletedProducts = deletedProducts ? JSON.parse(deletedProducts) : [];
		    console.log('dlete',deletedProducts)
		    deletedProducts.forEach(function(lineId) {
		        console.log('Deleting:', lineId);
		        var row = $('tr[data-line-id="' + lineId + '"]');
		        console.log('Row:', row);
		        if (row.length > 0) {
		            row.remove(); // Hide the row if it exists
		            console.log('Row Hidden');
		        } else {
		            console.log('Row not found:', lineId);
		        }
		    });
		    updateTotalAmount()

		}

		function loadEditedQuantitiesFromLocalStorage(partnerId, uniqueSlotId) {
		    // Iterate through all the products
		    $('.editable-quantity').each(function() {
		        var productName = $(this).closest('tr').find('td:first').text().trim();
		        var key = partnerId + '_' + uniqueSlotId + '_' + productName;
		        
		        // Retrieve the edited quantity for the current product from local storage
		        var storedData = localStorage.getItem(key);
		        console.log('After deletion - Local Storage Data:', storedData);
		        
		        if (storedData) {
		            var editedQuantity = JSON.parse(storedData)[productName];
		            var data = JSON.parse(storedData);
		            var addedToSlot = data['data-added-to-slot'];
		            
		            if (addedToSlot === 'true') {
		                // Update the UI to reflect that the product was added to the slot
		                $(this).closest('tr').attr('data-added-to-slot', 'true');
		            } else {
		                // Update the UI to reflect that the product was not added to the slot
		                $(this).closest('tr').removeAttr('data-added-to-slot');
		            }


		            
		            // Update the UI with the edited quantity
		            $(this).text(editedQuantity).show();
		            $(this).closest('tr').find('.edit-quantity').val(editedQuantity).hide();
		        }
		    });
		    updateTotalAmount();
	    }

	    function loadAddedProductsFromLocalStorage(partnerId, uniqueSlotId) {
	    	console.log('444',uniqueSlotId)
	   
		        var key = partnerId + '_' + uniqueSlotId 
		        var addedProducts = JSON.parse(localStorage.getItem(key)) || [];

		     // Iterate through the added products
			    addedProducts.forEach(function(addedProduct) {
			        // Check if the added product matches the current partnerId and uniqueSlotId
			        if (addedProduct.partnerId === partnerId && addedProduct.uniqueSlotId === uniqueSlotId) {
			            // Create a new row for the added product in the table
			            var productRowHTML = '<tr data-line-id="' + addedProduct.lineId + '" data-product-id="' + addedProduct.productId + '" data-added-to-slot="true">' +
			                                    '<td>' +
                                    				'<img src="' + addedProduct.imageData + '" alt="' + addedProduct.productName + '" class="slot-product-image">' +
                                   					 addedProduct.productName +
                                    			'</td>' +
			                                    '<td class="quantity-cell">' +
			                                        '<span class="editable-quantity" data-value="' + addedProduct.quantity + '">' + addedProduct.quantity + '</span>' +
			                                        '<input type="number" class="edit-quantity" style="display:none;" value="' + addedProduct.quantity + '"/>' +
			                                    '</td>' +
			                                    '<td>' + addedProduct.uom + '</td>' +
			                                    '<td>' + addedProduct.price.toFixed(2) + '</td>' +
			                                    '<td>' + (addedProduct.quantity * addedProduct.price).toFixed(2) + '</td>' +
			                                    // '<td>' +
			                                    //     '<button type="button" class="btn btn-primary edit-button">Edit</button>' +
			                                    //     '<button type="button" class="btn btn-primary save-button" style="display: none;">Save</button>' +
			                                    // '</td>' +
			                                    // '<td>' +
			                                    //     '<i class="fa fa-trash delete-icon" style="color: black; cursor: pointer;"></i>' +
			                                    // '</td>' +
			                                '</tr>';

			            // Add the new row to the table
			            var $productRow = $(productRowHTML);
				        $productRow.attr('data-added-to-slot', 'true'); // Set data-added-to-slot attribute to true
				        $('#product_placeholder_row').before($productRow);
				        updateTotalAmount();
			        }
		        });
			
		}
        
		
        hideDeletedRows();

		loadEditedQuantitiesFromLocalStorage(partnerId, uniqueSlotId)
		
		loadAddedProductsFromLocalStorage(partnerId, uniqueSlotId)
    

		function updateLocalStorageOnQuantityEdit(partnerId, uniqueSlotId, productName, newQuantity) {
		    // Construct a unique key for the edited quantity based on partnerId, uniqueSlotId, and productName
		    var key = partnerId + '_' + uniqueSlotId + '_' + productName;

		    // Retrieve existing data from local storage
		    var storedData = localStorage.getItem(key);

            
		    // Parse the stored data as JSON or initialize an empty object if no data exists
		    var dataToUpdate = storedData ? JSON.parse(storedData) : {};

		    // Update the quantity for the specific product
		    dataToUpdate[productName] = newQuantity;

		    // Store the updated data back in local storage
		    localStorage.setItem(key, JSON.stringify(dataToUpdate));
		    console.log(key)
		}

		function storeAddedProductInLocalStorage(partnerId, uniqueSlotId, lineId, productId, productName, quantity, uom, price, imageData = null) {
		    console.log('444',uniqueSlotId)
		    var key = partnerId + '_' + uniqueSlotId;
		    // Get the existing added products from local storage
		    var addedProducts = localStorage.getItem(key);
		    addedProducts = addedProducts ? JSON.parse(addedProducts) : [];

		    // Create an object to represent the added product
		    var addedProduct = {
		        partnerId: partnerId,
		        uniqueSlotId: uniqueSlotId,
		        lineId: lineId,
		        productId: productId,
		        productName: productName,
		        quantity: quantity,
		        uom: uom,
		        imageData: imageData,
		        price: price
		    };
		    console.log('4444',addedProduct)

		    // Add the new added product to the array
		    addedProducts.push(addedProduct);

		    // Store the updated added products array back in local storage
		    localStorage.setItem(key, JSON.stringify(addedProducts));
		    console.log('Updated added products:', key);

		}

        
        function isWithin48Hours(slotDate) {
	        var currentTime = new Date();
	        var differenceInMilliseconds = new Date(slotDate) - currentTime;
	        var differenceInHours = differenceInMilliseconds / (1000 * 60 * 60);
	        return differenceInHours >= 48 && differenceInHours > 0; // Check if difference is less than 48 hours and greater than 0
	    }   

		$(document).on('click', '.edit-button', function() {
			var slotDate = $('p:contains("Slot Date:")').text().trim().split(':')[1].trim();
			// if (isWithin48Hours(slotDate)) {
				var $row = $(this).closest('tr');
				$row.find('.editable-quantity').hide();
				$row.find('.edit-quantity').show().val($row.find('.editable-quantity').text());
				$(this).hide();
				$row.find('.save-button').show();
			// } else {
            // 		alert("You can only edit before 48 hours before slot_date.");
            // }
		});

		$(document).on('click', '.save-button', function() {
			var portalBlock = document.querySelector('.o_portal_block');
			
			var partnerIdText = document.getElementById('partner-id').textContent;
			var partnerId = partnerIdText.split(':')[1].trim();
			console.log('Partner ID:', partnerId);


			console.log(portalBlock);
		    if (portalBlock) {
			    // Get the value of the t-att-id attribute
			    var uniqueSlotId = portalBlock.getAttribute('id');
		
			} else {
			    console.error('Element with class o_portal_block not found.');
			}

			var $row = $(this).closest('tr');
			var newQuantityInput = $row.find('.edit-quantity').val(); // Get the input value as string
    		var newQuantity = parseFloat(newQuantityInput).toFixed(2);
    		console.log(typeof(newQuantity))
			var oldQuantity = parseFloat($row.find('.editable-quantity').text());
			var priceText = $row.find('td:nth-child(4)').text().trim(); // Retrieve the price text
            

            var productName = $row.find('td:first').text().trim();
            
            console.log('data:', productName, newQuantity, oldQuantity);

		    // Check if priceText is empty or not a valid numerical value
		    if (!priceText || isNaN(parseFloat(priceText))) {
		        console.error("Invalid price text:", priceText);
		        return;
		    }
		    
		    var price = parseFloat(priceText);
			var subtotalCell = $row.find('td:nth-child(5)');
			
			// Calculate new subtotal for the product line
			var newSubtotal = newQuantity * price;
			var oldSubtotal = parseFloat(subtotalCell.text());
			subtotalCell.text(newSubtotal.toFixed(2)); // Update displayed subtotal

			// Calculate change in subtotal for this product line
			var subtotalChange = newSubtotal - oldSubtotal;

			// Update total price based on subtotal change
			var totalText = $('.total_amount').text().trim();
			var totalAmount = parseFloat(totalText);

			// Update total amount based on subtotal change
			var newTotal = totalAmount + subtotalChange;
			console.log(newTotal)

			// Show message indicating the change in quantity and subtotal
			if (subtotalChange > 0) {
				message = "You increased the " + productName.trim() + " quantity from " + oldQuantity + " to " + newQuantity + ", so the extra amount is $" + subtotalChange.toFixed(2);
			} else if (subtotalChange < 0) {
				message = "You decreased the " + productName.trim() + " quantity from " + oldQuantity + " to " + newQuantity + ", so the amount decreased by $" + Math.abs(subtotalChange).toFixed(2);
			} else {
				message = "No change in subtotal.";
			}

			// Update total price display
			// $('.total_amount').text(newTotal.toFixed(2));

			// Hide edit quantity input and show editable quantity
			$row.find('.edit-quantity').hide();
			$row.find('.editable-quantity').text(newQuantity).show();

			// Toggle visibility of buttons
			$(this).hide();
			$row.find('.edit-button').show();

			// Show message to the customer
			showMessage(message);

			if (subtotalChange > 0) {
		        $row.attr('data-added-to-slot', 'true');
		        $('#extra-payment-button').show();

		        // Store the product details including the data-added-to-slot attribute to local storage
		        var key = partnerId + '_' + uniqueSlotId + '_' + productName;
			    var storedData = localStorage.getItem(key);
			    var dataToUpdate = storedData ? JSON.parse(storedData) : {};
			    dataToUpdate['data-added-to-slot'] = 'true';
			    localStorage.setItem(key, JSON.stringify(dataToUpdate));
		    } else {
		        $row.removeAttr('data-added-to-slot');
		        $('#extra-payment-button').hide();

		        var key = partnerId + '_' + uniqueSlotId + '_' + productName;
                localStorage.removeItem(key);
		    }
		
		    updateTotalAmount();
		    updateLocalStorageOnQuantityEdit(partnerId, uniqueSlotId, productName, newQuantity)
		});


        $(document).on('click', '#extra-payment-button', function() {
            var totalAmount = updateTotalAmount();
            var extraAmount = totalAmount - totalAmounts;

            addSlotProductsToCart();

            var uniqueSlotId = $(".o_portal_block").attr("id");
            hasSaleOrderForSlot(uniqueSlotId);
        });
        function addSlotProductsToCart() {
        	console.log('@@@@')
        	var products = [];
        	var extraAmount = parseFloat($("#extra-amount").text()); 
            console.log( '^^^^^^',extraAmount)

            var uniqueSlotId = $(".o_portal_block").attr("id");
            console.log("unique ID:",uniqueSlotId)
    		//Loop through the product lines and add them to the cart
		    $('#slot_detail_templates tbody tr[data-added-to-slot="true"]:not(#product_placeholder_row, #message_area)').each(function() {
		    	console.log('999')
		    	var $productRow = $(this);
		        var productId = $productRow.data('product-id');
		        var productName = $productRow.find('td:first').text().trim();
		        var quantity;

		            // Check if the quantity is displayed as text (default product)
		        if ($productRow.find('.editable-quantity').is(':not(:input)')) {
		            // If it's a default product, retrieve the quantity from the visible text
		            quantity = parseInt($productRow.find('.editable-quantity').text());
		        } else {
		                // If it's a newly added product, retrieve the quantity from the input field
		                quantity = parseInt($productRow.find('.edit-quantity').val());
		            }
		        var price = parseFloat($productRow.find('td:nth-child(4)').text());

		        console.log("Product ID:", productId);
		        console.log("Product Name:", productName);
		        console.log("Quantity:", quantity);
		        console.log("Price:", price);

		        var oldQuantity = parseInt(localStorage.getItem(productName)) || 0;
		        console.log(productName)
		        console.log(oldQuantity)
		        console.log(quantity)
        		var increaseQuantity = quantity - oldQuantity;
        		console.log(increaseQuantity)
        		var extraAmount = parseFloat($("#extra-amount").text()); 
        		console.log( '^^^^^^',extraAmount)
 
                if ($productRow.attr('data-added-to-slot') === 'true' && oldQuantity === 0){
                	console.log(' quantity')
                	if (productId && productName && !isNaN(quantity) && !isNaN(price)) {
		                products.push({
		                    'id': productId,
		                    'name': productName,
		                    'quantity': quantity,
		                    'extraAmount': extraAmount,
		                });
		            }

                }
                

                if ($productRow.attr('data-added-to-slot') === 'true' && oldQuantity !== 0 && increaseQuantity > 0) {
                	console.log('edit quantity')
                	if (productId && productName && !isNaN(quantity) && !isNaN(price)) {
		                products.push({
		                    'id': productId,
		                    'name': productName,
		                    'quantity': increaseQuantity,
		                    'extraAmount': extraAmount,
		                });
		            }
				}            

		    });


		    ajax.jsonRpc('/add_to_cart_with_extra_payment', 'call', {
                'products': products,
                'uniqueSlotId':uniqueSlotId

            }).then(function(response) {
                // Handle success response
                console.log('Products added to cart with extra payment');
                // Redirect to payment page
                var redirectUrl = "/shop/payment";
		        window.location.href = redirectUrl;

		        

            }).catch(function(error) {
                // Handle error response
                console.error('Error adding products to cart:', error);
            });
		}



		function showMessage(message) {
			// Display message to the customer
			$('#message_area').text(message);
		}

		function generateLineId() {
		    // Implement your logic to generate a unique ID here
		    // For demonstration, using a simple counter
		    var lineIdCounter = $('#slot_detail_templates tbody tr').length + 1;
		    return lineIdCounter;
		}

		$(document).on('click', '.delete-icon', function() {
			var slotDate = $('p:contains("Slot Date:")').text().trim().split(':')[1].trim(); // Extract slot date from the page
        	// if (isWithin48Hours(slotDate)) {
	            var row = $(this).closest('tr');
	            var productName = row.find('td:first').text().trim(); // Get the product name
	            var lineId = row.attr('data-line-id');
			    var partnerId = $('#partner-id').text().trim().split(':')[1].trim();
			    var uniqueSlotId = $('.o_portal_block').attr('id');
	            
	            // Store the product key or ID in local storage
			    var deletedProducts = localStorage.getItem('deletedProducts');
			    deletedProducts = deletedProducts ? JSON.parse(deletedProducts) : [];
			    deletedProducts.push(lineId);
			    localStorage.setItem('deletedProducts', JSON.stringify(deletedProducts));
                
                console.log(deletedProducts)
			    // Remove the row from the table
			    row.remove();


			    // Update total amount after removing the product
			    updateTotalAmount();
            // } else {
	        //     // Alert the user that they cannot delete after 48 hours of slot_date
	        //     alert("You can only delete before 48 hours before slot_date.");
            // }
        });


		$('.btn-add-products').click(function () {
			var slotDate = $('p:contains("Slot Date:")').text().trim().split(':')[1].trim(); // Extract slot date from the page
        	// if (isWithin48Hours(slotDate)) {
				ajax.jsonRpc('/get_inventory_products', 'call', {})
					.then(function (data) {
						renderKanbanView(data);
					});
			// } else {
		    //         // Alert the user that they cannot add after 48 hours of slot_date
		    //         alert("You can only add products before 48 hours before slot_date.");
		    //     }	
		});

		function renderKanbanView(data) {
		    $('.kanban_view_container').html('');

		    var leafProducts = data.leaf_products;
		    var normalProducts = data.normal_products;

		    renderProducts('<h4 class="leaf-heading">Leaf Products :</h4>', leafProducts, '.kanban_view_container');
		    renderProducts('<h4 class="normal-heading">Normal Products :</h4>', normalProducts, '.kanban_view_container');

		    $('.products_karban_views_wrapper').show();
		}
      
		function renderProducts(title, products, containerSelector) {
		    var $container = $(containerSelector);
		    $container.append('<h3>' + title + '</h3>');

		    var $productGroup = $('<div class="product_group"></div>'); // Create a product group container

		    for (var i = 0; i < products.length; i++) {
		        var product = products[i];
		        var $productDiv = $('<div class="kanban_product"></div>');
		        $productDiv.attr('data-product-id', product.id);

		        var $image = $('<img src="' + product.image_url + '" alt="' + product.name + '">');
		        $image.addClass('product_image');
                $productDiv.append($image);

		        $productDiv.append('<p><strong>Product Name:</strong> ' + product.name + '</p>');
		        var $quantityDiv = $('<div class="quantity"></div>');
		        $quantityDiv.append('<strong>Quantity:</strong> ');

		        var $quantityContainer = $('<div class="quantity-container"></div>');
		        $quantityContainer.append('<i class="fa fa-minus decrease-quantity"></i>');
		        $quantityContainer.append('<span class="quantity-value">' + product.quantity + '</span>');
		        $quantityContainer.append('<i class="fa fa-plus increase-quantity"></i>');
		        $quantityDiv.append($quantityContainer);
        
        		$productDiv.append($quantityDiv);

		        $productDiv.append('<p><strong>UOM :</strong> ' + product.uom + '</p>');
		        var formattedPrice = parseFloat(product.list_price).toFixed(2);
				var priceHTML = '<p><strong>Unit Price:</strong>' + formattedPrice + '</p>';
				$productDiv.append(priceHTML);
		        
                // Add status information
		        if (product.status === 'Out of Stock') {
		            var $badge = $('<span class="badge badge-danger">Out of Stock</span>');
		            $productDiv.append($badge);
		        }else{
		        	var $button = $('<button class="btn btn-primary add-to-slot">Add to Slot</button>');
		        	$productDiv.append($button);
		        }

		        

		        $productGroup.append($productDiv); // Append product to the product group
		    }

		    $container.append($productGroup); // Append the product group to the main container
		    
		    // Increment and decrement functionality
		    $(document).off('click', '.increase-quantity').on('click', '.increase-quantity', function(){
	        var quantitySpan = $(this).siblings('.quantity-value');
	        var currentQuantity = parseInt(quantitySpan.text());
	        quantitySpan.text(currentQuantity + 1);
    		});

		    $(document).off('click', '.decrease-quantity').on('click', '.decrease-quantity', function(){
		        var quantitySpan = $(this).siblings('.quantity-value');
		        var currentQuantity = parseInt(quantitySpan.text());
		        if (currentQuantity > 1) {
		            quantitySpan.text(currentQuantity - 1);
		        }
		    });

		    $(document).off('click', '.add-to-slot').on('click', '.add-to-slot', function(){
		    	var lineId = generateLineId();

		    	var portalBlock = document.querySelector('.o_portal_block');
				console.log(portalBlock);
			    if (portalBlock) {
				    // Get the value of the t-att-id attribute
				    var uniqueSlotId = portalBlock.getAttribute('id');
			
				} else {
				    console.error('Element with class o_portal_block not found.');
				}

				var portalBlock = document.querySelector('.o_portal_block');
			
				var partnerIdText = document.getElementById('partner-id').textContent;
				var partnerId = partnerIdText.split(':')[1].trim();

			    var $product = $(this).closest('.kanban_product');
			    var productId = $product.data('product-id');
			    var productNameFull = $product.find('p strong:contains("Product Name")').parent().text().trim();
			    var productName = productNameFull.replace('Product Name:', '').trim();
			    var quantity = parseInt($product.find('.quantity-value').text());
			    // console.log(quantity)
			    var uomFull = $product.find('p strong:contains("UOM")').parent().text().trim();
	            var uom = uomFull.replace('UOM :', '').trim();
			    var $priceElement = $product.find('p strong:contains("Unit Price")');
			    // console.log($priceElement)
				var price = 0; // Default price

				if ($priceElement.length > 0) {
			        var priceText = $priceElement.parent().contents().filter(function() {
			            return this.nodeType == 3; // Filter out text nodes
			        }).text().trim();
			        var priceWithoutDollar = priceText.replace('$', '').trim()
			        var price = parseFloat(priceWithoutDollar);
			    } else {
			        console.error("Price element not found for product:", productName);
			    }
	            
	            var subtotal = price * quantity;

	            
	            // Check if the product already exists in the table
	            var productExists = false;

	            // console.log("Before each loop");
	            // console.log($('#slot_detail_templates tbody tr'));

	            $('#slot_detail_templates tbody tr').each(function(){
	            	// console.log("Inside each loop");
			        var $row = $(this);
			        var existingProductName = $row.find('td:first-child').text().trim();
			        // console.log(existingProductName)
			        var existingProductId = $row.data('product-id');
	        		if (existingProductName === productName)  {
			            // Update quantity and subtotal if product already exists
			            var existingQuantity = parseInt($row.find('.editable-quantity').attr('data-value'));
			            var newQuantity = existingQuantity + quantity;
			            $row.find('.editable-quantity').attr('data-value', newQuantity).text(newQuantity);
			            $row.find('.edit-quantity').val(newQuantity)
			            
			            var subtotal = newQuantity * price;
			            $row.find('td:nth-child(5)').text(subtotal.toFixed(2));
			            // Set flag to true to indicate product exists
			            productExists = true;
			            updateTotalAmount()
			            updateLocalStorageOnQuantityEdit(partnerId, uniqueSlotId, productName, newQuantity);

			            return false; // Exit the loop
			        }
			    })
			    // console.log("After each loop");
			    if (!productExists){
			    	var imageData = '';
				    if (product.image) {
				        // Assuming product.image contains the URL of the image
				        // Fetch the image and convert it to base64
				        var img = new Image();
				        img.crossOrigin = 'Anonymous';
				        img.onload = function() {
				            var canvas = document.createElement('canvas');
				            canvas.width = img.width;
				            canvas.height = img.height;
				            var ctx = canvas.getContext('2d');
				            ctx.drawImage(img, 0, 0);
				            imageData = canvas.toDataURL('image/png');
				            // Add a new row for the product
				            var productRowHTML = '<tr data-line-id="' + lineId + '" data-product-id="' + productId + '" data-added-to-slot="true">' +
				                                '<td><img src="' + imageData + '" alt="' + productName + '" class="slot-product-image">' + productName + '</td>' +
				                                '<td class="quantity-cell">' +
				                                '<span class="editable-quantity" data-value="' + quantity + '">' + quantity + '</span>' +
				                                '<input type="number" class="edit-quantity" style="display:none;" value="' + quantity + '"/>' +
				                                '</td>' +
				                                '<td>' + uom + '</td>' +
				                                '<td>' + price.toFixed(2) + '</td>' +
				                                '<td>' + (quantity * price).toFixed(2) + '</td>' +
				                                '<td>' +
				                                '<button type="button" class="btn btn-primary edit-button">Edit</button>' +
				                                '<button type="button" class="btn btn-primary save-button" style="display: none;">Save</button>' +
				                                '</td>' +
				                                '<td>' +
				                                '<i class="fa fa-trash delete-icon" style="color: black; cursor: pointer;"></i>' +
				                                '</td>' +
				                                '</tr>';
				            $('#product_placeholder_row').before(productRowHTML);
				            updateTotalAmount();
				            $product.attr('data-added-to-slot', 'true');
				            storeAddedProductInLocalStorage(partnerId, uniqueSlotId, lineId, productId, productName, quantity, uom, price, imageData);
				        };
				        img.src = product.image;
				    } else {
				        // Add a new row for the product without the image
				        var productRowHTML = '<tr data-line-id="' + lineId + '" data-product-id="' + productId + '" data-added-to-slot="true">' +
				                            '<td>' + productName + '</td>' +
				                            '<td class="quantity-cell">' +
				                            '<span class="editable-quantity" data-value="' + quantity + '">' + quantity + '</span>' +
				                            '<input type="number" class="edit-quantity" style="display:none;" value="' + quantity + '"/>' +
				                            '</td>' +
				                            '<td>' + uom + '</td>' +
				                            '<td>' + price.toFixed(2) + '</td>' +
				                            '<td>' + (quantity * price).toFixed(2) + '</td>' +
				                            // '<td>' +
				                            // '<button type="button" class="btn btn-primary edit-button">Edit</button>' +
				                            // '<button type="button" class="btn btn-primary save-button" style="display: none;">Save</button>' +
				                            // '</td>' +
				                            // '<td>' +
				                            // '<i class="fa fa-trash delete-icon" style="color: black; cursor: pointer;"></i>' +
				                            // '</td>' +
				                            '</tr>';
				        $('#product_placeholder_row').before(productRowHTML);
				        updateTotalAmount();
				        $product.attr('data-added-to-slot', 'true');
				        storeAddedProductInLocalStorage(partnerId, uniqueSlotId, lineId, productId, productName, quantity, uom, price);
				    }
                    // localStorage.clear()
			        
			       
			    }
			    

		    });
        }
	});
});









