$(document).ready(function() {
	$('#import_objects_button').hide();
	$('#export_objects_button').hide();
	if($('#ab_tests_table').length > 0) {
		
		$('#ab_tests_table').DataTable({
	    	"scrollX": true,
			"scrollY": '50vh',
			"scrollCollapse": true,
			"searching": false,
			"paging": false,
			"ordering": false,
			"lengthChange": false,
			"info": false,    
		});

		$('#send_ab_tests_button').click(SendCampaignClicked);
		$('#schedule_ab_tests_button').click(ScheduleCampaignClicked);
		$('#unschedule_ab_tests_button').click(UnscheduleCampaignClicked);
	}
	else if($('#ab_tests_form').length > 0) {
		$('#ab_tests_list_id').change(ListChanged);
		$('#ab_tests_email_id_1').change(EmailChanged);
		$('#ab_tests_email_id_2').change(EmailChanged);
		$('#ab_tests_email_id_3').change(EmailChanged);
		if($('#ab_tests_segment_id option').length < 2) {
			$('#ab_tests_segment_id').parent().parent().hide()
		}
		//console.log($('#ab_tests_list_id option:selected').length);
		if($('#ab_tests_list_id option:selected').length == 0) {
			$('#ab_tests_list_id').val('0');
		}
		if($('#ab_tests_email_id_1 option:selected').length == 0) {
			$('#ab_tests_email_id_1').val('0');
		}
		if($('#ab_tests_email_id_2 option:selected').length == 0) {
			$('#ab_tests_email_id_2').val('0');
		}
		if($('#ab_tests_email_id_3 option:selected').length == 0) {
			$('#ab_tests_email_id_3').val('0');
		}
		$('#ab_tests_send_date_1').datepicker({'format': 'yyyy-mm-dd'});
		$('#ab_tests_send_date_2').datepicker({'format': 'yyyy-mm-dd'});
		$('#ab_tests_send_date_3').datepicker({'format': 'yyyy-mm-dd'});

		$('#ab_tests_test_type').change(TestTypeChanged);
		TestTypeChanged();
		$('#ab_tests_test_combinations').change(TestCombinationsChanged);
		TestCombinationsChanged();
	}
	else if($('#schedule_form').length > 0) {
		$('#ab_test_date').datepicker({'format': 'yyyy-mm-dd'});
	}
});
function ToolButtonCheck() {
	$('#schedule_ab_tests_button').attr('disabled', 'disabled');
	$('#unschedule_ab_tests_button').attr('disabled', 'disabled');
	$('#send_ab_tests_button').attr('disabled', 'disabled');
	$('#move_objects_button').attr('disabled', 'disabled');
	var cnt = ListCheckCount('ab_tests');
	var can_schedule = false;
	var can_unschedule = false;
	var can_send = false;
	var can_move = false;
	if(cnt == 1) {
		can_schedule = true;
		can_unschedule = true;
		can_send = true;
		can_move = true;
	}
	else if(cnt > 0) {
		can_move = true;
	}

	var checked = CheckedRows('ab_tests');
	var can_schedule_count = 0;
	var can_unschedule_count = 0;
	var can_send_count = 0;
	var can_move_count = 0;
	for(var idx = 0; idx < checked.length; idx ++) {
		var id = checked[idx];
		var status = $('#status_field_' + id).html();

		if(status == 'save') {
			if(can_schedule) {
				can_schedule_count += 1;
			}
			else {
				can_schedule_count -= 1;
			}
			if(can_send) {
				can_send_count += 1;
			}
			else {
				can_send_count -= 1;
			}
			if(can_move) {
				can_move_count += 1;
			}
			else {
				can_move_count -= 1;
			}
		}
		else if(status == 'schedule') {
			if(can_unschedule) {
				can_unschedule_count += 1;
			}
			else {
				can_unschedule_count -= 1;
			}
		}
		else {
			can_schedule_count -= 1;
			can_unschedule_count -= 1;
			can_send_count -= 1;
			can_move_count -= 1;
		}

		/*var can_schedule_count = 0;
		var can_unschedule_count = 0;
		var can_replicate_count = 0;
		var can_send_count = 0;
		var can_test_count = 0;
		var can_move_count = 0;*/
		if(can_schedule_count > 0) {
			AbleButton('schedule_ab_tests_button');
		}
		if(can_unschedule_count > 0) {
			AbleButton('unschedule_ab_tests_button');
		}
		if(can_send_count > 0) {
			AbleButton('send_ab_tests_button');
		}
		if(can_move_count > 0) {
			AbleButton('move_objects_button');
		}
	}
}
var changed_email_id;
function EmailChanged(evt) {
	console.log(evt);
	changed_email_id = evt.target.id;
	console.log(changed_email_id);
	var email = $('#' + changed_email_id + ' option:selected').text();
	var email_id = $('#' + changed_email_id).val();
	if(email_id != '0') {

		var brand = $('#brand_id').val();

		var data = {'brand': brand, 'id': email_id};
		var url = "/api/emails/get";
		var method = "POST";

		AjaxCall(url, data, method, EmailChangedSuccess, EmailChangedError);
	}
}
function EmailChangedSuccess(data) {
	obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var emails = obj.Results;
    	var changed_email_id_num_idx = changed_email_id.length - 1;
    	var changed_email_id_num = changed_email_id[changed_email_id_num_idx];
		if(emails.length > 0) {
			var email = emails[0];
			if(changed_email_id_num == '1') {
				$('#ab_tests_subject_line').val(email.subject);
			}
			//var subject = $('#ab_tests_subject_line').val();
			$('#ab_tests_subject_line_' + changed_email_id_num).val(email.subject);
	    }
    }	
    else {
        alert(HandleErrors(obj));
    }
}
function EmailChangedError(msg) {
	alert(msg);
}
function ListChanged() {
	var current_list_id = $('#ab_tests_list_id').val();
	if(current_list_id != '0') {
		$('#ab_tests_segment_id').empty();
		$('#ab_tests_segment_id').append(CreateDynamicOption('-', 'Loading Segments...'));

		var brand = $('#brand_id').val();

		var data = {'brand': brand, 'list_id': current_list_id};
		var url = "/api/segments/all";
		var method = "POST";

		AjaxCall(url, data, method, ListChangedSuccess, ListChangedError);

		var data = {'brand': brand, 'id': current_list_id};
		var url = "/api/lists/get_defaults";
		var method = "POST";

		AjaxCall(url, data, method, ListDetailsSuccess, ListDetailsError);
	}
}

function ListChangedSuccess(data) {
	obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var segments = obj.Results;
    	$('#ab_tests_segment_id').empty();
    	$('#ab_tests_segment_id').append(CreateDynamicOption('0', '-Select-'));
    	if(segments.length > 0) {
	    	for(var idx = 0; idx < segments.length; idx ++) {
	    		var segment = segments[idx];
	    		$('#ab_tests_segment_id').append(CreateDynamicOption(segment.id, segment.name));
	    	}
	    	$('#ab_tests_segment_id').parent().parent().show();
	    }
	    else {
	    	$('#ab_tests_segment_id').parent().parent().hide();
	    }
    }	
    else {
        alert(HandleErrors(obj));
        $('#ab_tests_segment_id').empty();
		$('#ab_tests_segment_id').append(CreateDynamicOption('-', 'ERROR Loading Segments'));
    }
}
function ListChangedError(msg) {
	alert(msg);
	$('#ab_tests_segment_id').empty();
	$('#ab_tests_segment_id').append(CreateDynamicOption('-', 'ERROR Loading Segments'));
}
function ListDetailsSuccess(data) {
	obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var current_defaults = obj.Results;
    	if(current_defaults.length > 0) {
    		var current_default = current_defaults[0];
    		$('#ab_tests_from_name').val(current_default.from_name);
    		$('#ab_tests_from_name_1').val(current_default.from_name);
    		$('#ab_tests_from_name_2').val(current_default.from_name);
    		$('#ab_tests_from_name_3').val(current_default.from_name);
	    }	
    }	
    else {
        alert(HandleErrors(obj));
    }
}
function ListDetailsError(msg) {
	alert(msg);
}
function ConfirmCancelSchedule(anchor) {
	return confirm('Are you sure you want to cancel this A/B Test\'s schedule?');
}

/*$('#send_ab_tests_button').click(SendCampaignClicked);*/
function SendCampaignClicked() {
	var checked = CheckedRows('ab_tests');
	var item = checked[0];

	location.href = "/ab_tests/" + item + "/send";
}
/*
$('#schedule_ab_tests_button').click(ScheduleCampaignClicked);*/
function ScheduleCampaignClicked() {
	var checked = CheckedRows('ab_tests');
	var item = checked[0];

	location.href = "/ab_tests/" + item + "/schedule";
}
/*
$('#unschedule_ab_tests_button').click(UnscheduleCampaignClicked);*/
function UnscheduleCampaignClicked() {
	var conf = ConfirmCancelSchedule();
	if(!conf) {
		return false;
	}
	var checked = CheckedRows('ab_tests');
	var item = checked[0];

	location.href = "/ab_tests/" + item + "/unschedule";
}

function TestTypeChanged() {
	var type = $('#ab_tests_test_type').val();
	console.log(type);
	if(type == 'content') {
		ChangeDisplayForType(['email_id'], ['send_date', 'send_time', 'subject_line', 'from_name', 'reply_to']);
	}
	else if(type == 'from_name') {
		ChangeDisplayForType(['from_name', 'reply_to'], ['send_date', 'send_time', 'subject_line', 'email_id']);

	}
	else if(type == 'send_time') {
		ChangeDisplayForType(['send_date', 'send_time'], ['from_name', 'reply_to', 'subject_line', 'email_id']);
	}
	else if(type == 'subject_line') {
		ChangeDisplayForType(['subject_line'], ['from_name', 'reply_to', 'send_date', 'send_time', 'email_id']);
	}
}

function ChangeDisplayForType(show, hide) {
	for(var idx = 1; idx < 4; idx ++) {
		for(var s_idx = 0; s_idx < show.length; s_idx ++) {
			var s_id = show[s_idx];
			var field_id = s_id + '_' + idx;
			ShowFormField(field_id);
		}
		for(var h_idx = 0; h_idx < hide.length; h_idx ++) {
			var h_id = hide[h_idx];
			var field_id = h_id + '_' + idx;
			HideFormField(field_id);
		}
	}
	if(!inArray('email_id', show)) {
		ShowFormField('email_id_1');
	}
}
function ShowFormField(id) {
	$('#ab_tests_' + id).parent().parent().show();
}
function HideFormField(id) {
	$('#ab_tests_' + id).parent().parent().hide();
}

function TestCombinationsChanged() {
	var combos = parseInt($('#ab_tests_test_combinations').val());
	if(combos == 2) {
		$('fieldset[id="36"]').hide();
	}
	else {
		$('fieldset[id="36"]').show();	
	}
}