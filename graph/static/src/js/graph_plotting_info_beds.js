odoo.define('graph.get_bed_info', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');


    $(document).ready(function () {

        function removeModal() {
            $('.my-modal').remove();
        }


        function displayBedsNoCropPlanningInfo(bedName) {
            removeModal();
            var modalHtml = `
            <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="my-modal-content">
                        <div class="my-modal-body">
                            ${bedName} Is Empty
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the modal HTML to the body
        $('body').append(modalHtml);

        // Show the modal
        $('#errorModal').modal('show');
    }



        function displayBedsCropPlanningInfo(cropName,sowingDate,landPrepareDate,cropEndDate,harvestDate,totalGainOutput) {
            removeModal();
            var modalHtml = `
            <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="my-modal-content">
                        <div class="my-modal-body">
                            <p>Crop Name : ${cropName}</p>
                            <p>Sowing Date : ${sowingDate}</p>
                            <p>Land Prepare Date : ${landPrepareDate}</p>
                            <p>Crop End Date : ${cropEndDate}</p>
                            <p>Harvest Date : ${harvestDate}</p>
                            <p>Total Gain Output(Kg's): ${totalGainOutput}</p>

                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the modal HTML to the body
        $('body').append(modalHtml);

        // Show the modal
        $('#errorModal').modal('show');
    }

        function displayBedsCancelCropPlanningInfo(cropName){
            removeModal();
            var modalHtml = `
            <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="my-modal-content">
                        <div class="my-modal-body">
                            <p>${cropName} Crop Is Cancelled</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the modal HTML to the body
        $('body').append(modalHtml);

        // Show the modal
        $('#errorModal').modal('show');

    }

        function displayBedsNoMenureInfo(cropName){
            removeModal();
            var modalHtml = `
            <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="my-modal-content">
                        <div class="my-modal-body">
                            <p>No Menure Available For ${cropName} Crop </p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the modal HTML to the body
        $('body').append(modalHtml);

        // Show the modal
        $('#errorModal').modal('show');

    }

        function displayBedsCancelMenureInfo(cropName){
            removeModal();
            var modalHtml = `
            <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="my-modal-content">
                        <div class="my-modal-body">
                            <p>${cropName} Crop Is Cancelled </p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the modal HTML to the body
        $('body').append(modalHtml);

        // Show the modal
        $('#errorModal').modal('show');

    }

        function displayBedsNoCropMenureInfo(bedName){
            removeModal();
            var modalHtml = `
            <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="my-modal-content">
                        <div class="my-modal-body">
                            <p>No Crop In Bed ${bedName} </p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the modal HTML to the body
        $('body').append(modalHtml);

        // Show the modal
        $('#errorModal').modal('show');

    }

        function displayBedsMenureInfo(menureNames, menureQuantities, cropNameMenure) {
            removeModal();
            var modalHtml = `
                <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                    <div class="modal-dialog" role="document">
                        <div class="my-modal-content">
                            <div class="my-modal-body">
                                <p>Crop Name: ${cropNameMenure[0]}</p>
                                <ol>
            `;

            // Iterate over each menure item
            for (var i = 0; i < menureNames.length; i++) {
                modalHtml += `
                    <li>
                        <p>Menure: ${menureNames[i]}</p>
                        <p>Quantity(Kg's): ${menureQuantities[i]}</p>
                    </li>
                `;
            }

            modalHtml += `
                                </ol>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Append the modal HTML to the body
            $('body').append(modalHtml);

            // Show the modal
            $('#errorModal').modal('show');
        }



        function displayBedsNoPestInfo(cropName){
            removeModal();
            var modalHtml = `
            <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="my-modal-content">
                        <div class="my-modal-body">
                            <p>No Pest Available For ${cropName} Crop </p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the modal HTML to the body
        $('body').append(modalHtml);

        // Show the modal
        $('#errorModal').modal('show');

    }

        function displayBedsCancelPestInfo(cropName){
            removeModal();
            var modalHtml = `
            <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="my-modal-content">
                        <div class="my-modal-body">
                            <p>${cropName} Crop Is Cancelled </p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the modal HTML to the body
        $('body').append(modalHtml);

        // Show the modal
        $('#errorModal').modal('show');

    }

        function displayBedsNoCropPestInfo(bedName){
            removeModal();
            var modalHtml = `
            <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="my-modal-content">
                        <div class="my-modal-body">
                            <p>No Crop In Bed ${bedName} </p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the modal HTML to the body
        $('body').append(modalHtml);

        // Show the modal
        $('#errorModal').modal('show');

    }
        function displayBedsPestInfo(cropNamesPest, pestNames, diseaseNames, pestQuantities) {
            removeModal();
            var modalHtml = `
                <div class="my-modal fade" id="errorModal" tabindex="-1" role="dialog" aria-labelledby="errorModalLabel" aria-hidden="true">
                    <div class="modal-dialog" role="document">
                        <div class="my-modal-content">
                            <div class="my-modal-body">
                                <p>Crop Name: ${cropNamesPest[0]}</p>
                                <ol>
            `;

            // Iterate over each pest record
            for (var i = 0; i < cropNamesPest.length; i++) {
                modalHtml += `
                    <li>
                        <p>Pest Name: ${pestNames[i]}</p>
                        <p>Disease Name: ${diseaseNames[i]}</p>
                        <p>Pest Quantity(Kg's): ${pestQuantities[i]}</p>
                    </li>
                `;
            }

            modalHtml += `
                                </ol>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Append the modal HTML to the body
            $('body').append(modalHtml);

            // Show the modal
            $('#errorModal').modal('show');
        }



        function setBedItemBackgroundColors() {
            var currentPath = window.location.pathname;
            if (currentPath.endsWith('/crop-planning')) {
                $('.bed-item').each(function() {
                    var bedState = $(this).data('bedstate');
                    console.log("SSSSSSSSSSSSSSS",bedState)

                    var backgroundColor;

                    // Set background color based on bed_state value
                    switch (bedState) {
                        case 'draft':
                            backgroundColor = '#03131f';
                            break;
                        case 'confirm':
                            backgroundColor = '#f58d42';
                            break;
                        case 'execute':
                            backgroundColor = '#06c40c';
                            break;
                        case 'complete':
                            backgroundColor = '#1d7cc4';
                            break;                    
                        case 'cancel':
                            backgroundColor = '#f50905';
                            break;
                        default:
                            backgroundColor = 'grey';
                            // Default color
                    }
                    $(this).css('background-color', backgroundColor);
                });
            }



            if(currentPath.endsWith('/menure')){
                console.log("yess color menure",$(this).data('menurestate'))
                $('.bed-item').each(function(){
                    var bedMenure = $(this).data('menurestate');
                    var bedCrop = $(this).data('cropname');

                    console.log("FFFFFFFF",bedMenure)
                    var backgroundColor;


                    if(bedMenure !== undefined && 
                        bedCrop !== undefined){
                        backgroundColor = '#aa4008';

                    }else if(bedMenure === undefined && bedCrop !== undefined){
                        backgroundColor = '#529d25';
                    }else{
                        backgroundColor = '#585e32';

                    }
                    $(this).css({
                        'background-color': backgroundColor,
                    });
                });
            }
            if(currentPath.endsWith('/pest')){
                console.log("yess color pest",$(this).data('peststate'))
                $('.bed-item').each(function(){
                    var bedPest = $(this).data('peststate');
                    var bedCrop = $(this).data('cropname');
                    console.log("FFFFFFFF",bedPest)
                    var backgroundColor;

                    if(bedPest !== undefined && bedCrop !== undefined){
                        backgroundColor = '#ad0a1b';

                    }else if(bedPest === undefined && bedCrop !== undefined){
                        backgroundColor = '#529d25';
                    }else if(bedPest === 'cancel' ){
                        backgroundColor = 'red';

                    }
                    else{
                        backgroundColor = '#585e32';

                    }
                    $(this).css('background-color', backgroundColor);
                });
            }
        }
        setBedItemBackgroundColors();


        
        function bedCropMenurePestInfo(event) {
            var selectedOption = $('#filterSelect').val();
            var currentPath = window.location.pathname;
           
            console.log("Clicked bed-box container");
            var bedBox = $(this); 
            var bedName = $(this).data('bedname');
            var bedId = $(this).data('bedid');  
            var cropName = $(this).data('cropname');
            var zoneName = $(this).data('zonename');
            var greenhouseName = $(this).data('greenhousename');
            
            var bedState = $(this).data('bedstate');
            console.log("XXXXXXXXXXX", bedName, cropName,zoneName,greenhouseName);
            $('.beds-info-popup').remove();

            // **********************trial***********************
            if (currentPath.endsWith('/crop-planning')) {
                console.log("yessss crop-planning")
                // Your existing code for crop planning
                ajax.jsonRpc('/get_bed_info', 'call', {
                    'bed_name': bedName,
                    'bed_id':bedId,
                    'crop_name': cropName,
                }).then(function (response) {
                    console.log("Response from server:", response);
                    if ($.isEmptyObject(response)) {
                        console.error("Error: Empty response received");
                        displayBedsNoCropPlanningInfo(bedName)
                    }                   
                    else {
                        if (bedState == 'draft' || bedState == 'confirm' || bedState == 'execute'){
                            console.log("SSSSSSSSSSSSSS",bedState)

                            var cropName = response.crop_name;
                            var sowingDate = response.sowing_date;
                            var landPrepareDate = response.land_prepare_date;
                            var cropEndDate = response.crop_end_date;
                            var harvestDate = response.harvest_date;
                            var totalGainOutput = response.total_gain_output;

                            displayBedsCropPlanningInfo(cropName,sowingDate,landPrepareDate,cropEndDate,harvestDate,totalGainOutput)

                        }
                        else if(bedState =='cancel'){
                            var cropName = response.crop_name;

                            displayBedsCancelCropPlanningInfo(cropName)
                        }
                       
                    }
                        // Handle response
                }).guardedCatch(function (error) {
                    console.error("Error:", error);
                });

            }



            // ************************menure************************
            if (currentPath.endsWith('/menure')) {
                console.log("yessss menure")
                ajax.jsonRpc('/get_menure_info', 'call', {
                    'bed_name': bedName,
                    'zone_name':zoneName,
                    'greenhouse_name':greenhouseName,
                    
                    'crop_name': cropName,
                    
                    
                }).then(function (menureResponse) {
                        
                    console.log("Menure Response:", menureResponse);

                    if ($.isEmptyObject(menureResponse)) {
                        console.error("Error: Empty response received");
                        if(cropName ){
                            if(bedState !== 'cancel'){
                                console.log("SSSSSSSSSSSSSS",bedState)
                                displayBedsNoMenureInfo(cropName)

                            }else{
                                console.log("SSSSSSSSSSSSSS",bedState)
                                displayBedsCancelMenureInfo(cropName)

                            }
                            
                        }else if (!cropName ){
                            if(bedState !== 'cancel'){
                                console.log("SSSSSSSSSSSSSSS",bedState)
                                displayBedsNoCropMenureInfo(bedName)

                            }
                        }
                    }
                        
                    else{
                        if(bedState == 'draft' || bedState == 'confirm' || bedState == 'harvest' || bedState == 'growing'){
                            console.log("PPPPPPPPPPPPPPPPPPPPPPPP",bedState)

                            if (Array.isArray(menureResponse) && menureResponse.length > 0) {
                                // Accumulate data from all records
                                var menureNames = [];
                                var menureQuantities = [];
                                var cropNamesMenure = [];

                                menureResponse.forEach(function (menureRecord) {
                                    menureNames.push(menureRecord.product_id_menure);
                                    menureQuantities.push(menureRecord.stock_change_menure);
                                    cropNamesMenure.push(menureRecord.crop_name_in_menure);
                                });

                                // Display menure information for all records
                                displayBedsMenureInfo(menureNames, menureQuantities, cropNamesMenure);
                            }

                        }
                    }     

                }).guardedCatch(function (error) {
                    console.error("Error:", error);
                    
                });
            }

            // ************************pest*************************
            if (currentPath.endsWith('/pest')) {
                console.log("yessss pest")
                ajax.jsonRpc('/get_pest_info', 'call', {
                    'bed_name': bedName,
                    'zone_name':zoneName,
                    'greenhouse_name':greenhouseName,
                    
                    'crop_name': cropName,
                }).then(function (pestResponse) {
                    
                    console.log("Pest Response:", pestResponse);

                    if ($.isEmptyObject(pestResponse)) {
                        console.error("Error: Empty response received");
                        if(cropName ){
                            if(bedState !== 'cancel'){
                                console.log("SSSSSSSSSSSSSS",bedState)
                                displayBedsNoPestInfo(cropName)

                            }else{
                                console.log("SSSSSSSSSSSSSS",bedState)
                                displayBedsCancelPestInfo(cropName)

                            }
                            
                        }else if (!cropName ){
                            if(bedState !== 'cancel'){
                                console.log("SSSSSSSSSSSSSSS",bedState)
                                displayBedsNoCropPestInfo(bedName)

                            }
                        }
                    }
                        
                    else{
                        if(bedState == 'draft' || bedState == 'confirm' || bedState == 'harvest' || bedState == 'growing'){
                            console.log("PPPPPPPPPPPPPPPPPPPPPPPP",bedState)

                            if (Array.isArray(pestResponse) && pestResponse.length > 0) {
                                var cropNamesPest = [];
                                var pestNames = [];
                                var diseaseNames = [];
                                var pestQuantities = [];
                                console.log("vvvvvvvvvvvvv",cropNamesPest,pestNames,diseaseNames,pestQuantities)

                                pestResponse.forEach(function (pestRecord) {
                                    cropNamesPest.push(pestRecord.crop_name_in_pest);
                                    pestNames.push(pestRecord.product_id_pest);
                                    diseaseNames.push(pestRecord.disease);
                                    pestQuantities.push(pestRecord.stock_change_pest);
                                });

                                displayBedsPestInfo(cropNamesPest, pestNames, diseaseNames, pestQuantities);
                            }
                            
                        }
                    }     

                }).guardedCatch(function (error) {
                    console.error("Error:", error);
                    
                });
            }

        }

        // Attach click event handler to bed-item elements
        $('.bed-item').on('click', bedCropMenurePestInfo);

        $('.bed-checkbox').on('click', function(event) {
        event.stopPropagation();
    });
    });
});
