$(document).ready(function() {
    $('#import_objects_button').hide();
    $('#export_objects_button').hide();
    $('#search_objects_button').hide();
    if($('#imports_table').length > 0) {
        
        $('#imports_table').DataTable({
            "scrollX": true,
            "scrollY": '50vh',
            "scrollCollapse": true,
            "searching": false,
            "paging": false,
            "ordering": false,
            "lengthChange": false,
            "info": false,    
        });

        $('#start_import_button').click(StartImportClicked);
    }
});

function ToolButtonCheck() {
    DisableButton('start_import_button');
    var cnt = ListCheckCount('imports');
    if(cnt == 1)
    {
        AbleButton('start_import_button');
    }
}

function StartImportClicked()
{
    var brand = $('#brand_id').val();
    var checked = CheckedRows('imports');
    if(checked.length != 1)
    {
        StartImportError('Only 1 Import Definition can be selected at a time');
    }
    var item = checked[0];

    var url = "/api/imports/start";
    var data = {'brand': brand, 'id': item}
    var method = "POST";

    DisableButton('start_import_button');
    AjaxCall(url, data, method, StartImportSuccess, StartImportError);
}

function StartImportSuccess(msg) {
    obj = JSON.parse(msg);
    if(obj.Status == "OK") {
        alert('Import started');
    }
    else {
        alert(HandleErrors(obj));
    }
    ToolButtonCheck();
}

function StartImportError(msg) {
    alert(msg);
    ToolButtonCheck();
}

function TargetTypeChanged() {
    $('.target_type_group').hide();
    $('.target_folders_ul').hide();
    var type = $('#target_type').val();
    if(type == 'lists' || type == 'template_categories') {
        $('#target_folder_group').show();
        if(type == 'lists') {
            $('#target_folders_lists').show();
        }
        else {
            $('#target_folders_template_categories').show();
        }
    }
    else if(type == 'subscribers') {
        $('#target_lists_group').show();
    }
}