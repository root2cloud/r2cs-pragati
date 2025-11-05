odoo.define('membership_module.membership_plans_fetch_data', function (require) {
    'use strict';

    var ajax = require('web.ajax');

    var fetchSlotData = function (slotId, successCallback, errorCallback) {
        ajax.jsonRpc("/membership_module/fetch_slot_data", 'call', {
            slot_id: parseInt(slotId),
        }).then(function (data) {
            if (data && data.id !== null && data.slot_name !== false) {
                console.log(data)
                successCallback(data);
            } else {
                errorCallback('Invalid data fetched: ' + JSON.stringify(data));
            }
        }).catch(function (error) {
            errorCallback('Error fetching slot data: ' + JSON.stringify(error));
        });
    };

    return {
        fetchSlotData: fetchSlotData,
    };
});