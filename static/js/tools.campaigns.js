$(document).ready(function() {
	$('#import_objects_button').hide();
	$('#export_objects_button').hide();
	if($('#campaigns_table').length > 0) {
		
		$('#campaigns_table').DataTable({
	    	"scrollX": true,
			"scrollY": '50vh',
			"scrollCollapse": true,
			"searching": false,
			"paging": false,
			"ordering": false,
			"lengthChange": false,
			"info": false,    
		});
		//$('.campaigns_check').click(CampaignChecked);

		$('#send_campaigns_button').click(SendCampaignClicked);
		$('#test_campaigns_button').click(TestCampaignClicked);
		$('#schedule_campaigns_button').click(ScheduleCampaignClicked);
		$('#unschedule_campaigns_button').click(UnscheduleCampaignClicked);
		$('#cancel_campaigns_button').click(CancelCampaignClicked);
		$('#replicate_campaigns_button').click(ReplicateCampaignClicked);

	}
	else if($('#campaigns_form').length > 0) {
		$('#campaigns_list_id').change(ListChanged);
		$('#campaigns_email_id').change(EmailChanged);
		if($('#campaigns_segment_id option').length < 2) {
			$('#campaigns_segment_id').parent().parent().hide()
		}
		console.log($('#campaigns_list_id option:selected').length);
		if($('#campaigns_list_id option:selected').length == 0) {
			$('#campaigns_list_id').val('0');
		}
		if($('#campaigns_email_id option:selected').length == 0) {
			$('#campaigns_email_id').val('0');
		}
	}
	else if($('#schedule_form').length > 0) {
		$('#campaign_date').datepicker({'format': 'yyyy-mm-dd'});
	}
});
function ToolButtonCheck() {
	$('#schedule_campaigns_button').attr('disabled', 'disabled');
	$('#unschedule_campaigns_button').attr('disabled', 'disabled');
	$('#replicate_campaigns_button').attr('disabled', 'disabled');
	$('#send_campaigns_button').attr('disabled', 'disabled');
	$('#test_campaigns_button').attr('disabled', 'disabled');
	$('#move_objects_button').attr('disabled', 'disabled');
	var cnt = ListCheckCount('campaigns');
	var can_schedule = false;
	var can_unschedule = false;
	var can_replicate = false;
	var can_send = false;
	var can_test = false;
	var can_move = false;
	if(cnt == 1) {
		can_schedule = true;
		can_unschedule = true;
		can_replicate = true;
		can_send = true;
		can_test = true;
		can_move = true;
	}
	else if(cnt > 0) {
		can_move = true;
	}

	var checked = CheckedRows('campaigns');
	var can_schedule_count = 0;
	var can_unschedule_count = 0;
	var can_replicate_count = 0;
	var can_send_count = 0;
	var can_test_count = 0;
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
			if(can_replicate) {
				can_replicate_count += 1;
			}
			else {
				can_replicate_count -= 1;
			}
			if(can_send) {
				can_send_count += 1;
			}
			else {
				can_send_count -= 1;
			}
			if(can_test) {
				can_test_count += 1;
			}
			else {
				can_test_count -= 1;
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
		else if(status == 'send') {
			if(can_replicate) {
				can_replicate_count += 1;
			}
			else {
				can_replicate_count -= 1;
			}
		}
		else {
			can_schedule_count -= 1;
			can_unschedule_count -= 1;
			can_replicate_count -= 1;
			can_send_count -= 1;
			can_test_count -= 1;
			can_move_count -= 1;
		}

		/*var can_schedule_count = 0;
		var can_unschedule_count = 0;
		var can_replicate_count = 0;
		var can_send_count = 0;
		var can_test_count = 0;
		var can_move_count = 0;*/
		if(can_schedule_count > 0) {
			AbleButton('schedule_campaigns_button');
		}
		if(can_unschedule_count > 0) {
			AbleButton('unschedule_campaigns_button');
		}
		if(can_replicate_count > 0) {
			AbleButton('replicate_campaigns_button');
		}
		if(can_send_count > 0) {
			AbleButton('send_campaigns_button');
		}
		if(can_test_count > 0) {
			AbleButton('test_campaigns_button');
		}
		if(can_move_count > 0) {
			AbleButton('move_objects_button');
		}
	}
}
function EmailChanged() {
	var email = $('#campaigns_email_id option:selected').text();
	var email_id = $('#campaigns_email_id').val();
	if(email_id != '0') {
		if($('#update_type').val() == 'new') {
			$('#campaigns_name').val(email);
		}
		var brand = $('#brand_id').val();

		var data = {'brand': brand, 'id': email_id};
		var url = "/api/emails/get";
		var method = "POST";

		AjaxCall(url, data, method, EmailChangedSuccess, ListChangedError);
	}
}
function EmailChangedSuccess(data) {
	obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var emails = obj.Results;
		if(emails.length > 0) {
			var email = emails[0];
			var subject = $('#campaigns_subject_line').val();
			$('#campaigns_subject_line').val(email.subject);
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
	var current_list_id = $('#campaigns_list_id').val();
	if(current_list_id != '0') {
		$('#campaigns_segment_id').empty();
		$('#campaigns_segment_id').append(CreateDynamicOption('-', 'Loading Segments...'));

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
    	$('#campaigns_segment_id').empty();
    	$('#campaigns_segment_id').append(CreateDynamicOption('0', '-Select-'));
    	if(segments.length > 0) {
	    	for(var idx = 0; idx < segments.length; idx ++) {
	    		var segment = segments[idx];
	    		$('#campaigns_segment_id').append(CreateDynamicOption(segment.id, segment.name));
	    	}
	    	$('#campaigns_segment_id').parent().parent().show();
	    }
	    else {
	    	$('#campaigns_segment_id').parent().parent().hide();
	    }
    }	
    else {
        alert(HandleErrors(obj));
        $('#campaigns_segment_id').empty();
		$('#campaigns_segment_id').append(CreateDynamicOption('-', 'ERROR Loading Segments'));
    }
}
function ListChangedError(msg) {
	alert(msg);
	$('#campaigns_segment_id').empty();
	$('#campaigns_segment_id').append(CreateDynamicOption('-', 'ERROR Loading Segments'));
}
function ListDetailsSuccess(data) {
	obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var current_defaults = obj.Results;
    	if(current_defaults.length > 0) {
    		var current_default = current_defaults[0];
    		$('#campaigns_from_name').val(current_default.from_name);
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
	return confirm('Are you sure you want to cancel this campaign\'s schedule?');
}

/*$('#send_campaigns_button').click(SendCampaignClicked);*/
function SendCampaignClicked() {
	var checked = CheckedRows('campaigns');
	var item = checked[0];

	location.href = "/campaigns/" + item + "/send";
}
/*$('#test_campaigns_button').click(TestCampaignClicked);*/
function TestCampaignClicked() {
	var checked = CheckedRows('campaigns');
	var item = checked[0];

	location.href = "/campaigns/" + item + "/send?test=1";
}
/*
$('#schedule_campaigns_button').click(ScheduleCampaignClicked);*/
function ScheduleCampaignClicked() {
	var checked = CheckedRows('campaigns');
	var item = checked[0];

	location.href = "/campaigns/" + item + "/schedule";
}
/*
$('#unschedule_campaigns_button').click(UnscheduleCampaignClicked);*/
function UnscheduleCampaignClicked() {
	var conf = ConfirmCancelSchedule();
	if(!conf) {
		return false;
	}
	var checked = CheckedRows('campaigns');
	var item = checked[0];

	location.href = "/campaigns/" + item + "/unschedule";
}
/*
$('#cancel_campaigns_button').click(CancelCampaignClicked);*/
function CancelCampaignClicked() {
	var checked = CheckedRows('campaigns');
	var item = checked[0];

	location.href = "/campaigns/" + item + "/cancel";
}
/*
$('#replicate_campaigns_button').click(ReplicateCampaignClicked);*/
function ReplicateCampaignClicked() {
	var checked = CheckedRows('campaigns');
	var item = checked[0];

	location.href = "/campaigns/" + item + "/replicate";
}