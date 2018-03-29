$(document).ready(function() {
    $('#move_objects_button').hide();
    $('#import_objects_button').hide();
    $('#export_objects_button').hide();
    if($('#file_locations_table').length > 0) {
        
        $('#file_locations_table').DataTable({
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
    else if($('#file_locations_form').length > 0) {
        TypeChanged();
    }
});

function ToolButtonCheck() {
    //Nothing
}

function TypeChanged() {
    var type = $('#type').val();

    $('.type_panel').hide();
    $('#' + type + '_panel').show();
}