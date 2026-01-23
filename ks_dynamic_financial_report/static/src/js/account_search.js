odoo.ksExtraAccountFilterSearch = function(input) {
    // Prevent default browser behavior
    var e = window.event || {};
    if (e.preventDefault) e.preventDefault();
    if (e.stopPropagation) e.stopPropagation();

    var filter = input.value.toUpperCase().trim();
    var $container = $(input).closest('.ks-account-filter');

    // 1. Always keep Pinned/Selected items visible
    $container.find('.selected-accounts-list .ks-account-item').show();

    // 2. Filter only the Available items
    var $availableItems = $container.find('.available-accounts-list .ks-account-item');

    if (filter === '') {
        $availableItems.show();
    } else {
        $availableItems.each(function() {
            var $item = $(this);
            var text = $item.text().toUpperCase();
            if (text.indexOf(filter) > -1) {
                $item.show();
            } else {
                $item.hide();
            }
        });
    }
    return false;
};