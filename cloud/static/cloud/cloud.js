$(document).ready(function() {
	var selected_entry;

	open_folder(current_folder);

	$('#parent').click(function(){
		open_folder(current_folder.replace(/[^/]+\/$/, ''));
	});

	$('#delete').click(function(){
		if (!selected_entry) return;
		$.ajax({
			url: '/cloud/delete',
			type: 'POST',
			data: {
				'folder': current_folder,
				'path': selected_entry
			},
			success: fill_table
		});
	});

	$('#rename').click(function(){
		if (!selected_entry) return;
		var new_name = prompt("New name:", selected_entry);
		// should do checks on new_name
		if (new_name != null && new_name != "") {
			$.ajax({
				url: '/cloud/rename',
				type: 'POST',
				data: {
					'folder': current_folder,
					'old_path': selected_entry,
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
		$.ajax({
			url: '/cloud/copy',
			type: 'POST',
			data: {
				'path': current_folder+selected_entry
			},
			success: function(data) {
				$('#paste').prop('disabled', false);
			}
		});

	});

	$('#cut').click(function(){
		$.ajax({
			url: '/cloud/cut',
			type: 'POST',
			data: {
				'path': current_folder+selected_entry
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

	function fill_table(entries) {
		content = '';
		entries.forEach(function(entry) {
			content += '<tr>';
			content += '<td class="entry-name type-'+entry['type']+'">'+entry['name']+'</td>';
			content += '<td>'+entry['size']+'</td>';
			content += '<td>'+entry['last_mod']+'</td>';
			content += '</tr>';
		});
		$('#table-files tbody').html(content);
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
				$('#table-files tbody tr').unbind("click").click( function () {
					selected_entry = current_folder+$(this).find(".entry-name").text();
					$('#table-files>tbody>tr').removeClass('checked-table-row');
					$(this).addClass('checked-table-row');
		
					$('#copy').prop('disabled', false);
					$('#cut').prop('disabled', false);
					$('#delete').prop('disabled', false);
					$('#rename').prop('disabled', false);
				});
		
				$('.entry-name.type-dir').unbind("dblclick").dblclick(function() {
					open_folder(selected_entry+'/');
				});
				
				$('#parent').prop('disabled', !current_folder);
			}
		});
	}

});