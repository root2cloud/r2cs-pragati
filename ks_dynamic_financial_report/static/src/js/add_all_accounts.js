odoo.define('ks_general_ledger.add_accounts', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var rpc = require('web.rpc');

    // Hook into the report rendering
    $(document).on('DOMNodeInserted', function(e) {
        if ($(e.target).find('.ks_py-mline-table-div').length > 0) {
            addAllAccountsColumn();
        }
    });

    function addAllAccountsColumn() {
        var $rows = $('.ks_py-mline-table-div tbody tr');
        var moveIds = [];
        var rowData = [];

        // Collect move IDs from rows
        $rows.each(function() {
            var $dropdown = $(this).find('[data-bs-move-id]');
            if ($dropdown.length > 0) {
                var moveId = parseInt($dropdown.attr('data-bs-move-id'));
                if (moveId) {
                    moveIds.push(moveId);
                    rowData.push({
                        row: $(this),
                        moveId: moveId
                    });
                }
            }
        });

        if (moveIds.length === 0) return;

        // Fetch all accounts with debit/credit using RPC
        rpc.query({
            model: 'account.move.line',
            method: 'search_read',
            domain: [['move_id', 'in', moveIds]],
            fields: ['move_id', 'account_id', 'debit', 'credit'],  // ✅ ADDED debit, credit
        }).then(function(lines) {
            // Group accounts by move_id
            var accountsByMove = {};
            lines.forEach(function(line) {
                var mid = line.move_id[0];
                if (!accountsByMove[mid]) {
                    accountsByMove[mid] = [];
                }

                // Get FULL account info with debit/credit
                var accountName = line.account_id[1]; // e.g. "100133 Cash Sparsh"
                var debit = line.debit || 0;
                var credit = line.credit || 0;

                // Format: "100133 Cash Sparsh (Dr: 1,488.33)"
                var accountInfo = accountName;
                if (debit > 0) {
                    accountInfo += ' (Dr: ' + debit.toFixed(2) + ')';
                } else if (credit > 0) {
                    accountInfo += ' (Cr: ' + credit.toFixed(2) + ')';
                }

                accountsByMove[mid].push({
                    name: accountName,
                    fullInfo: accountInfo,
                    code: accountName.split(' ')[0]
                });
            });

            // Add accounts to each row
            rowData.forEach(function(item) {
                var accounts = accountsByMove[item.moveId] || [];

                // Sort by account code
                accounts.sort(function(a, b) {
                    return a.code.localeCompare(b.code);
                });

                // Join the full info
                var accountsStr = accounts.map(function(acc) {
                    return acc.fullInfo;
                }).join(', ');

                // Find the "All Accounts" cell and populate it
                var $allAccountsCell = item.row.find('td').eq(6); // 7th column
                $allAccountsCell.text(accountsStr);
            });
        });
    }
});
