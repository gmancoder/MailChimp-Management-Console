var editor;
var form = 'form';
$(document).ready(function() {
	if($('#emails_table').length > 0) {
		$('#import_objects_button').hide();
		$('#export_objects_button').hide();

		$('#emails_table').DataTable({
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
	else if($('#emails_form').length > 0) {
		editor = ace.edit("editor");
		editor.setTheme("ace/theme/twilight");
		editor.getSession().setMode("ace/mode/html");
		toggleFolderView('form');
		ResizeMergeButtonText();
	}
});

function ResizeMergeButtonText() {
	$('.merge_tag_button').each(function() {
		var font_size = 14;
		$(this).find('span:first').css('font-size', font_size + 'px');
        var tag = $(this).html();
        var width = $(this).find('span:first').width();
        var i_width = $(this).width();
        while(width > i_width) {
            font_size -= 1;
            $(this).find('span:first').css('font-size', font_size + 'px');
            width = $(this).find('span:first').width();
        }
    });
}

function DisabledButton() {
	event.preventDefault();
}

function SaveHTML() {
	var sections = [];
	var content = "";
	if($('#html_section_form').length > 0) {
		$('.email_section_textarea').each(function() {
			var tag = $(this).attr('id');
			var s_content = $(this).val();
			var j_value = tag + '#||#' + s_content;
			sections.push(j_value);
		});
	}
	else {
		content = editor.getValue();
	}
	var email_id = $('#email_id').val();
	var brand = $('#brand_id').val();

	var data = {'brand': brand, 'email_id': email_id, 'content': content, 'section': sections}
    var url = "/api/emails/savehtml";
    var method = "POST"

    AjaxCall(url, data, method, SaveHTMLSuccess, SaveHTMLError);
}
function SaveHTMLSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
    	var html = obj.Results;
    	$('#html_preview').html(html);
        alert("HTML Saved Successfully");
    }
    else {
        alert(HandleErrors(obj));
    }
}

function SaveHTMLError(msg) {
    alert(msg);
}

function SubmitEmailForm(type) {
	if(form == 'form') {
		$('#' + type + '_form').submit()
	}
	else if (form == 'html') {
		SaveHTML();
	}
	else {
		return false;
	}
}
function ChangeForm(f) {
	form = f;
	if(form == 'preview') {
		$('.email_action').each(function() {
			$(this).hide();
		})
	}
	else {
		$('.email_action').each(function() {
			$(this).show();
		})
	}
}

function LoadPreview() {
	
}

function AddTag(tag) {
	editor.insert(tag);
}

function ToggleList(list) {
	$('#' + list).slideToggle();
}

function EditContent(tag) {
	$('#email_section_name').html(tag);
	$('#template_section_tag').val(tag);
	editor.setValue($('#' + tag).val());
	$('#edit_html_content_modal').modal('show');
}

function SaveHTMLSection() {
	var tag = $('#template_section_tag').val();
	$('#' + tag).val(editor.getValue());
	$('#edit_html_content_modal').modal('hide');
}