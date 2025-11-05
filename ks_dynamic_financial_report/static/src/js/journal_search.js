odoo.ksJournalFilterSearch = function(input) {
    var filter = input.value.toUpperCase();
    var list = input.parentNode.querySelectorAll(".ks-journal-item");
    for (var i = 0; i < list.length; i++) {
        var item = list[i];
        if (item.textContent.toUpperCase().indexOf(filter) > -1) {
            item.style.display = "";
        } else {
            item.style.display = "none";
        }
    }
};