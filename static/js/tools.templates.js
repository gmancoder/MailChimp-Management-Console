var editor;
var form = 'form';
$(document).ready(function() {
	if($('#templates_table').length > 0) {
		$('#import_objects_button').hide();
		$('#export_objects_button').hide();
		$('#search_objects_button').hide();

		$('#templates_table').DataTable({
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
	else if($('#templates_form').length > 0) {
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
	var content = editor.getValue();
	var template_id = $('#template_id').val();
	var brand = $('#brand_id').val();

	var data = {'brand': brand, 'template_id': template_id, 'content': content}
    var url = "/api/templates/savehtml";
    var method = "POST"

    AjaxCall(url, data, method, SaveHTMLSuccess, SaveHTMLError);
}
function SaveHTMLSuccess(data) {
    obj = JSON.parse(data);
    if(obj.Status == "OK") {
        alert("HTML Saved Successfully");
    }
    else {
        alert(HandleErrors(obj));
    }
}

function SaveHTMLError(msg) {
    alert(msg);
}

function SubmitTemplateForm(type) {
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
		$('.template_action').each(function() {
			$(this).hide();
		})
	}
	else {
		$('.template_action').each(function() {
			$(this).show();
		})
	}
}

function LoadPreview() {
	var content = editor.getValue();
	$('#html_preview').html(content);
}

function AddTag(tag) {
	editor.insert(tag);
}

function ToggleList(list) {
	$('#' + list).slideToggle();
}