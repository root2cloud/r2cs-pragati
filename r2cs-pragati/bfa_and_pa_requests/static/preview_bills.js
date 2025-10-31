odoo.define('bfa_and_pa_requests.payment_advice_form', function (require) {
    "use strict";

    
    var ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                var openPdfViewerButton = $('<button>', {
                    class: 'btn btn-primary oe_highlight',
                    text: 'Open PDF',
                });
                openPdfViewerButton.appendTo(this.$buttons);
                openPdfViewerButton.on('click', function () {
                    self.do_action(self._getActionOpenPDF());
                });
            }
        },

        _getActionOpenPDF: function () {
            return {
                type: 'ir.actions.act_url',
                url: '/web/content/?model=' + this.modelName + '&id=' + this.res_id + '&field=original_bills',
                target: 'new',
            };
        },
    });

    // var ListController = require('web.ListController');
    // var session = require('web.session');

    // ListController.include({
    //     renderButtons: function ($node) {
    //         this._super.apply(this, arguments);
    //         if (this.$buttons) {
    //             var self = this;
    //             var openPdfViewerButton = $('<button>', {
    //                 class: 'btn btn-primary oe_highlight',
    //                 text: 'Open PDF',
    //             });
    //             openPdfViewerButton.appendTo(this.$buttons);
    //             openPdfViewerButton.on('click', function () {
    //                 self._fetchOriginalBillFilename().then(function (filename) {
    //                     if (filename) {
    //                         self.do_action({
    //                             type: 'ir.actions.act_url',
    //                             url: '/web/content/' + self.modelName + '/' + self.res_id + '/original_bills?download=true',
    //                             target: 'new',
    //                         });
    //                     } else {
    //                         alert('Filename not available.');
    //                     }
    //                 });
    //             });
    //         }
    //     },

    //     _fetchOriginalBillFilename: function () {
    //         return this._rpc({
    //             model: this.modelName,
    //             method: 'read',
    //             args: [[this.res_id], ['original_bills_filename']],
    //         }).then(function (result) {
    //             if (result && result.length > 0 && result[0].original_bills_filename) {
    //                 return result[0].original_bills_filename;
    //             }
    //             return false;
    //         });
    //     },
    // });

});


document.querySelector('.action_approve').addEventListener('click', function() {
    // Simulate click event on o_ActivityMarkDonePopoverContent_doneButton
    document.querySelector('.o_ActivityMarkDonePopoverContent_doneButton').click();
});
