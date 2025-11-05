odoo.ksExtraAccountFilterSearch = function(input) {
    var filter = input.value.toUpperCase();
    var items = input.parentNode.querySelectorAll('.ks-extra-account-item');
    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        if (item.textContent.toUpperCase().indexOf(filter) > -1) {
            item.style.display = "";
        } else {
            item.style.display = "none";
        }
    }
};