String.prototype.toTitleCase = function(n) {
   var s = this;
   if (1 !== n) s = s.toLowerCase();
   return s.replace(/(^|\s)[a-z]/g,function(f){return f.toUpperCase()});
}

var DEFAULT_SUBSCRIBER = 'exacttarget@solutionset.com';
var tables = [];
var table_ids = [];
var loaders = [];
var current_folder_id = 0;
var folder_not_to_delete = ['My Lists', 'Segments', 'Tracking', 'Campaigns'];
var folders_collapsed = false;
$(window).resize(ResizeWindows);
function ResizeWindows() {
    var height = window.innerHeight;
    adjust_height('folder_list_container', height, 113);
    adjust_height('form_row', height, 193);
    adjust_height('list_info_row', height, 217, 540);

    if($('#edit_html_content_modal').length == 0) {
        adjust_height('editor', height, 270);
        adjust_height('merge_tags_container', height, 270);
    }
    else {
        adjust_height('editor', height, 110);
        adjust_height('merge_tags_container', height, 110);
    }
}
function adjust_height(container, old_height, delta, min_height = -1, tag="id") {
    var pre = '#'
    if(tag != "id") {
        pre = "."
    }
    if($('.alert').length > 0) {
        delta += 75;
    }
    if($(pre + container).length > 0) {
        new_height = old_height - delta;
        if(new_height < min_height && min_height > -1) {
            new_height = min_height;
        }
        $(pre + container).css('height', new_height + 'px');
    }
}
$(document).ready(function() {
    ResizeWindows();
    $('input.sw-checkbox').bootstrapSwitch({
        size: 'small',
        onText: 'Yes',
        offText: 'No',
    });

    $('#ip_address_table').DataTable({
        order: [[0, "asc"]],
        columns: [
        null,
        null,
        {'orderable': false}
        ]
    });

    $('#folders').bind("select_node.jstree", function (e, data) {
                var href = data.node.a_attr.href
                document.location.href = href;
    }).jstree({
        "core" : {
            "multiple" : false,
            'themes': {'dots': false}
        },
        'plugins': ['changed'],
        
    });

    $.contextMenu({
    // define which elements trigger this menu
        selector: ".js-folder-context",
        // define the elements of the menu
        items: {
            "new": {name: "New Folder", icon: "create", callback: function(key, opt){ NewFolder(opt, $(this)); }},
            "rename": {name: "Rename Folder", icon: "edit", callback: function(key, opt){ Rename(opt, $(this)); }},
            "delete": {name: "Delete Folder", icon: "delete", callback: function(key, opt){ DeleteFolder(opt, $(this)); }}
        }
        // there's more, have a look at the demos and docs...
    });

    $('#move_to_folder').bind("select_node.jstree", function (e, sel_data) {
            var id = sel_data.node.id
            var name = sel_data.node.text
            console.log(sel_data);
            $('#move_to_folder_id').val(id);
            $('#move_to_folder_name').val(name);
    }).jstree({
        "core" : {
            "multiple" : false,
            'themes': {'dots': false}
        },
        'plugins': ['changed'],
        
    });

    if($('#current_folder_span').length > 0) {
        current_folder_id = $('#current_folder_span').html();
    }

    /*if($('#folder_list_container').length > 0) {
        var height = window.innerHeight;
        $('#folder_list_container').resizable({
            resize: function(event, ui) {
                var x=ui.element.outerWidth();
                var y=ui.element.outerHeight();
                var par=$(this).parent().width();
                var ele=ui.element;
                var factor = par-x - 5;
                if($('#form_container').length > 0) {
                    $('#form_container').css('width', factor + 'px');
                    adjust_height('form_container', height, 200);
                    if($('.merge_tag_button').length > 0) {
                        ResizeMergeButtonText();
                    }
                }
                else if($('#list_container').length > 0) {
                    $('#list_container').css('width', factor + 'px');
                    adjust_height('list_container', height, 200);
                }
                adjust_height('folder_list_container', height, 113);
            }
        });
    }*/
});
function GetDateAsString(today) {
    year = today.getFullYear().toString();
    month = today.getMonth() + 1;
    if(month < 10) {
        month = '0' + month.toString();
    }
    else {
        month = month.toString();
    }
    day = today.getDate();
    if(day < 10) {
        day = '0' + day.toString();
    }
    else {
        day = day.toString();
    }

    return year + month + day;
}
function SelectAll(cls)
{
    $('.' + cls).each(function() {
        if(!$(this).is(':checked'))
            {
                $(this).click();
            }
    })
}

function UnSelectAll(chk_class) {
    $('.' + chk_class).each(function() {
        if($(this).is(':checked'))
        {
            $(this).click();
        }
    });
}

function CheckConfirmPassword()
{
    var passwd = $('#password').val();
    var conf_passwd = $('#conf_password').val();

    if(passwd != conf_passwd)
    {
        alert('Password fields don\'t match');
        return false;
    }
    return true;
}

function ShowLoader(action, id) {
    if(loaders.length == 0) {
        var title = document.title;
        title = '[Busy] ' + title;
        document.title = title;
    }
    $('#' + id).show();
    $('#' + id + '_action').html(action);
    loaders.push(id);
}
function HideLoader(id)
{
    idx = loaders.indexOf(id);
    if(idx > -1) {
        loaders.splice(idx,1);
    }
    if(loaders.length == 0) {
        var title = document.title;
        title = title.replace('[Busy] ', '');
        document.title = title;
    }
    $('#' + id).hide();
}


function HandleErrors(obj) {
    errors = "";
    for(var e = 0; e < obj.Errors.length; e ++) {
        errors += obj.Errors[e].Message + "\n";
    }
    return errors;
}

function CreateDynamicOption(value, text, selected) {
    var sel = ""
    if(typeof selected !== undefined && selected != undefined) {
        sel = "selected" 
    }
    return "<option class='dynamic_option' value='" + value + "' " + sel + ">" + text + "</option>";
}
function CreateDynamicListOption(value, text) {
    return "<li class='dynamic_option' id='" + value + "'>" + text + "</li>";
}

function SingleDimArrayAsString(arr, delim) {
    var str = "";
    for(var f = 0; f < arr.length; f ++) {
        if(str != "") {
            str += "|"
        }
        str += arr[f];
    }
    return str;
}

function PopulateDataTable(field_names, data, table_id) {
    table_id = typeof table_id !== 'undefined' ? table_id : 'de_data_table';
    var columns = [];
    
    for(var f = 0; f < field_names.length; f ++) {
        columns.push({
            data: field_names[f],
            title: field_names[f]
        });
    }

    _DestroyDataTable(table_id);

    var de_table = $('#' + table_id).DataTable( {
      "destroy": true,
      "data": data,
      "columns": columns
    });

    _AppendDataTable(de_table, table_id);
}

function _DestroyDataTable(table_id) {
    idx = arrayIndex(table_id, table_ids)
    if(idx != null) {
        tables[idx].destroy();
        tables.splice(idx, 1);
        table_ids.splice(idx, 1);
        $('#' + table_id + '_body').empty();
    }
}

function _DestroyOnlyDataTable(table_id) {
    idx = arrayIndex(table_id, table_ids)
    if(idx != null) {
        tables[idx].destroy();
        tables.splice(idx, 1);
        table_ids.splice(idx, 1);
    }
}

function _AppendDataTable(table, table_id) {
    tables.push(table);
    table_ids.push(table_id);
}

function arrayCompare(a1, a2) {
    if (a1.length != a2.length) return false;
    var length = a2.length;
    for (var i = 0; i < length; i++) {
        if (a1[i] !== a2[i]) return false;
    }
    return true;
}

function inArray(needle, haystack) {
    var length = haystack.length;
    for(var i = 0; i < length; i++) {
        if(typeof haystack[i] == 'object') {
            if(arrayCompare(haystack[i], needle)) return true;
        } else {
            if(haystack[i] == needle) return true;
        }
    }
    return false;
}

function arrayIndex(needle, haystack) {
    var length = haystack.length;
    for (var i = 0; i < length; i ++) {
        if(haystack[i] == needle) {
            return i;
        }
    }
    return null;
}
function addMonths(date, months) {
    date.setMonth(date.getMonth() + months);
    return date;
}

function AjaxCall(ajax_url, data, method, success_callback, error_callback) {
    $.ajax({
        type: method,
        url: ajax_url,
        data: data,
        success: success_callback,
        error: error_callback
    });
}

function GenerateAlias(obj_id, alias_id) {
    var alias = $('#' + obj_id).val().toLowerCase().replace(/ /g, '_');
    alias_field = $('#' + alias_id);
    if (alias_field.length > 0) {
        current_alias = alias_field.val();
        if(current_alias == "") {
            $('#' + alias_id).val(alias);
        }
    }
}

function ToggleAll(cls) {
    if($('#' + cls + '_all').is(':checked')) {
        SelectAll(cls);
    }
    else {
        UnSelectAll(cls);
    }
}

function ButtonCheck(folder_type) {
    if($('.tool_list_table').length > 0) {
        $('.' + folder_type + '_check').click(function() {
            cnt = ListCheckCount(folder_type);
            if(cnt > 0) {
                AbleButton('move_objects_button');
                AbleButton('delete_objects_button');
            }
            else {
                DisableButton('move_objects_button');
                DisableButton('delete_objects_button');
            }

            ToolButtonCheck(cnt);
        });
    }
}

function DisableButton(button) {
    $('#' + button).attr('disabled', 'disabled');
}

function AbleButton(button) {
    $('#' + button).removeAttr('disabled');
}

function ListCheckCount(folder_type) {
    var cnt = 0;
    $('.' + folder_type + '_check').each(function() {
        if($(this).is(':checked')) {
            cnt += 1;
        }
    });

    return cnt;
}

function CheckedRows(folder_type) {
    ids = []
    $('.' + folder_type + '_check').each(function() {
        if($(this).is(':checked')) {
            ids.push($(this).val());
        }
    });

    return ids;
}

function ChangeShowRows(tool) {
    var rows = $('#show_rows').val();
    if(location.href.indexOf('?') == -1) {
        location.href = tool + "?r=" + rows;
    }
    else {
        location.href = tool + "&r=" + rows;
    }
}

function NewFolder(opt, obj) {
    var id = obj[0].id;
    ResetModal('new_folder_modal');
    HideLoader('new_folder_modal_loading');
    $('#new_folder_modal_content').show();
    $('#parent_folder_id').val(id);
    $('#submit_type').val('new');
    $('#new_folder_modal').modal('show');
}

function ResetModal(modal) {
    $('#' + modal).find('input').each(function() {
        $(this).empty();
    });
    $('#' + modal).find('select').each(function() {
        $(this).val('');
    });
}

function NewFolderSubmit(folder_type) {
    var brand = $('#brand_id').val();
    if(brand != "" && brand != undefined)
    {
        var name = $('#new_folder_name').val();
        var parent_id = $('#parent_folder_id').val();
        var submit_type = $('#submit_type').val();
        if(name != "" && name != undefined) {
            if(submit_type == "new") {
                ShowLoader('Creating New Folder', 'new_folder_modal_loading');
                $('#new_folder_modal_content').hide();

                var data = {'brand': brand, 'name': name, 'parent_id': parent_id, 'folder_type': folder_type};
                url = "/api/folders/new";
                method = "POST";
                AjaxCall(url, data, method, NewFolderSuccess, NewFolderError);
            }
            else if(submit_type == "edit") {
                ShowLoader('Renaming Folder', 'new_folder_modal_loading');
                $('#new_folder_modal_content').hide();

                var data = {'brand': brand, 'name': name, 'folder_id': parent_id};
                url = "/api/folders/rename";
                method = "POST";
                AjaxCall(url, data, method, NewFolderSuccess, NewFolderError);
            }
        }
    }
}

function NewFolderSuccess(data) {;
    HideLoader('new_folder_modal_loading');
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        location.href = "/folder/" + obj.Results.ID;
    }
    else {
        alert(HandleErrors(obj));
        $('#new_folder_modal').modal('hide');
        HideLoader('new_folder_modal_loading');
        $('#new_folder_modal_content').show();
    }
}

function NewFolderError(msg) {
    alert(msg);
    $('#new_folder_modal').modal('hide');
    HideLoader('new_folder_modal_loading');
    $('#new_folder_modal_content').show();
}

function Rename(opt, obj) {
    var id = obj[0].id;
    var title = obj[0].title;
    /*ResetModal('new_folder_modal');*/
    HideLoader('new_folder_modal_loading');
    $('#new_folder_modal_content').show();
    $('#parent_folder_id').val(id);
    $('#new_folder_name').val(title);
    $('#submit_type').val('edit');
    $('#new_folder_modal').modal('show');
}

function DeleteFolder(opt, obj) {
    conf = confirm('Are you sure?');
    if(!conf) {
        return false;
    }
    var current_folder_id = obj[0].id;
    var title = obj[0].title;
    if(inArray(title, folder_not_to_delete)) {
        return false;
    }
    var brand = $('#brand_id').val();
    if(brand != "" && brand != undefined)
    {
        var data = {'brand': brand, 'folder_id': current_folder_id}
        var url = "/api/folders/delete"
        var method = "POST"

        AjaxCall(url, data, method, DeleteFolderSuccess, DeleteFolderError);
    }
}

function DeleteFolderSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        window.location.reload();
    }
    else {
        errors = HandleErrors(obj);
        alert(errors);
    }
}

function DeleteFolderError(msg) {
    alert(msg);
}

function SubmitForm(form_type) {
    $('#' + form_type + "_form").submit();
}

function MoveObjects(folder_type) {
    if(ListCheckCount(folder_type) == 0) {
        alert('No Objects Selected');
        return false;
    }
    $('#move_objects_modal').modal('show');
}

function MoveObjectsSubmit(folder_type) {
    var brand = $('#brand_id').val();
    if(brand != "" && brand != undefined)
    {
        var new_folder_id = $('#move_to_folder_id').val();
        if(new_folder_id != "") {
            var ids = CheckedRows(folder_type);
            var data = {'brand': brand, 'folder_id': new_folder_id, 'id': ids}
            var url = "/api/" + folder_type + "/move"
            var method = "POST"

            AjaxCall(url, data, method, MoveObjectsSuccess, MoveObjectsError);
        }
    }
}

function MoveObjectsSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        $('#move_objects_modal').modal('hide');
        location.href = "/folder/" + obj.Results.ID;
    }
    else {
        alert(HandleErrors(obj));
        $('#move_objects_modal').modal('hide');
    }
}

function MoveObjectsError(msg) {
    alert(msg);
    $('#move_objects_modal').modal('hide');
}

function DeleteObjects(folder_type) {
    conf = confirm('Are you sure?');
    if(!conf) {
        return false;
    }
    var brand = $('#brand_id').val();
    if(brand != "" && brand != undefined)
    {
        var ids = CheckedRows(folder_type);
        var data = {'brand': brand, 'id': ids}
        var url = "/api/" + folder_type + "/delete"
        var method = "POST"

        AjaxCall(url, data, method, DeleteObjectsSuccess, DeleteObjectsError);
    }
}

function DeleteObjectsSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        if(current_folder_id != 0) {
            location.href = "/folder/" + current_folder_id;
        }
        else {
            window.location.reload();
        }
    }
    else {
        alert(HandleErrors(obj));
    }
}

function DeleteObjectsError(msg) {
    alert(msg);
}

function StartImport() {
    $('#import_current_step').val("import_general")
    $('#import_modal').modal('show');
}

function ShowImportFileModal() {
    RefreshImportFileList();
    $('#import_file_selection_modal').modal('show');
}

function RefreshImportFileList() {
    var brand = $('#brand_id').val();
    if(brand != "" && brand != undefined)
    {
        $('#import_file_selection_form').hide();
        ShowLoader('Getting Importable Files', 'import_file_selection_modal_loading');
        var data = {'brand': brand}
        var url = "/api/imports/files"
        var method = "POST"

        AjaxCall(url, data, method, ImportFileListSuccess, ImportFileListError);
    }
}

function ImportFileListSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        console.log(obj);
        folder_str = "<li>imports" + _process_import_file_children(obj.Results) + "</li>";
        $('#import_file_selection_file_list').append(folder_str);
        $('#import_file_selection_files').bind("select_node.jstree", function (e, sel_data) {
            var path = sel_data.node.li_attr.rel
            console.log(sel_data);
            if (path != "folder") {
                $('#import_file').val(path);
            }
        }).jstree({
            "core" : {
                "multiple" : false,
                'themes': {'dots': false}
            },
            'plugins': ['changed'],
            
        });
        HideLoader('import_file_selection_modal_loading');
        $('#import_file_selection_form').show();
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('import_file_selection_modal_loading');
    }
}

function _process_import_file_children(obj) {
    folder_str = ""
    if(obj != undefined && obj.length > 0) {
        folder_str = "<ul>";
        for(var idx = 0; idx < obj.length; idx ++) {
            child = obj[idx]
            if (child.type == "folder") {
                folder_str += "<li rel='folder'>" + child.name;
            }
            else {
                folder_str += "<li rel='" + child.full_path + "'>" + child.name;
            }
            if(typeof child.children !== undefined) {
                folder_str += _process_import_file_children(child.children);
            }
            folder_str += "</li>";
        }
        folder_str += "</ul>";
    }
    return folder_str;
}

function ImportFileListError(msg) {
    alert(msg);
    HideLoader('import_file_selection_modal_loading');
}

function SelectImportFile() {
   $('#import_file_selection_modal').modal('hide');
}

function ImportModalContinue() {
    var current_step = $('#import_current_step').val();
    if(current_step == "import_general") {
        var import_file = $('#import_file').val();
        if(import_file == "") {
            alert('Select a file');
            return false;
        }
        var import_file_delimiter = $('#import_file_delimiter').val();
        if(import_file_delimiter == "") {
            alert('Enter a file delimiter');
            return false;
        }
        $('#import_general').hide();
        $('#import_mapping').show();
        $('#import_current_step').val('import_mapping');
        ShowLoader("Preparing Field Mapping", "import_modal_loading");
        $('#import_form').hide();
        var brand = $('#brand_id').val();
        var target_type = $('#import_target_type').val();
        var target_folder_id = $('#import_folder_id').val();
        var data = {'brand': brand, 'target_folder_id': target_folder_id, 'target_type': target_type, 'import_file': import_file, 'import_file_delimiter': import_file_delimiter}
        var url = "/api/imports/mapping";
        var method = "POST"

        AjaxCall(url, data, method, ImportFieldsSuccess, ImportFieldsError);
    }
    else if(current_step == "import_mapping") {
        ShowLoader("Submitting Import", "import_modal_loading");
        $('#import_form').hide();
        var import_file = $('#import_file').val();
        var import_file_delimiter = $('#import_file_delimiter').val();
        var import_type = $('#import_type').val();
        var brand = $('#brand_id').val();
        var target_type = $('#import_target_type').val();
        var import_notify = $('#import_notification').val();
        var import_folder_id = $('#import_folder_id').val();
        var error = false;
        $('.required-true').each(function() {
            if($(this).val() == "") {
                alert('Some required fields not mapped');
                error = true
            }
        });
        if(!error) {
            mappings = []
            $('.dynamic-header select').each(function() {
                var id = $(this).attr('id')
                var field_name = id.replace(/select_/g, '')
                var header = $(this).val();
                mappings.push(header + ':' + field_name)
            });

            var date = new Date().toString('yyyy-M-d');
            var data = {
                'brand': brand,
                'name': 'Import of ' + import_file + ' of type ' + target_type + ' on ' + date,
                'target_type': target_type, 
                'target_folder_id': import_folder_id,
                'import_file': import_file, 
                'import_file_delimiter': import_file_delimiter,
                'import_type': import_type,
                'import_notification': import_notify,
                'system': 1,
                'mapping': mappings
            };
            var url = "/api/imports/submit";
            var method = "POST"

            AjaxCall(url, data, method, ImportSubmitSuccess, ImportSubmitError);
        }
        HideLoader('import_modal_loading');
        $('#import_form').show();
    }
}
function ImportFieldsSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        var file_header = obj.Results.FileHeader;
        var import_fields = obj.Results.ImportFields;
        for(var idx = 0; idx < import_fields.length; idx ++) {
            var field = import_fields[idx];
            var row_content = '<div class="form-group dynamic-header">' + 
                '<label for="header_' + field.Name + '" class="control-label col-lg-2">' + field.Label + '</label>' +
                '<div class="col-lg-10">' + 
                    '<select name="select_' + field.Name + '" class="form-control required-' + field.Required + '" id="select_' + field.Name + '">' + 
                        '<option value=""></option>';
            for(var h_idx = 0; h_idx < file_header.length; h_idx ++) {
                header = file_header[h_idx];
                if(header.name == field.Name)
                {
                    row_content += CreateDynamicOption(header.name, header.name, "selected");
                }
                else {
                    row_content += CreateDynamicOption(header.name, header.name);   
                }
            }
            row_content += "</select></div></div>";
            $('#import_mapping_form').append(row_content);
        }
        HideLoader('import_modal_loading');
        $('#import_modal_back_button').show();
        $('#import_form').show();  
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('import_modal_loading');
        $('#import_general').show();
        $('#import_mapping').hide();
        $('#import_form').show();
    }
    

}
function ImportFieldsError(msg) {
    alert(msg);
    HideLoader('import_modal_loading');
    $('#import_general').show();
    $('#import_mapping').hide();
    $('#import_form').show();
}

function ImportModalBack() {
    $('#import_modal_back_button').hide();
    $('#import_general').show();
    $('#import_mapping').hide();
    $('#import_current_step').val('import_general');
}
function ImportSubmitSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        alert('Import submitted successfully, it should begin shortly');
        $('#import_modal').modal('hide');
        ImportModalBack();
        if(current_folder_id != 0) {
            location.href = "/folder/" + current_folder_id;
        }
        else {
            window.location.reload();
        }
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('import_modal_loading');
        $('#import_form').show();
    }
}

function ImportSubmitError(msg) {
    alert(msg);
    HideLoader('import_modal_loading');
    $('#import_form').show();
}

function StartExport() {
    var target_type = $('#export_target_type').val();
    var date = new Date().toString('yyyyMd');
    $('#export_file').val('export_' + target_type + '_' + date + '.csv');
    if(ListCheckCount(target_type) > 0) {
        $('#export_type').val('2')
    }
    else if(target_type != "subscribers") {
        $('#export_type').val('3');
    }
    $('#export_modal').modal('show');
}

function ExportModalContinue() {
    var current_step = $('#export_current_step').val();
    if(current_step == "export_general") {
        $('#export_general').hide();
        $('#export_fields').show();
        $('#export_current_step').val('export_fields');
        ShowLoader("Getting Fields", "export_modal_loading");
        $('#export_form').hide();
        var brand = $('#brand_id').val();
        var target_type = $('#export_target_type').val();
        var target_folder_id = $('#export_folder_id').val();
        var data = {'brand': brand, 'target_type': target_type, 'target_folder_id': target_folder_id}
        var url = "/api/exports/fields";
        var method = "POST"

        AjaxCall(url, data, method, ExportFieldsSuccess, ExportFieldsError);
    }
    else if(current_step == "export_fields") {
        ShowLoader("Submitting Export", "export_modal_loading");
        $('#export_form').hide();
        var export_file = $('#export_file').val();
        var export_file_delimiter = $('#export_file_delimiter').val();
        var export_type = $('#export_type').val();
        var brand = $('#brand_id').val();
        var target_type = $('#export_target_type').val();
        var export_notify = $('#export_notification').val();
        var export_folder_id = $('#export_folder_id').val();
        var error = false;
        if(!error) {
            var fields = []
            $('.dynamic-header input').each(function() {
                if($(this).is(':checked')) {
                    var id = $(this).attr('id')
                    fields.push(id);
                }
            });
            var selected_objects = []
            if(export_type == "2") {
                selected_objects = CheckedRows(target_type);
            }

            var date = new Date().toString('yyyy-M-d');
            var data = {
                'brand': brand,
                'name': target_type + ' export on ' + date,
                'target_type': target_type, 
                'target_folder_id': export_folder_id,
                'export_file': export_file, 
                'export_file_delimiter': export_file_delimiter,
                'export_type': export_type,
                'export_notification': export_notify,
                'system': 1,
                'field': fields,
                'selected_object': selected_objects
            };
            var url = "/api/exports/submit";
            var method = "POST"

            AjaxCall(url, data, method, ExportSubmitSuccess, ExportSubmitError);
        }
        HideLoader('export_modal_loading');
        $('#export_form').show();
    }
}
function ExportModalBack() {
    $('#export_modal_back_button').hide();
    $('#export_general').show();
    $('#export_fields').hide();
    $('#export_current_step').val('export_general');
}
function ExportFieldsSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        var export_fields = obj.Results;
        for(var idx = 0; idx < export_fields.length; idx ++) {
            var field = export_fields[idx];
            var row_content = '<div class="form-group dynamic-header">' + 
                '<label for="' + field.Name + '" class="control-label col-lg-7">' + field.Label + '</label>' +
                '<div class="col-lg-5">' + 
                    '<input type="checkbox" class="form-control sw-checkbox export-field" value="1" id="' + field.Name + '" />' + 
                '</div></div>';
            $('#export_fields_form').append(row_content);
        }
        $('input.sw-checkbox').bootstrapSwitch({
            size: 'small',
            onText: 'Yes',
            offText: 'No',
        });
        HideLoader('export_modal_loading');
        $('#export_modal_back_button').show();
        $('#export_form').show();  
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('export_modal_loading');
        $('#export_general').show();
        $('#export_fields').hide();
        $('#export_form').show();
    }
}
function ExportFieldsError(msg) {
    alert(msg);
    HideLoader('export_modal_loading');
    $('#export_general').show();
    $('#export_fields').hide();
    $('#export_form').show();
}

function ExportSubmitSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        alert('Export submitted successfully, it should begin shortly');
        $('#export_modal').modal('hide');
        ExportModalBack();
        /*if(current_folder_id != 0) {
            location.href = "/folder/" + current_folder_id;
        }
        else {
            window.location.reload();
        }*/
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('export_modal_loading');
        $('#export_form').show();
    }
}

function ExportSubmitError(msg) {
    alert(msg);
    HideLoader('export_modal_loading');
    $('#export_form').show();
}

function StartSearch() {
    SearchModalBack();
    $('#search_modal').modal('show');
    var target_type = $('#search_target_type').val();
    var brand = $('#brand_id').val();
    $('#search_form').hide();
    ShowLoader('Getting Search Fields for ' + target_type, 'search_modal_loading');
    var target_list_id = "";
    if((target_type == "subscribers" || target_type == 'segment_subscribers') && typeof current_list !== undefined) {
        target_list_id = $('#search_folder_id').val();
    }
    var data = {'brand': brand, 'target_type': target_type, 'target_list_id': target_list_id};
    var url = "/api/forms/search";
    var method = "POST";

    AjaxCall(url, data, method, StartSearchSuccess, StartSearchError);
}

function StartSearchSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        for(var idx = 0; idx < obj.Results.length; idx ++) {
            var field = obj.Results[idx]
            $('#search_for').append(CreateDynamicOption(field.Name, field.Label));
        }
        HideLoader('search_modal_loading');
        $('#search_form').show();
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('search_modal_loading');
        $('#search_modal').modal('hide');
    }
}

function StartSearchError(msg) {
    alert(msg);
    HideLoader('search_modal_loading');
    $('#search_form').show();
    $('#search_modal').modal('hide');
}

function SearchModalContinue() {
    var current_step = $('#search_current_step').val();
    if(current_step == "search_general") {
        $('#search_general').hide();
        $('#search_results').show();
        $('#search_current_step').val('search_results');
        ShowLoader("Getting Results", "search_modal_loading");
        $('#search_form').hide();
        var brand = $('#brand_id').val();
        var target_type = $('#search_target_type').val();
        var search_type = $('#search_type').val();
        var search_for = $('#search_for').val();
        var search_contains = $('#search_contains').val();
        var search_folder_id = $('#search_folder_id').val();
        
        var data = {'brand': brand, 'target_type': target_type, 'search_type': search_type, 'search_for': search_for, 'search_contains': search_contains, 'search_folder_id': search_folder_id}
        var url = "/api/" + target_type + "/search";
        var method = "POST"

        AjaxCall(url, data, method, SearchResultsSuccess, SearchResultsError);
    }
}
function SearchModalBack() {
    _DestroyDataTable('search_results_table');
    $('#search_modal_back_button').hide();
    $('#search_general').show();
    $('#search_results').hide();
    $('#search_current_step').val('search_general');
    $('#search_modal_continue_button').show();
}

function SearchResultsSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        var fields = obj.Results.Fields;
        var data = obj.Results.Data;

        /*for (var idx = 0; idx < data.length; idx ++) {
            var row = data[idx];
            var row_content = '<tr>' + 
                    '<td>' + row['ID'] + "</td>" + 
                    '<td>' + row['MailChimp ID'] + '</td>' + 
                    '<td><a href="/lists/' + row['ID'] + '/details">' + row['Name'] + '</a></td>' +
                    '<td>' + row['Folder'] + '</td>' +
                '</tr>';
            $('#search_results_table_body').append(row_content);
        }*/
        PopulateDataTable(fields, data, "search_results_table")

        HideLoader('search_modal_loading');
        $('#search_form').show();
        $('#search_modal_continue_button').hide();
        $('#search_modal_back_button').show();
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('search_modal_loading');
        $('#search_form').show();
        $('#search_general').show();
        $('#search_results').hide();
        $('#search_current_step').val('search_general');
    }
}

function SearchResultsError(msg) {
    alert(msg);
    HideLoader('search_modal_loading');
    $('#search_form').show();
    $('#search_general').show();
    $('#search_results').hide();
    $('#search_current_step').val('search_general');
}
function toggleFolderView(view) {
    var src = $('#show_hide_folders_button a img').attr('src');
    var alt = $('#show_hide_folders_button a img').attr('alt');
    var title = $('#show_hide_folders_button a img').attr('title')
    

    if(!folders_collapsed) {
        $('#folder_list_container').hide();
        $('#' + view + '_container').removeClass('col-md-9');
        $('#' + view + '_container').addClass('col-md-12');
        src = src.replace('hide', 'show');
        alt = '>';
        title = 'Show Folders';
    }
    else {
        $('#' + view + '_container').removeClass('col-md-12');
        $('#' + view + '_container').addClass('col-md-9');
        $('#folder_list_container').show();
        src = src.replace('show', 'hide');
        alt = '<';
        title = 'Hide Folders';
    }

    $('#show_hide_folders_button a img').attr('src', src);
    $('#show_hide_folders_button a img').attr('alt', alt);
    $('#show_hide_folders_button a img').attr('title', title);

    if(folders_collapsed == true) {
        folders_collapsed = false;
    }
    else {
        folders_collapsed = true;
    }

    if($('.merge_tag_button').length > 0) {
        ResizeMergeButtonText();
    }

    $.fn.dataTable.tables( {visible: true, api: true} ).columns.adjust();
}