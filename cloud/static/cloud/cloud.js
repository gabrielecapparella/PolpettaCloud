document.onselectstart = function() {
    return false;
}

$(document).ready(function() {
	var selected_entries = [];
	var last_selected_index = -1;

	open_folder(current_folder);

	$('#parent').click(function(){
		open_folder(current_folder.replace(/[^/]+\/$/, ''));
	});

	$('#delete').click(function(){
		if (!selected_entries.length) return;
		$.ajax({
			url: '/cloud/delete',
			type: 'POST',
			data: {
				'folder': current_folder,
				'to_delete': selected_entries
			},
			success: fill_table
		});
	});

	$('#rename').click(function(){
		if (selected_entries.length!=1) return;
		var new_name = prompt("New name:", selected_entries[0]);
		// should do checks on new_name
		if (new_name != null && new_name != "") {
			$.ajax({
				url: '/cloud/rename',
				type: 'POST',
				data: {
					'folder': current_folder,
					'old_path': selected_entries[0],
					'new_path': current_folder+new_name
				},
				success: fill_table
			});
		}
	});

	$('#create-folder').click(function(){
		var name = prompt("Folder name:", "polpetta");
		if (name != null && name != "") {
			$.ajax({
				url: '/cloud/create-folder',
				type: 'POST',
				data: {
					'folder': current_folder,
					'name': name
				},
				success: fill_table
			});
		}
	});

	$('#copy').click(function(){
		if (!selected_entries.length) return;
		$.ajax({
			url: '/cloud/copy',
			type: 'POST',
			data: {
				'to_copy[]': selected_entries
			},
			success: function(data) {
				$('#paste').prop('disabled', false);
			}
		});

	});

	$('#cut').click(function(){
		if (!selected_entries.length) return;
		$.ajax({
			url: '/cloud/cut',
			type: 'POST',
			data: {
				'to_cut': selected_entries
			},
			success: function(data) {
				$('#paste').prop('disabled', false);
			}
		});

	});

	$('#paste').click(function(){
		$.ajax({ url: '/cloud/paste',
			type: 'POST',
			data: {
				'folder': current_folder
			},
			success: fill_table
		});

	});

	$('#upload-files').click(function() {
		$('#upload-files-hidden').trigger('click');
	});

	$('#upload-files-hidden').change(function () {
		var fd = new FormData();
		var files = $("#upload-files-hidden")[0].files;
		for (i = 0; i < files.length; i++) {
			fd.append('files[]', files[i]);
		}
		fd.append('folder', current_folder);

		$.ajax({
			url: '/cloud/upload-files',
			type: 'POST',
			data: fd,
			cache: false,
			contentType: false,
			processData: false,
			success: fill_table
		});
		$('#upload-files-hidden').val('');
	});

	function fill_table(entries) {
		selected_entries = [];
		last_selected = null;

		content = '';
		entries.forEach(function(entry) {
			content += '<tr>';
			content += '<td class="entry-name type-'+entry['type']+'">'+entry['name']+'</td>';
			content += '<td>'+entry['size']+'</td>';
			content += '<td>'+entry['last_mod']+'</td>';
			content += '</tr>';
		});
		$('#table-files tbody').html(content);
		$('#table-files tbody tr').unbind("click").click( function(event) {
			console.log(event.shiftKey);
			console.log(last_selected_index);
			if (event.ctrlKey) {
				$(this).toggleClass('checked-table-row');
				last_selected_index = $(this).index();
			} else if (event.shiftKey && last_selected_index>-1) {
				indexes = [$(this).index(), last_selected_index];
				indexes.sort(function(a, b){return a-b});
				for (var i = indexes[0]; i <= indexes[1]; i++) {
					$('#table-files tbody tr').eq(i).addClass('checked-table-row');
				}
				last_selected_index = -1;
			} else {
				$('#table-files>tbody>tr').removeClass('checked-table-row');
				$(this).addClass('checked-table-row');
				last_selected_index = $(this).index();
			}

			selected_entries = [];
			$('.checked-table-row').each(function() {
				selected_entries.push(current_folder+$(this).find(".entry-name").text());
			});	

			l = selected_entries.length
			$('#copy').prop('disabled', !l);
			$('#cut').prop('disabled', !l);
			$('#delete').prop('disabled', !l);
			$('#rename').prop('disabled', l!=1);
			console.log(selected_entries);
		});

		$('.entry-name.type-dir').unbind("dblclick").dblclick(function() {
			open_folder(selected_entries+'/');
		});		
	}

	function open_folder(path) {
		current_folder = path;
		$.ajax({
			type: "POST",
			url: "/cloud/get-folder",
			data: {
			  'folder': path
			},
			success: function(data) {
				fill_table(data);
				$('#parent').prop('disabled', !current_folder);
				$('header').html('PolpettaCloud - /'+current_folder);
			}
		});
	}

});