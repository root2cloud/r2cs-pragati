//odoo.define('ks_general_ledger.add_accounts', function (require) {
//    'use strict';
//
//    var rpc = require('web.rpc');
//
//    // Trigger when the report table is inserted into the DOM
//    $(document).on('DOMNodeInserted', function(e) {
//        if ($(e.target).find('.ks_py-mline-table-div').length > 0) {
//            addAllAccountsColumn();
//        }
//    });
//
//    function addAllAccountsColumn() {
//        // Skip initial balance rows, only process transaction rows
//        var $rows = $('.ks_py-mline-table-div tbody tr:not(.ks-initial-bal-row)');
//        var moveIds = [];
//        var rowData = [];
//
//        $rows.each(function() {
//            var moveId = $(this).data('move-id');
//            var currentAccountId = $(this).data('account-id');
//
//            if (moveId) {
//                moveIds.push(moveId);
//                rowData.push({
//                    row: $(this),
//                    moveId: moveId,
//                    accountId: currentAccountId
//                });
//            }
//        });
//
//        if (moveIds.length === 0) return;
//
//        // Fetch balancing lines
//        rpc.query({
//            model: 'account.move.line',
//            method: 'search_read',
//            domain: [['move_id', 'in', moveIds]],
//            fields: ['move_id', 'account_id', 'debit', 'credit'],
//        }).then(function(lines) {
//            var accountsByMove = {};
//
//            lines.forEach(function(line) {
//                if (!line.account_id) return;
//
//                var mid = line.move_id[0];
//                if (!accountsByMove[mid]) accountsByMove[mid] = [];
//
//                var accountId = line.account_id[0];
//                var accountName = line.account_id[1];
//
//                // STRIP ACCOUNT CODE: Removes numbers and dashes from the start
//                var cleanName = accountName.replace(/^\d+\s*-?\s*/, '').trim();
//
//                var debit = line.debit || 0;
//                var credit = line.credit || 0;
//                var info = cleanName;
//
//                if (debit > 0) {
//                    info += ' (Dr: ₹ ' + debit.toLocaleString('en-IN', {minimumFractionDigits: 2}) + ')';
//                } else if (credit > 0) {
//                    info += ' (Cr: ₹ ' + credit.toLocaleString('en-IN', {minimumFractionDigits: 2}) + ')';
//                }
//
//                accountsByMove[mid].push({
//                    id: accountId,
//                    name: cleanName,
//                    display: info
//                });
//            });
//
//            // Update the UI
//            rowData.forEach(function(item) {
//                var list = accountsByMove[item.moveId] || [];
//
//                // 1. Exclude the current account from the opposite list
//                var filtered = list.filter(function(acc) {
//                    return acc.id !== item.accountId;
//                });
//
//                // 2. Remove duplicate entries for the same account
//                var seen = {};
//                var unique = [];
//                filtered.forEach(function(acc) {
//                    if (!seen[acc.name]) {
//                        seen[acc.name] = true;
//                        unique.push(acc);
//                    }
//                });
//
//                // 3. Inject the HTML into the cell using the class selector
//                var finalHtml = unique.map(a => a.display).join('<br/>');
//                item.row.find('.all-accounts-cell').html(finalHtml || '-');
//            });
//        });
//    }
//});