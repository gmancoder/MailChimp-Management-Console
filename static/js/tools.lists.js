$(document).ready(function() {
	$('a[data-toggle="tab"]').on( 'shown.bs.tab', function (e) {
        $.fn.dataTable.tables( {visible: true, api: true} ).columns.adjust();
    } );
    $('#lists_table').DataTable({
    	"scrollX": true,
		"scrollY": '50vh',
		"scrollCollapse": true,
		"searching": false,
		"paging": false,
		"ordering": false,
		"lengthChange": false,
		"info": false,    
	});

	$('#list_merge_fields_table').DataTable({
    	"scrollX": true,
		"scrollY": '50vh',
		"scrollCollapse": true,
		"searching": false,
		"paging": false,
		"ordering": false,
		"lengthChange": false,
		"info": false,    
	});
});
function ToolButtonCheck(cnt) {
	if(cnt == 1) {
		$('#list_details_button').removeAttr('disabled');
	}
	else {
		$('#list_details_button').attr('disabled', 'disabled');
	}
}
function HideSubscriberButtons() {
	$('#subscriber_buttons').hide();
}
function ShowSubscriberButtons() {
	$('#subscriber_buttons').show();
}

function GetStatuses() {
	var brand = $('#brand_id').val();
	ShowLoader('Updating Status Overview', 'status_chart_loading');
	var data = {'brand': brand, 'list_id': current_list_id}
	var url = '/api/lists/statuses'
	var method = "POST"
	AjaxCall(url, data, method, GetStatusesSuccess, GetStatusesError);
}
function GetStatusesSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        var results = obj.Results;
        google.charts.load('current', {'packages':['corechart', 'table']});
        google.charts.setOnLoadCallback(function() {
	        var data = new google.visualization.DataTable();
		    data.addColumn('string', 'Status');
		    data.addColumn('number', 'Count');
		    var unsub_count = 0;
		    var sub_count = 0;
		    var cleaned_count = 0;
		    var pending_count = 0;
		    for(var idx = 0; idx < results.length; idx ++) {
		    	var result = results[idx];
		    	var status = result.status
		    	if(status == 'subscribed') {
		    		sub_count = result.count;
		    	}
		    	else if(status == 'unsubscribed') {
		    		unsub_count = result.count;
		    	}
		    	else if(status == 'cleaned') {
		    		cleaned_count = result.count;
		    	}
		    	else if(status == 'pending') {
		    		pending_count = result.count;
		    	}
		    }
		    data.addRows([['Active', sub_count], ['Unsubscribed', unsub_count], ['Cleaned', cleaned_count], ['Pending', pending_count]]);
		    drawChart(data);
		});
	    HideLoader('status_chart_loading');
	    $('#chart_container').show();
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('status_chart_loading');
    }
}

function drawChart(data) {
    // Set chart options
    var options = {'is3D': true,
                   	backgroundColor: { fill:'transparent' },
                   	colors: ['#049104', '#F92E01', '#E0AD01', '#c7e2e2']};

    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.PieChart(document.getElementById('chart_div'));
    chart.draw(data, options);
}

function GetStatusesError(msg) {
    alert(msg);
    HideLoader('status_chart_loading');
}

function GetSubscribers(page, limit) {
	var brand = $('#brand_id').val();
	if(page == 1) {
		ShowLoader('Getting Subscribers', 'list_subscribers_loading');
		$('#list_subscriber_container').hide();
	}
	var data = {'brand': brand, 'list_id': current_list_id, 'page': page, 'limit': limit}
	var url = "/api/subscribers/get"
	var method = "POST"
	AjaxCall(url, data, method, GetSubscribersSuccess, GetSubscribersError);
}

function GetSubscribersSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var table_id = "list_subscribers_table";
        var results = obj.Results;
        $('#list_subscribers_table_body').empty();
        $('#list_subscriber_table_head .merge-field-col').remove();
        var merge_fields = results.MergeFields;
        for(var idx = 0; idx < merge_fields.length; idx ++) {
        	var merge_field = merge_fields[idx];
        	var row = '<th class="merge-field-col" style="width:100px;">' + merge_field.name + '</th>';
        	$('#list_subscriber_table_head').append(row);
        }
        _DestroyDataTable(table_id);
        var subscriber_data = results.Data;
        for (var idx = 0; idx < subscriber_data.length; idx ++) {
        	var subscriber = subscriber_data[idx];
        	var row = '<tr>' +
        		'<td align="center" style="width:25px;"><input type="checkbox" class="list_subscribers_check" name="sub_check_' + subscriber.ID + '" id="sub_check_' + subscriber.ID + '" value="' + subscriber.ID + '" /></td>' +
        		'<td style="width:50px;">' + subscriber.ID + '</td>' + 
        		'<td style="width:400px;"><img src="/static/img/' + subscriber.Status + '.png" width="24px" alt="' + subscriber.Status + '" title="' + subscriber.Status + '" />&nbsp;<a href="/subscribers/' + subscriber.ID + '">' + subscriber.EmailAddress + '</a></td>' +
        		'<td style="width:150px;">' + subscriber.EmailTypePreference + '</td>' +
        		'<td style="width:200px;">' + subscriber.DateAdded + '</td>' +
        		'<td style="width:200px;">' + subscriber.LastModified + '</td>';
        	for(var midx = 0; midx < merge_fields.length; midx ++) {
	        	var merge_field = merge_fields[midx];
	        	row += '<td style="width:100px;overflow:hidden;">' + subscriber[merge_field.tag] + '</td>';
	        }
	        $('#list_subscribers_table_body').append(row);
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

		$('.list_subscribers_check').click(function() {
			cnt = ListCheckCount('list_subscribers');
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

	    HideLoader('list_subscribers_loading');
	    $('#list_subscriber_container').show();
	    $.fn.dataTable.tables( {visible: true, api: true} ).columns.adjust();
	    //table.fnAdjustColumnSizing();
    }
    else {
        alert(HandleErrors(obj));
        HideLoader('list_subscribers_loading');
    }
}

function GetSubscribersError(msg) {
    alert(msg);
    HideLoader('list_subscribers_loading');
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

function ListProperties() {
	$('.lists_check').each(function() {
		if($(this).is(':checked')) {
			location.href = "/lists/" + $(this).val() + "/properties"
		}
	});
}

//Merge Fields
function AddMergeField() {
	$('#submit_type').val('post');
	$('#merge_field_type_field').show();
	$('#merge_field_modal').modal('show');
}
function SetTag() {
	var name = $('#merge_field_name').val();
	var tag = $('#merge_field_tag').val();
	if(tag == "" && name != "") {
		tag = name.substring(0,10).toUpperCase().replace(/ /g, '');
		$('#merge_field_tag').val(tag);
	}
}
function ShowAdditionalFields() {
	var type = $('#merge_field_type').val();
	if(type != null) {
		var type_tag = type.replace(/ /g, '_')
		HideAdditionalOptions();
		if(type == "radio" || type == "dropdown") {
			var choices = ["First Choice", "Second Choice", "Third Choice"];
			var merge_field_choices = $('#merge_field_choices').val();
			if(merge_field_choices.length > 0) {
				choices = merge_field_choices.split('|');
			}
			InitChoices(choices);
		}
		else if ($('#' + type_tag + '_options').length > 0) {
			$('#' + type_tag + '_options').show();
		}
	}
}
function HideAdditionalOptions() {
	$('.additional_options').each(function() {
		$(this).hide();
	});
	$('#choice_options .dynamic-choice').remove();
}
function InitChoices(choices) {
	var name = $('#merge_field_name').val();
	if(choices.length > 0) {
		$('#choice_options h5').html(name + ' Choices');
		for(var idx = 0; idx < choices.length; idx ++) {
			var choice = choices[idx];
			var choice_num = idx + 1;
			AddDynamicChoice(choice_num, choice);
		}

		$('#choice_options').show();
	}
}

function AddDynamicChoice(choice_num, choice) {
	if(choice_num == -1) {
		$('#choice_options .dynamic-choice').each(function() {
			choice_num = parseInt($(this).attr('id')) + 1;
		});
	}
	var choice_field = '<div class="form-group dynamic-choice" id="' + choice_num + '">' + 
		'<label for="dynamic_choice_' + choice_num + '" class="control-label col-lg-2">' + choice_num + ':</label>' +
		'<div class="col-lg-8">' + 
			'<input type="text" class="form-control" id="dynamic_choice_' + choice_num + '" name="dynamic_choice_' + idx + '" value="' + choice + '" />' +
		'</div>' +
		'<div class="col-lg-2">' +
			'<a href="javascript:;" class="btn btn-xs btn-default" onClick="AddDynamicChoice(-1, \'New Choice\');">' + 
				'<img src="/static/img/add.png" width="16px" alt="+" title="Add Choice" />' + 
			'</a>&nbsp;' +
			'<a href="javascript:;" class="btn btn-xs btn-default" onClick="RemoveDynamicChoice(' + choice_num + ');">' + 
				'<img src="/static/img/remove.png" width="16px" alt="-" title="Remove Choice" />' + 
			'</a>' + 
		'</div></div>';
	$('#choice_options').append(choice_field);
}

function RemoveDynamicChoice(choice_num) {
	$('#choice_options .dynamic-choice[id="' + choice_num + '"]').remove();
}

function MergeFieldSubmit() {
	ShowLoader('Submitting Merge Field', 'merge_field_modal_loading');
	$('#merge_field_modal_content').hide();
	var brand = $('#brand_id').val();
	var list_id = current_list_id;
	var name = $('#merge_field_name').val();
	if(name == "") {
		alert('Enter a name');
		MergeFieldDoneLoading();
		return false;
	}
	var tag = $('#merge_field_tag').val();
	if(tag == "") {
		alert('Tag cannot be blank');
		MergeFieldDoneLoading();
		return false;
	}
	var old_tag = $('#merge_field_old_tag').val();
	var type = $('#merge_field_type').val();
	var required = 0;
	if($('#merge_field_required').is(':checked')) {
		required = 1;
	}
	var visible = 0;
	if($('#merge_field_visible').is(':checked')) {
		visible = 1;
	}
	var default_value = $('#merge_field_default_value').val();
	var display_order = $('#merge_field_display_order').val();
	if(display_order == "") {
		alert('Enter the display order');
		MergeFieldDoneLoading();
		return false;
	}

	var data = {'brand': brand, 'list_id': list_id, 'name': name, 'old_tag': old_tag, 'tag': tag, 'type': type, 'required': required, 'public': visible, 'default_value': default_value, 'display_order': parseInt(display_order), 'size': 0, "default_country":"", "date_format":"", "phone_format":"", "choice":[], "id": "", "merge_id":""};

	if(type == "radio" || type == "dropdown") {
		var choices = [];
		$('#choice_options .dynamic-choice').each(function() {
			var id = $(this).attr('id');
			choices.push($('#dynamic_choice_' + id).val());
		});
		if(choices.length == 0) {
			alert('No choices entered');
			MergeFieldDoneLoading();
			return false;
		}
		data['choice'] = choices
	}
	else if(type == 'text') {
		var max_length = $('#merge_field_max_length').val();
		if(max_length == "") {
			alert('Enter the max length');
			MergeFieldDoneLoading();
			return false;
		}
		data['size'] = max_length;
	}
	else if(type == "address") {
		var default_country = $('#merge_field_default_country').val();
		data['default_country'] = default_country
	}
	else if(type == "date") {
		var date_format = $('#merge_field_date_format').val();
		data['date_format'] = date_format;
	}
	else if(type == 'birthday') {
		var date_format = $('#merge_field_birthday_format').val();
		data['date_format'] = date_format;
	}
	else if(type == 'phone') {
		var phone_format = $('#merge_field_phone_format').val();
		data['phone_format'] = phone_format;
	}

	var submit_type = $('#submit_type').val();
	if(submit_type == "patch") {
		data['id'] = $('#merge_field_id').val();
		data['merge_id'] = $('#merge_field_mailchimp_id').val();
	}

	var url = "/api/list_merge_fields/" + submit_type;
	var method = "POST";

	AjaxCall(url, data, method, MergeFieldSubmitSuccess, MergeFieldSubmitError);
}

function MergeFieldSubmitSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	ResetModal('merge_field_modal');
        window.location.reload();
    }
    else {
        alert(HandleErrors(obj));
        MergeFieldDoneLoading();
    }
}

function MergeFieldSubmitError(msg) {
    alert(msg);
    MergeFieldDoneLoading();
}

function MergeFieldDoneLoading() {
	HideLoader('merge_field_modal_loading');
	$('#merge_field_modal_content').show();
}

function EditMergeField(mc_id, id) {
	$('#submit_type').val('patch');
	$('#merge_field_type_field').hide();
	$('#merge_field_modal').modal('show');
	ShowLoader('Loading Merge Field', 'merge_field_modal_loading');
	$('#merge_field_modal_content').hide();
	var data = {'brand': $('#brand_id').val(), 'list_id': current_list_id, 'id': id}
	var url = "/api/list_merge_fields/get_single"
	var method = "POST"
	AjaxCall(url, data, method, MergeFieldGetSuccess, MergeFieldGetError);
}

function MergeFieldGetSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        var merge_field = obj.Results[0]
        $('#merge_field_id').val(merge_field.id);
        $('#merge_field_mailchimp_id').val(merge_field.mailchimp_id);
        $('#merge_field_name').val(merge_field.name);
        $('#merge_field_tag').val(merge_field.tag);
        $('#merge_field_old_tag').val(merge_field.tag);
        $('#merge_field_type').val(merge_field.type);
        var required = merge_field.required
        if(required == '1' && !$('#merge_field_required').is(':checked')) {
        	$('#merge_field_required').click();
        }
        var visible = merge_field.public;
        if(visible == '0' && $('#merge_field_visible').is(':checked')) {
        	$('#merge_field_visible').click();
        }
        $('#merge_field_default_value').val(merge_field.default_value);
        $('#merge_field_display_order').val(merge_field.display_order);
        $('#merge_field_max_length').val(merge_field.size);
        $('#merge_field_default_country').val(merge_field.default_country);
        
        if(merge_field.type == 'date') {
	        $('#merge_field_date_format').val(merge_field.date_format);
	    }
	    else if(merge_field.type == "birthday") {
        	$('#merge_field_birthday_format').val(merge_field.date_format);
        }
        $('#merge_field_choices').val(merge_field.choices);
        ShowAdditionalFields();
        MergeFieldDoneLoading();
    }
    else {
        alert(HandleErrors(obj));
        MergeFieldDoneLoading();
    }
}

function MergeFieldGetError(msg) {
    alert(msg);
    MergeFieldDoneLoading();
}

function DeleteMergeField(mc_id, id) {
	var conf = confirm('Are you sure?');
	if(!conf) {
		return false;
	}
	$('#merge_field_modal').modal('show');
	ShowLoader('Deleting Merge Field', 'merge_field_modal_loading');
	$('#merge_field_modal_content').hide();

	var url = '/api/list_merge_fields/delete'
	var method = "POST"
	var data = {'brand': $('#brand_id').val(), 'list_id': current_list_id, 'merge_id': mc_id, 'id': id}
	AjaxCall(url, data, method, DeleteMergeFieldSuccess, DeleteMergeFieldError);
}

function DeleteMergeFieldSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	$('#merge_field_modal').modal('hide');
        document.location.reload();
    }
    else {
        alert(HandleErrors(obj));
        $('#merge_field_modal').modal('hide');
        MergeFieldDoneLoading();
    }
}

function DeleteMergeFieldError(msg) {
    alert(msg);
    $('#merge_field_modal').modal('hide');
    MergeFieldDoneLoading();
}

function DeleteSelectedSubscribers() {
	subscribers_to_delete = CheckedRows('list_subscribers');
	if(subscribers_to_delete.length > 0) {
		conf = confirm('Are you sure you want to delete ' + subscribers_to_delete.length + ' subscribers?\nThis operation CANNOT be undone!');
		if(!conf) {
			return false;
		}

		ShowLoader('Deleting Selected Subscribers', 'merge_field_modal_loading');
		$('#merge_field_modal_content').hide();
		$('#merge_field_modal').modal('show');
		var data = {'brand': $('#brand_id').val(), 'list_id': current_list_id, 'subscriber': subscribers_to_delete}
		var url = "/api/subscribers/delete"
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
    	$('#merge_field_modal').modal('hide');
        document.location.reload();
    }
    else {
        alert(HandleErrors(obj));
        $('#merge_field_modal').modal('hide');
        MergeFieldDoneLoading();
    }
}

function DeleteSubscriberError(msg) {
    alert(msg);
    $('#merge_field_modal').modal('hide');
    MergeFieldDoneLoading();
}