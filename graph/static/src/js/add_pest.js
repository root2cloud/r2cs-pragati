
odoo.define('graph.add_pest', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var qweb = core.qweb;
    var Dialog = require('web.Dialog');

    var _t = core._t;

    function updatePestBedIds(cropId) {
        if (!cropId || isNaN(parseInt(cropId))) {
            console.error('Invalid crop ID:', cropId);
            return;
        }
        ajax.jsonRpc('/fetch_pest_bed_ids', 'call', {
            'crop_id': cropId,
        }).then(function(response) {
            console.log("OOOOOOOOOOOOOO",response)
            if (response) {
                var bedIds = response.join(','); 
                $('#pest_bed').val(bedIds);
            } else {
                $('#pest_bed').val('');
            }
        })
    }

    $(document).ready(function(){
	    $('#add-pest').click(function(){
	    	var greenhouse =$(this).data('greenhousename')
            console.log("kkkkkkkkkkkk",greenhouse)
            var zoneId = $(this).data('zonename')
            window.location.href = '/' + greenhouse + '/' + zoneId + '/adding-pest';

	        
	    });
	    $('#crop_id').on('change', function() {
	        var selectedCropId = $(this).val();
	        updatePestBedIds(selectedCropId);
	    });
	});

});
