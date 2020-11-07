// document.onselectstart = function(e) {
//     if (e.shiftKey) return false;
// }

$(document).ready(function() {
	let current_folder = window.location.pathname.replace(/^(\/cloud\/)/, "").replace(/^(-\/)/, "");
	let last_selected_index = -1;
	let files = [];

	$('#parent').prop('disabled', !current_folder);
	$('header').html('PolpettaCloud - /'+current_folder);

	$.ajax({
		type: "POST",
		url: "/cloud/get-folder",
		data: { 'folder': current_folder },
		success: function(data) {
			fill_table(data);
		}
	});

	$('#table-files').on("mousedown", function(e) {
		if (e.shiftKey) e.preventDefault();
	});

	$('#table-files').on("click", "tbody tr", function(event) {
			console.log(event.shiftKey);
			console.log(last_selected_index);
			if (event.ctrlKey) {
				$(this).toggleClass('checked-table-row');
				last_selected_index = $(this).index();
			} else if (event.shiftKey && last_selected_index>-1) {
				let indexes = [$(this).index(), last_selected_index];
				indexes.sort(function(a, b){return a-b});
				for (let i = indexes[0]; i <= indexes[1]; i++) {
					$('#table-files tbody tr').eq(i).addClass('checked-table-row');
				}
				last_selected_index = -1;
			} else {
				$('#table-files>tbody>tr').removeClass('checked-table-row');
				$(this).addClass('checked-table-row');
				last_selected_index = $(this).index();
			}

			let selected_entries = [];
			$('.checked-table-row').each(function() {
				selected_entries.push(current_folder+$(this).find(".entry-name").text());
			});

			let l = selected_entries.length
			$('#copy').prop('disabled', !l);
			$('#cut').prop('disabled', !l);
			$('#delete').prop('disabled', !l);
			$('#rename').prop('disabled', l!=1);
			console.log(selected_entries);
			fill_info(selected_entries);
		});
		$('#table-files').on("dblclick", ".type-dir", function() {
			if (!current_folder) {
				window.location.href = window.location.href+"-/"+$(this).html()+'/';
			} else {
				window.location.href = window.location.href+$(this).html()+'/';
			}
		});

	$('#parent').click(function(){
		window.location.href = window.location.href.replace(/[^/]+\/$/, ''); // magic
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

/*	$('#synch-drive').click(function(){
		if (selected_entries.length!=1) return;
		$.ajax({
			url: '/cloud/synch-gdrive',
			type: 'POST',
			data: {
				'path': current_folder+selected_entries[0]
			},
			success: fill_info
		});
	});*/

	function fill_info(selected_entries) {
		if (selected_entries.length<1) { 
			// TODO: main folder
		} else if (selected_entries.length==1) {
			sel = files[last_selected_index];
			$('#info-name').html(sel['name']);
			$('#info-size').html(sel['size']);
			$.ajax({
				url: '/cloud/get-info',
				type: 'POST',
				data: {
					'path': current_folder+sel['name']
				},
				success: function(data) {
					if(data['gdrive_sync']){
						$('#synch-drive').html("Unsynchronize");
					} else {
						$('#synch-drive').html("Synchronize");
					}					
				}
			});
		} else {
			// TODO: multiple files
		}
	}

	function fill_table(entries) {
		last_selected_index = -1;
		files = entries;

		let content = '';
		entries.forEach(function(entry) {
			content += '<tr>';
			content += '<td class="entry-name type-'+entry['type']+'">'+entry['name']+'</td>';
			content += '<td>'+entry['size']+'</td>';
			content += '<td>'+entry['last_mod']+'</td>';
			content += '</tr>';
		});
		$('#table-files tbody').html(content);
	}
});