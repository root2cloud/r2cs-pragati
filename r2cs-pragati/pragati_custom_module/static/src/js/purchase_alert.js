odoo.define('pragati_custom_module.display_alert', function (require) {
    "use strict";

    var core = require('web.core');
    var _t = core._t;

    var DisplayAlert = core.Class.extend({
        init: function () {
            var self = this;
            this.actions = {
                display_alert: function () {
                    self.displayAlert();
                },
            };
        },

        displayAlert: function () {
            var message = "The 'Submit' button has been clicked.";
            alert(message);
        },
    });

    core.action_registry.add('display_alert', DisplayAlert);

    return DisplayAlert;
});
