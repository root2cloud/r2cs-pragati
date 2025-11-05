$(document).ready(function() {
    $('.add-to-cart').click(function() {
        var productId = $(this).data('product-id');
        var selectedQuantity = parseFloat($('#quantity-input-' + productId).val());
        var priceCategory = $(this).data('price-category');
        var maxQuantity = getMaxQuantityByCategory(priceCategory); // Function to get max quantity

        if (selectedQuantity > maxQuantity) {
            alert('Quantity limit exceeded for this category.');
            return false; // Prevent adding to cart
        }
    });

    function getMaxQuantityByCategory(category) {
        // Logic to retrieve the maximum allowed quantity for the given category.
        // You can implement this function as needed.
        if (category === '100rs') {
            return 1; // 1 kg limit for 100rs category
        } else if (category === '80rs') {
            return 1; // 1 kg limit for 80rs category
        } else if (category === '60rs') {
            return 1; // 1 kg limit for 60rs category
        } else {
            return 0; // Default case
        }
    }
});
