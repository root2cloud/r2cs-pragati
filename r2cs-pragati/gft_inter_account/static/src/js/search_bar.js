odoo.define('gft_inter_account.search_bar', function (require) {
    "use strict";

    $(document).ready(function() {
        console.log("Document is ready");

        // Wait for the window to load completely
        $(window).on('load', function() {
            console.log("Window loaded");

            // Delegate event handler to a parent element
            $(document).on('keyup', '#rayazorpaySearch', function () {
                console.log("Keyup event triggered");

                // Get the input value and convert to uppercase for case-insensitive comparison
                var input, filter, rows, row, i, txtValue;
                input = $(this);
                filter = input.val().toUpperCase();
                
                console.log("Number of rows found: " + filter);

                var notebook = input.closest('.o_notebook');
                console.log("Notebook element: ", notebook);
                
                rows = notebook.find('table tbody tr.o_data_row');
                console.log("Number of rows found: " + rows.length);
                // console.log("Number of rows found: " + rows);

                for (i = 0; i < rows.length; i++) {
                    row = $(rows[i]);
                    var match = false;
                    // txtValue = row.find("td[name='customer_name']").text().toUpperCase();
                    // console.log(txtValue)
                    row.find('td').each(function() {
                        var cellText = $(this).text().toUpperCase();
                        if (cellText.indexOf(filter) > -1) {
                            match = true;
                            return false; // Break the loop
                        }
                    });
                    if (match) {
                        row.show();
                    } else {
                        row.hide();
                    }
                    // if (txtValue.indexOf(filter) > -1) {
                    //     row.show();
                    // } else {
                    //     row.hide();
                    // }
                }
            });
        });
    });
});