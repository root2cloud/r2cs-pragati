odoo.define('my_zip_loc.zip_code', function (require) {
    'use strict';

    var ajax = require('web.ajax');

    $(document).ready(function () {
        ajax.jsonRpc("/get_zip_codes", 'call', {}).then(function (data) {
            var select = document.getElementById("zip_code");
            if (select) {
                for (var i = 0; i < data.length; i++) {
                    var opt = data[i].zip_field + " - " + data[i].location_field;
                    var el = document.createElement("option");
                    el.textContent = opt;
                    el.value = opt;
                    select.appendChild(el);
                }
            } else {
                console.log('Element with id "zip_code" not found');
            }
        });
    });
});
