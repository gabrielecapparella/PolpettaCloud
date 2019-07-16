$(document).ready(function() {
	var current_folder = '';
	var selected_entry;

	$.ajax({
		type: "POST",
		url: "/cloud/get-folder",
		data: {
		  'folder': ''
		},
		success: fill_table
	});

	$('#delete').click(function(){
		if (!selected_entry) return;
		$.ajax({ url: '/delete',
			type: 'POST',
			contentType: 'application/json',
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
			$.ajax({ url: '/rename',
				type: 'POST',
				contentType: 'application/json',
				data: {
					'folder': current_folder,
					'old_path': selected_entry,
					'new_path': current_folder.concat(new_name)
				},
				success: fill_table
			});
		}
	});

	$('#create-folder').click(function(){
		var name = prompt("Folder name:", "polpetta");
		if (name != null && name != "") {
			$.ajax({ url: '/create-folder',
				type: 'POST',
				contentType: 'application/json',
				data: {
					'folder': current_folder,
					'name': name
				},
				success: fill_table
			});
		}
	});

	function fill_table(entries) {
		content = '';
		entries.forEach(function(entry) {
			content += '<tr>';
			content += '<td class="entry-name">'+entry[0]+'</td>';
			content += '<td>'+entry[1]+'</td>';
			content += '<td>'+entry[2]+'</td>';
			content += '</tr>';
		});
		$('#table-files tbody').html(content);
		$('#table-files tbody tr').unbind("click").click( function () {
			selected_entry = current_folder.concat($(this).find(".entry-name").text());
			$('#table-files>tbody>tr').removeClass('checked-table-row');
			$(this).addClass('checked-table-row');
		});
	}

});