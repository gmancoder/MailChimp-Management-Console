$(document).ready(function() {
    $('#move_objects_button').hide();
    $('#import_objects_button').hide();
    $('#export_objects_button').hide();
    if($('#users_table').length > 0) {
        
        $('#users_table').DataTable({
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
});

function ToolButtonCheck() {
    //Nothing
}