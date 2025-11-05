// odoo.define('membership_module.custom_membership', function (require) {
//     'use strict';

//     var core = require('web.core');
//     var _t = core._t;
//     var rpc = require('web.rpc');
//     var Dialog = require('web.Dialog');

//     function onClickBuyButton(planningId, planName,membershipId) {
//         rpc.query({
//             model: 'membership.planning',
//             method: 'search_read',
//             domain: [['id', '=', planningId]],
//             fields: ['plan_name','membership_id'],
//         }).then(function (result) {
//             console.log(result)
//             if (result.length > 0) {
//                 var selectedPlanName = result[0].plan_name;
//                 var selectedMembershipId = result[0].membership_id[0].toString() ;

       

//                 if (selectedPlanName === planName && selectedMembershipId === membershipId) {
//                     console.log("runnnn")
//                     rpc.query({
//                         route: '/custom/buy_plan',
//                         params: {
//                             planning_id: planningId,
//                             plan_name: planName,
//                             membership_id: membershipId,
//                         },
//                     }).then(function (response) {
//                         if (response.success) {
//                             window.location.href = '/shop/cart';
//                         } else {
//                             console.error(response.message);
//                         }
//                     });
//                 } else {
//                     console.error('Selected plan does not match.');
//                 }
//             } else {
//                 console.error('Plan not found.');
//             }
//         });
        
//      }

//     window.onClickBuyButton = onClickBuyButton;

// });
// *********************************************************************************

odoo.define('membership_module.custom_membership', function (require) {
    'use strict';

    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');

    function onClickBuyButton(planningId, planName, membershipId) {
        rpc.query({
            model: 'membership.planning',
            method: 'search_read',
            domain: [['id', '=', planningId]],
            fields: ['plan_name', 'membership_id'],
        }).then(function (result) {
            if (result.length > 0) {
                var selectedPlanName = result[0].plan_name;
                var selectedMembershipId = result[0].membership_id[0].toString();

                if (selectedPlanName === planName && selectedMembershipId === membershipId) {
                    rpc.query({
                        route: '/custom/buy_plan',
                        params: {
                            planning_id: planningId,
                            plan_name: planName,
                            membership_id: membershipId,
                        },
                    }).then(function (response) {
                        if (response.success) {
                            
                            // Check if the current URL is already '/shop/cart' to avoid unnecessary redirection
                            console.log('yewwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww',response.success)
                            // if (window.location.pathname !== '/shop/cart') {
                            //     console.log('yewwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww')
                            //     window.location.href = '/shop/cart';
                            // }
                        } else {
                            console.error(response.message);
                        }
                    });
                } else {
                    console.error('Selected plan does not match.');
                }
            } else {
                console.error('Plan not found.');
            }
        });
    }

    // Attach the function to the window for access in XML
    window.onClickBuyButton = onClickBuyButton;

});

