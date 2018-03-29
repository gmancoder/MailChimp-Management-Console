$(document).ready(function() {
	$('#import_objects_button').hide();
	$('#delete_objects_button').hide();
	if($('#campaign_tracking_table').length > 0) {
		
		$('#campaign_tracking_table').DataTable({
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
	else if($('#tracking_detail').length > 0) {
		$('#email_screenshot').colorbox();
	}
	else if($('#tracking_activity_table').length > 0) {
		$('#tracking_activity_table').DataTable({
	    	"scrollX": true,
			"scrollY": '50vh',
			"scrollCollapse": true,
			"searching": false,
			"paging": false,
			"ordering": false,
			"lengthChange": false,
			"info": false,    
		});
		$('#move_objects_button').hide();
		$('#export_objects_button').hide();
		$('#search_objects_button').hide();
	}
});

function StartTrackingExport(id, activity, type) {
	var date = new Date().toString('yyyyMd');
    $('#export_tracking_file').val('export_tracking_' + activity + '_' + date + '.csv');
	$('#export_tracking_modal').modal('show');
}

function TrackingExportModalContinue() {
	ShowLoader("Submitting Export", "export_tracking_modal_loading");
    $('#export_tracking_form').hide();
    var export_tracking_file = $('#export_tracking_file').val();
    var export_tracking_file_delimiter = $('#export_tracking_file_delimiter').val();
    var brand = $('#brand_id').val();
    var export_tracking_target_type = $('#export_tracking_target_type').val();
    var export_tracking_target_activity = $('#export_tracking_target_activity').val();
    var export_tracking_tracking_id = $('#export_tracking_id').val();
    var export_notify = $('#export_tracking_notification').val();
    var date = new Date().toString('yyyy-M-d');
    var data = {
        'brand': brand,
        'name': 'Tracking export on ' + date,
        'target_type': export_tracking_target_type, 
        'target_activity': export_tracking_target_activity, 
        'target_id': export_tracking_tracking_id,
        'export_file': export_tracking_file, 
        'export_file_delimiter': export_tracking_file_delimiter,
        'export_notification': export_notify,
        'system': 1
    };
    var url = "/api/campaign_tracking/export";
    var method = "POST"

    AjaxCall(url, data, method, TrackingExportSubmitSuccess, TrackingExportSubmitError);
}

function TrackingExportSubmitSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        alert('Export submitted successfully, it should begin shortly');
        $('#export_tracking_modal').modal('hide');
    }
    else {
        alert(HandleErrors(obj)); 
    }
    $('#export_tracking_form').show();
    HideLoader('export_tracking_modal_loading');
}

function TrackingExportSubmitError(msg) {
    alert(msg);
    HideLoader('export_tracking_modal_loading');
    $('#export_tracking_form').show();
}

function StartTrackingSearch() {
	$('#search_tracking_modal').modal('show');
}

function TrackingSearchModalContinue() {
	$('#search_tracking_general').hide();
    $('#search_tracking_results').show();
    $('#search_tracking_current_step').val('search_tracking_results');
	ShowLoader("Getting Results", "search_tracking_modal_loading");
    $('#search_tracking_form').hide();
    var brand = $('#brand_id').val();
    var tracking_id = $('#search_tracking_id').val();
    var target_activity = $('#search_tracking_target_activity').val();
    var target_type = $('#search_tracking_target_type').val();
    var contains = $('#search_tracking_contains').val();

    var data = {
        'brand': brand,
        'target_type': target_type, 
        'target_activity': target_activity, 
        'tracking_id': tracking_id,
        'contains': contains
    };
    var url = "/api/campaign_tracking/search_activity";
    var method = "POST"

    AjaxCall(url, data, method, TrackingSearchSuccess, TrackingSearchError);
}

function TrackingSearchModalBack() {
    _DestroyDataTable('search_tracking_results_table');
    $('#search_tracking_modal_back_button').hide();
    $('#search_tracking_general').show();
    $('#search_tracking_results').hide();
    $('#search_tracking_current_step').val('search_tracking_general');
    $('#search_tracking_modal_continue_button').show();
}

function TrackingSearchSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        var fields = obj.Results.Fields;
        var data = obj.Results.Data;
        PopulateDataTable(fields, data, "search_tracking_results_table")

        HideLoader('search_tracking_modal_loading');
        $('#search_tracking_form').show();
        $('#search_tracking_modal_continue_button').hide();
        $('#search_tracking_modal_back_button').show();
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('search_tracking_modal_loading');
        $('#search_tracking_form').show();
        $('#search_tracking_general').show();
        $('#search_tracking_results').hide();
        $('#search_tracking_current_step').val('search_tracking_general');
    }
}

function TrackingSearchError(msg) {
    alert(msg);
    HideLoader('search_tracking_modal_loading');
    $('#search_tracking_form').show();
    $('#search_tracking_general').show();
    $('#search_tracking_results').hide();
    $('#search_tracking_current_step').val('search_tracking_general');
}

function ToolButtonCheck() {

}