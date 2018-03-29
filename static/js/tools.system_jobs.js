$(document).ready(function() {
    $('#move_objects_button').hide();
    $('#import_objects_button').hide();
    $('#export_objects_button').hide();
    $('#delete_objects_button').hide();
    if($('#system_jobs_table').length > 0) {
        
        $('#system_jobs_table').DataTable({
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