var merge_ops = {
	'AddressMerge': [
		{'value': 'contains', 'label': 'Contains'}, 
		{'value': 'notcontain', 'label': 'Does not contain'}, 
		{'value':'blank', 'label': 'Blank'}, 
		{'value':'blank_not', 'label': 'Not Blank'}
	],
	'BirthdayMerge': [
		{'value': 'is', 'label': 'Is'},
		{'value': 'not', 'label': 'Is Not'},
		{'value':'blank', 'label': 'Blank'}, 
		{'value':'blank_not', 'label': 'Not Blank'}	
	],
	'DateMerge': [
		{'value': 'is', 'label': 'Is'},
		{'value': 'not', 'label': 'Is Not'},
		{'value': 'less', 'label': 'Is Less Than'},
		{'value':'blank', 'label': 'Blank'}, 
		{'value':'blank_not', 'label': 'Not Blank'}	
	],
	'TextMerge': [
		{'value': 'is', 'label': 'Is'},
		{'value': 'not', 'label': 'Is Not'},
		{'value': 'contains', 'label': 'Contains'}, 
		{'value': 'notcontain', 'label': 'Does not contain'},
		{'value': 'greater', 'label': 'Is Greater Than'}, 
		{'value': 'less', 'label': 'Is Less Than'},
		{'value': 'starts', 'label': 'Starts With'},
		{'value': 'ends', 'label': 'Ends With'},
		{'value':'blank', 'label': 'Blank'}, 
		{'value':'blank_not', 'label': 'Not Blank'}
	],
	'SelectMerge': [
		{'value': 'is', 'label': 'Is'},
		{'value': 'not', 'label': 'Is Not'},
		{'value':'blank', 'label': 'Blank'}, 
		{'value':'blank_not', 'label': 'Not Blank'}	
	],
	'EmailAddress': [
		{'value': 'is', 'label': 'Is'},
		{'value': 'not', 'label': 'Is Not'},
		{'value': 'contains', 'label': 'Contains'}, 
		{'value': 'notcontain', 'label': 'Does not contain'},
		{'value': 'greater', 'label': 'Is Greater Than'}, 
		{'value': 'less', 'label': 'Is Less Than'}
	]
};

var merge_fields_for_segments = [];
var segment_condition_count = 0;
var init = true;
var current_list_id;

$(document).ready(function() {
	$('a[data-toggle="tab"]').on( 'shown.bs.tab', function (e) {
        $.fn.dataTable.tables( {visible: true, api: true} ).columns.adjust();
    } );
	if($('#segments_table').length > 0) {
		$('#import_objects_button').hide();
		$('#export_objects_button').hide();

		$('#segments_table').DataTable({
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
	else if($('#segments_form').length > 0) {
		ChangeFormOptions();
		ListChanged();
		$('#segments_type').change(ChangeFormOptions);
		$('#segments_list_id').change(ListChanged);
		$('#segment_condition_field').change(SegmentFieldChanged);
		//RenderConditionsTable();
	}
});

function ChangeFormOptions() {
	var type = $('#segments_type').val();
	if(type == 'saved') {
		$('#segment_conditions').show();
		$('#segment_subscribers').hide();
	}
	else {
		$('#segment_conditions').hide();
		$('#segment_subscribers').show();
	}
}

function ListChanged() {
	current_list_id = $('#segments_list_id').val();
	$('#segment_subscribers_form').hide();
	$('#segment_condition_form').hide();
	ClearSubscriberList('list_subscriber_id_source');
	ClearSubscriberList('list_subscriber_id');
	if(!init) {
		_DestroyDataTable('segment_conditions_table');
	}
	ShowLoader('Getting List Subscribers', 'segment_subscribers_loading');
	ShowLoader('Getting List Merge Fields', 'segment_conditions_loading');
	
	var brand = $('#brand_id').val();

	var data = {'brand': brand, 'list_id': current_list_id, 'page': 1, 'limit': 0};
	var url = "/api/subscribers/get";
	var method = "POST";

	AjaxCall(url, data, method, ListChangedSuccess, ListChangedError)
}

function ListChangedSuccess(data) {
	obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var subscribers = obj.Results.Data;
    	for(var idx = 0; idx < subscribers.length; idx ++) {
    		var subscriber = subscribers[idx];
    		var value = subscriber.ID + '|' + subscriber.EmailAddress;
    		//console.log(list_subscribers.indexOf(parseInt(subscriber.id)))
    		if(!inArray(parseInt(subscriber.ID), list_subscribers)) {
    			$('#list_subscriber_id_source').append(CreateDynamicOption(value, subscriber.EmailAddress));
    		}
    		else {
    			$('#list_subscriber_id').append(CreateDynamicOption(value, subscriber.EmailAddress));	
    			AddSubscriberToFormField(value);
    		}

    	}
    	$('#segment_condition_field .dynamic_option').remove();
    	var merge_fields = obj.Results.MergeFields;
    	merge_fields_for_segments = [];
    	for(var idx = 0; idx < merge_fields.length; idx ++) {
    		var merge_field = merge_fields[idx];
    		if(merge_field.type != "phone" && merge_field.type != "imageurl" && merge_field.type != "url") {
				var value = SegmentConditionType(merge_field.type) + '|' + merge_field.tag + '|' + merge_field.name;
				$('#segment_condition_field').append(CreateDynamicOption(value, merge_field.name));
			}
		}
    	PopulateSegmentOps();
    	$('#segment_subscribers_form').show();
    	$('#segment_condition_form').show();
		HideLoader('segment_subscribers_loading');
		HideLoader('segment_conditions_loading');
		init = false;
		RenderConditionsTable();
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('segment_subscribers_loading');
        HideLoader('segment_conditions_loading');
    }
}
function ListChangedError(msg) {
	alert(msg);
	HideLoader('segment_subscribers_loading');
	HideLoader('segment_conditions_loading');
}

function AddExistingCondition(tag) {
	for(var idx = 0; idx < conditions.length; idx ++) {
		condition = conditions[idx];
		var c_tag = condition.field;
		if(c_tag == tag) {
			AddNewCondition(condition.field, condition.op, condition.value);
		}
	}
}

function ClearSubscriberList(id) {
	$('#' + id + ' dynamic-option').remove();
}

function MoveSubscribers(src, target, all) {
	$('#' + src + ' option').each(function() {
		if($(this).is(':selected') || all) {
			$('#' + target).append(CreateDynamicOption($(this).val(), $(this).text()));
			$(this).remove();
			if(target.indexOf('source') != -1) {
				RemoveSubscriberFromFormField($(this).val());
			}
			else {
				AddSubscriberToFormField($(this).val());
			}
		}
	});
}

function RemoveSubscriberFromFormField(value) {
	var form_val = $('#selected_subscribers').val();
	var new_form_val = "";
	var form_val_parts = form_val.split(';');
	for(var idx = 0; idx < form_val_parts.length - 1; idx ++) {
		var part = form_val_parts[idx];
		if(part != value) {
			new_form_val += part + ';';
		}
	}
	$('#selected_subscribers').val(new_form_val);
}

function AddSubscriberToFormField(value) {
	var form_val = $('#selected_subscribers').val();
	form_val += value + ';';
	$('#selected_subscribers').val(form_val);
}


function AddSubscribers() {
	MoveSubscribers('list_subscriber_id_source', 'list_subscriber_id', false);
}

function RemoveSubscribers() {
	MoveSubscribers('list_subscriber_id', 'list_subscriber_id_source', false);
}
function AddAllSubscribers() {
	MoveSubscribers('list_subscriber_id_source', 'list_subscriber_id', true);
}

function RemoveAllSubscribers() {
	MoveSubscribers('list_subscriber_id', 'list_subscriber_id_source', true);
}
function SegmentFieldChanged() {
	var obj = $(this);
	PopulateSegmentOps(obj);
}
function PopulateSegmentOps() {
	var val = $('#segment_condition_field').val()
	var val_parts = val.split('|');
	var type = val_parts[0];
	var ops = merge_ops[type];
	$('#segment_condition_op option.dynamic_option').remove();
	for(var idx = 0; idx < ops.length; idx ++) {
		var op = ops[idx];
		$('#segment_condition_op').append(CreateDynamicOption(op.value, op.label));
	}
}
function SegmentConditionType(type) {
	if(type == 'text' || type == 'number') {
		return "TextMerge";
	}
	else if(type == "address" || type == "zip") {
		return "AddressMerge";
	}
	else if(type == "birthday") {
		return "BirthdayMerge";
	}
	else if(type == "date") {
		return "DateMerge";
	}
	else if(type == "dropdown" || type =="radio") {
		return "SelectMerge";
	}
	else if(type == "email") {
		return "EmailAddress";
	}
	else {
		return "";
	}
}
function ShowAddConditionForm() {
	$('#add_new_condition_form').slideToggle();
}
function AddNewCondition() {
	var field = $('#segment_condition_field').val();
	var field_spl = field.split('|');
	var field_name = field_spl[2];
	var op = $('#segment_condition_op').val();
	var value = $('#segment_condition_value').val();

	segment_condition_count += 1;
	var condition = '<tr class="condition_row">' + 
		'<td>' + field_name + '</td>' + 
		'<td>' + op + '</td>' + 
		'<td>' + value + '</td>' + 
		'<td>' + 
			'<input type="hidden" name="segment_condition" value="' + field_spl[0] + '|' + field_spl[1] + '|' + op + '|' + value + '" />' +
			'<a href="javascript:;" onClick="RemoveCondition(this);" class="btn btn-xs btn-danger">Remove</a>' +
		'</td></tr>';
	_DestroyOnlyDataTable('segment_conditions_table');
	$('#segment_conditions_table_body').append(condition);
	RenderConditionsTable();

	$('#segment_condition_field').val("");
	$('#segment_condition_op').val("");
	$('#segment_condition_value').val("");
	//ShowAddConditionForm();

}

function RenderConditionsTable() {
	
    var segment_conditions_table = $('#segment_conditions_table').DataTable( {
	    "destroy": true,
	    "scrollX": true,
	    "scrollCollapse": true,
		"searching": false,
		"paging": false,
		"ordering": false,
		"lengthChange": false,
		"info": false
    });

    _AppendDataTable(segment_conditions_table, 'segment_conditions_table');
}

function GetSubscribers(page, limit) {
	var brand = $('#brand_id').val();
	if(page == 1) {
		ShowLoader('Getting Subscribers', 'segment_subscribers_loading');
		$('#segment_subscriber_container').hide();
	}
	var data = {'brand': brand, 'segment_id': current_segment_id, 'page': page, 'limit': limit}
	var url = "/api/segments/get_subscribers"
	var method = "POST"
	AjaxCall(url, data, method, GetSubscribersSuccess, GetSubscribersError);
}

function GetSubscribersSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var table_id = "segment_subscribers_table";
        var results = obj.Results;
        $('#segment_subscribers_table_body').empty();
        $('#segment_subscriber_table_head .merge-field-col').remove();
        var merge_fields = results.MergeFields;
        for(var idx = 0; idx < merge_fields.length; idx ++) {
        	var merge_field = merge_fields[idx];
        	var row = '<th class="merge-field-col" style="width:100px;">' + merge_field.name + '</th>';
        	$('#segment_subscriber_table_head').append(row);
        }
        _DestroyDataTable(table_id);
        var subscriber_data = results.Data;
        for (var idx = 0; idx < subscriber_data.length; idx ++) {
        	var subscriber = subscriber_data[idx];
        	var row = '<tr>' +
        		'<td align="center" style="width:25px;"><input type="checkbox" class="segment_subscribers_check" name="sub_check_' + subscriber.ID + '" id="sub_check_' + subscriber.ID + '" value="' + subscriber.ID + '" /></td>' +
        		'<td style="width:50px;">' + subscriber.ID + '</td>' + 
        		'<td style="width:400px;"><img src="/static/img/' + subscriber.Status + '.png" width="24px" alt="' + subscriber.Status + '" title="' + subscriber.Status + '" />&nbsp;<a href="/subscribers/' + subscriber.ID + '">' + subscriber.EmailAddress + '</a></td>' +
        		'<td style="width:150px;">' + subscriber.EmailTypePreference + '</td>' +
        		'<td style="width:200px;">' + subscriber.DateAdded + '</td>' +
        		'<td style="width:200px;">' + subscriber.LastModified + '</td>';
        	for(var midx = 0; midx < merge_fields.length; midx ++) {
	        	var merge_field = merge_fields[midx];
	        	row += '<td style="width:100px;overflow:hidden;">' + subscriber[merge_field.tag] + '</td>';
	        }
	        $('#segment_subscribers_table_body').append(row);
        }

        var table = $('#' + table_id).DataTable({
        	"destroy": true,
			"scrollX": true,
			"scrollY": '50vh',
			"scrollCollapse": true,
			"searching": false,
			"paging": false,
			"ordering": false,
			"lengthChange": false,
			"info": false,
			"bAutoWidth": true,
		});

		

		_AppendDataTable(table, table_id);

		$('.segment_subscribers_check').click(function() {
			cnt = ListCheckCount('segment_subscribers');
			console.log(cnt);
			if(cnt > 0) {
				$('#delete_objects_button').removeAttr('disabled');
	        }
	        else {
	            $('#delete_objects_button').attr('disabled', 'disabled');
	        }
		});

        var total_records = results.TotalRecords;
        var records_returned = subscriber_data.length;
        var records_per_page = parseInt($('#show_rows').val());
        if(records_per_page > 0) {
        	var page_count = Math.ceil(total_records / records_per_page);
        }
        else {
        	var page_count = 1;
        }

        var pagination = "";
        $('#subscriber_pagination').empty();
        if(current_page != 1) {
        	pagination += '<a href="javascript:;" onClick="SubscriberPage(' + (current_page - 1) + ');">< Prev</a>&nbsp;';
        }
        if(current_page <= 4) {
        	var start_page = 1;
        }
        else {
        	var start_page = current_page - 4;
        }
        for(idx = start_page; idx < current_page + 5; idx ++)
        {
        	if(current_page != idx && idx <= page_count) {
        		pagination += '<a href="javascript:;" onClick="SubscriberPage(' + idx + ');">' + idx + '</a>&nbsp;';
        	}
        	else if(current_page == idx) {
        		pagination += '<strong>' + idx + '</strong>&nbsp;';
        	}
        }
        if(current_page < page_count) {
        	pagination += '<a href="javascript:;" onClick="SubscriberPage(' + (current_page + 1) + ');">Next ></a>';
        }
        $('#subscriber_pagination').append(pagination);

	    HideLoader('segment_subscribers_loading');
	    $('#segment_subscriber_container').show();
	    $.fn.dataTable.tables( {visible: true, api: true} ).columns.adjust();
	    //table.fnAdjustColumnSizing();
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('segment_subscribers_loading');
    }
}

function GetSubscribersError(msg) {
    alert(msg);
    HideLoader('segment_subscribers_loading');
}

function SubscriberPage(pg) {
	current_page = pg;
	var records_per_page = parseInt($('#show_rows').val());
	GetSubscribers(pg, records_per_page);
}

function ChangeSubscriberShowRows() {
	current_page = 1;
	var records_per_page = parseInt($('#show_rows').val());
	GetSubscribers(1, records_per_page);
}

function ToggleActions(tab) {
	$('.segment_action').each(function() {
		if(tab == 'properties') {
			$(this).show();
		}
		else {
			$(this).hide();
		}	
	})
	
}

function DeleteSelectedSubscribers() {
	subscribers_to_delete = CheckedRows('segment_subscribers');
	if(subscribers_to_delete.length > 0) {
		conf = confirm('Are you sure you want to remove ' + subscribers_to_delete.length + ' subscribers from this segment?\nThis operation CANNOT be undone!');
		if(!conf) {
			return false;
		}

		ShowLoader('Deleting Selected Subscribers', 'loading_modal_loading');
		$('#loading_modal').modal('show');
		var data = {'brand': $('#brand_id').val(), 'segment_id': current_segment_id, 'subscriber': subscribers_to_delete}
		var url = "/api/segment_subscribers/remove"
		var method = "POST"

		AjaxCall(url, data, method, DeleteSubscriberSuccess, DeleteSubscriberError);
	}
}

function DeleteSubscriberSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var results = obj.Results;
    	var result_string = "";
    	for(var idx = 0; idx < results.length; idx ++) {
    		result_string += results[idx].ID + ": " + results[idx].Message + "\n";
    	}
    	alert(result_string);
    	$('#loading_modal').modal('hide');
    	HideLoader('loading_modal_loading');
    	SubscriberPage(1);
    }
    else {
        alert(HandleErrors(obj));
        $('#loading_modal').modal('hide');
        HideLoader('loading_modal_loading');
    }
}

function DeleteSubscriberError(msg) {
    alert(msg);
    $('#loading_modal').modal('hide');
    HideLoader('loading_modal_loading');
}

function RefreshSegment() {
	ShowLoader('Refreshing Subscribers', 'loading_modal_loading');
	$('#loading_modal').modal('show');
	var data = {'brand': $('#brand_id').val(), 'segment_id': current_segment_id}
	var url = "/api/segment_subscribers/refresh"
	var method = "POST"

	AjaxCall(url, data, method, RefreshSegmentSuccess, RefreshSegmentError);
}

function RefreshSegmentSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	SubscriberPage(1);
    	$('#loading_modal').modal('hide');
        HideLoader('loading_modal_loading');
    }
    else {
        alert(HandleErrors(obj));
        $('#loading_modal').modal('hide');
        HideLoader('loading_modal_loading');
    }
}

function RefreshSegmentError(msg) {
    alert(msg);
    $('#loading_modal').modal('hide');
    HideLoader('loading_modal_loading');
}