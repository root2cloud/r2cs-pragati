$(document).ready(function () { 

    var acs_doc_id = $("input[name='acs_doc_id']").val();
    var acs_home_action = $("input[name='acs_home_action']").val();
    
    // Image editor
    var imageEditor = new tui.ImageEditor('#tui-image-editor-container', {
        includeUI: {
            loadImage: {
                path: '/web/content/' + acs_doc_id,
                name: 'Image',
            },
            theme: whiteTheme, // or whiteTheme blackTheme
            initMenu: 'draw',
            menuBarPosition: 'right',
        },
        cssMaxWidth: 700,
        cssMaxHeight: 700,
        usageStatistics: false,
    });
    window.onresize = function () {
        imageEditor.ui.resizeEditor();
    };

    //replace Download image to save
    $('.tui-image-editor-header-buttons .tui-image-editor-download-btn').replaceWith('<button class="tui-image-editor-save-btn" id="ACSdoSaveFile">Save</button>');
    $('.tui-image-editor-header-logo').replaceWith("<a href='" + acs_home_action + "' id='AcsReturnAction' class='ml16'><img src='/acs_hms_body_chart/static/src/js/home-icon.jpeg' width='45' height='auto'><i class='fa fa-home mr-1 fa-3x'/></a>");

    // LISTEN TO THE CLICK AND SEND VIA AJAX TO THE SERVER
    $('#ACSdoSaveFile').on('click', function (e) {
        //SEND TO SERVER
        var image_data = imageEditor.toDataURL();
        $.ajax({
            url: '/my/acs/image/' + acs_doc_id, // upload url
            method: "POST",
            data: imageEditor.toDataURL(),
            cache : false,
            processData: false
        }).done(function(response) {
            var link = document.getElementById('AcsReturnAction');
            link.click();
        });
        return false;
    });

});