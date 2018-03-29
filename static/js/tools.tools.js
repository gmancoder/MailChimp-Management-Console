$(document).ready(function() {
    $('#move_objects_button').hide();
    $('#import_objects_button').hide();
    $('#export_objects_button').hide();
    $('#delete_objects_button').hide();
    if($('#tools_table').length > 0) {
        
        $('#tools_table').DataTable({
            "scrollX": true,
            "scrollY": '50vh',
            "scrollCollapse": true,
            "searching": false,
            "paging": false,
            "ordering": false,
            "lengthChange": false,
            "info": false,    
        });
    }
    else if($('#settings_table').length > 0) {
        SettingsTableInit();
    }

    
});

function ChangeForm(id) {
    if(id == 'form')
    {
        $('#save_tool_form').show();
        $('#setting_tool_form').hide();
    }
    else {
        $('#save_tool_form').hide();
        $('#setting_tool_form').show();
    }
}

function SettingsTableInit()
{
    var settings_table = $('#settings_table').DataTable({
        order: [[0, "asc"]],
        columns: [
        null,
        null,
        null,
        {'orderable': false}
        ]
    });

    _AppendDataTable(settings_table, 'settings_table');
}

function AddSetting() {
    $('#tool_setting_modal').modal('show');
}

function SaveSetting() {
    $('#tool_setting_modal_form').hide();
    $('#tool_setting_modal_loading').show();
    $('#tool_setting_modal_loading_action').html('Adding Setting');

    var tool_id = $('#tool_id').val();
    var key = $('#key').val();
    var value = $('#value').val();
    var brand = $('#brand_id').val();

    var data = {'brand': brand, 'tool_id': tool_id, 'key': key, 'value': value};
    var url = '/api/tool_settings/add';
    var method = 'POST';
    AjaxCall(url, data, method, SaveSettingSuccess, SaveSettingError);
}

function SaveSettingSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        _DestroyDataTable('settings_table');

        var results = obj.Results;
        for(var idx = 0; idx < results.length; idx ++) {
            var result = results[idx];
            var row = '<tr id="' + result.id + '"><td>' + result.key + '</td>' + 
                '<td>' + result.value + '</td>' + 
                '<td>' + result.updated + '</td>' + 
                '<td align="center"><a href="javascript:;" onClick="DeleteSetting(' + result.id + ');" class="btn btn-xs btn-danger">Delete</a></td>' + 
                '</tr>';
            $('#settings_table_body').append(row);
        }

        SettingsTableInit();
        $('#tool_setting_modal_form').show();
        $('#tool_setting_modal_loading').hide();
        $('#tool_setting_modal').modal('hide');
    }
    else {
        alert(HandleErrors(obj));
        $('#tool_setting_modal_form').show();
        $('#tool_setting_modal_loading').hide();
    }
}

function SaveSettingError(msg) {
    alert(msg);
    $('#tool_setting_modal_form').show();
    $('#tool_setting_modal_loading').hide();
}

function DeleteSetting(id) {
    var conf = confirm('Are you sure?');
    if(!conf) {
        return false;
    }
    var brand = $('#brand_id').val();

    var data = {'brand': brand, 'id': id};
    var url = '/api/tool_settings/delete';
    var method = 'POST';
    AjaxCall(url, data, method, DeleteSettingSuccess, DeleteSettingError);
}

function DeleteSettingSuccess(msg) {
    obj = JSON.parse(msg);
    if(obj.Status == "OK") {
        var id = obj.Results.ID;
        _DestroyOnlyDataTable('settings_table');
        $('#settings_table_body #' + id).remove();
        SettingsTableInit();
    }
    else {
        alert(HandleErrors(obj));
    }
}

function DeleteSettingError(msg) {
    alert(msg);
}