odoo.define('membership_module.slot_deadline_popup', function (require) {
    var core = require('web.core');
    var _t = core._t;
    var ajax = require('web.ajax');
    var session = require('web.session');
    var QWeb = core.qweb;

    $(document).ready(function() {
        // AJAX request to check if the slot is available
        ajax.jsonRpc('/slot/detail/<slot_id>/<unique_slot_id>', 'call', {})
            .then(function(response) {
                // Check if the response contains a message
                if (response.message) {
                    // Display the message as a popup
                    alert(response.message);
                    // You can also use a modal popup or any other method to display the message
                }
        });
        
    });
})