
odoo.define('graph.add_harvest', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var qweb = core.qweb;
    var Dialog = require('web.Dialog');

    var _t = core._t;

    function updateCropId(productId, greenhouse) {
        console.log("XXXXXXXXXXXXXXXXXXX", greenhouse);
        if (!productId || isNaN(parseInt(productId))) {
            console.error('Invalid productId ID:', productId);
            return;
        }
        ajax.jsonRpc('/fetch_crop_ids', 'call', {
            'product_id': productId,
            'greenhouse': greenhouse,
        }).then(function(response) {
            console.log("OOOOOOOOOOOOOOcrop", response);
            if (response) {
                $('#crop_id').empty();
                $('#harvest_bed').val(""); 
                response.forEach(function(option) {
                    $('#crop_id').append($('<option>', {
                        value: option.value,
                        text: option.text
                    }));
                    if (option.bed_names) {
                        $('#harvest_bed').val(option.bed_names);
                    }
                });
                
                // response.forEach(function(cropId) {
                //     $('#crop_id').append($('<option>', {
                //         value: cropId,
                //         text: cropId
                //     }));
                // });
            } 

        });
    }

    

    function updateBedIds(givenCropId){
        console.log(givenCropId)
        if (!givenCropId || isNaN(parseInt(givenCropId))) {
            console.error('Invalid givenCropId ID:', givenCropId);
            return;
        }
        
        ajax.jsonRpc('/fetch_harvest_bed_ids','call',{
            'given_crop_id':givenCropId,
        }).then(function(response){
            console.log("OOOOOOOOOOOOOOOharvest",response)
            if(response){
                
                var bedIds =response.join(',');
                $('#harvest_bed').val(bedIds);
            }
        })

    }

    $(document).ready(function(){
        $('#add-harvest').click(function(){
            var greenhouse =$(this).data('greenhousename')
            var zoneId = $(this).data('zonename')
            window.location.href = '/' + greenhouse + '/' + zoneId + '/adding-daily-harvest';

           
        });
        $('#product_id').on('change', function() {
            var selectedProductId = $(this).val();
            var greenhouse = $(this).data('greenhouse'); 
            updateCropId(selectedProductId,greenhouse);
        });
        
    });


    
});
