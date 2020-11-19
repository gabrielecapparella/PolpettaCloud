$(document).ready(function() {
	let current_folder = window.location.pathname.replace(/^(\/cloud\/)/, "").replace(/^(-\/)/, "");
	let last_selected_index = -1;
	let files = [];
	let selected_entries = [];
	let visualization_mode = null;

	$('#parent').prop('disabled', !current_folder);
	$('header').html('PolpettaCloud - /'+current_folder);

	$.ajax({
		type: "POST",
		url: "/cloud/get-folder",
		data: { 'folder': current_folder },
		success: function(data) {
			set_visualization_mode("grid");
			update_files(data);
		}
	});

	$('#table-container, #grid-container').on("mousedown", function(e) {
		if (e.shiftKey) e.preventDefault();
	});

	$('#table-files').on("click", "tbody tr", function(event) {
		click_entry(event, $(this), '#table-files tbody tr');
	});

	$('#grid-container').on("click", ".grid-element", function(event) {
		click_entry(event, $(this), '#grid-container>.grid-element');
	});

	$('#main').on("dblclick", ".type-dir", function() {
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
			success: update_files
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
				success: update_files
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
				success: update_files
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
			success: update_files
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
			success: update_files
		});
		$('#upload-files-hidden').val('');
	});

	$('#show-grid').click(function(){
		set_visualization_mode("grid");
	});

	$('#show-table').click(function(){
		set_visualization_mode("table");
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

	function set_visualization_mode(mode) {
		visualization_mode = mode;
		if (mode==="table") {
			$('#show-table').hide();
			$('#table-container').show();
			$('#show-grid').show();
			$('#grid-container').hide();
			fill_table();
		} else {
			$('#show-table').show();
			$('#table-container').hide();
			$('#show-grid').hide();
			$('#grid-container').show();
			fill_grid();
		}
	}

	function update_files(new_files) {
		files = new_files;
		if (visualization_mode==="table") fill_table();
		else fill_grid();
	}

	function click_entry(event, element, selector) {
		if (event.ctrlKey) {
			element.toggleClass('checked-entry');
			last_selected_index = element.index();
		} else if (event.shiftKey && last_selected_index>-1) {
			let indexes = [element.index(), last_selected_index];
			indexes.sort(function(a, b){return a-b});
			for (let i = indexes[0]; i <= indexes[1]; i++) {
				$(selector).eq(i).addClass('checked-entry');
			}
			last_selected_index = -1;
		} else {
			$("#main .checked-entry").removeClass('checked-entry');
			element.addClass('checked-entry');
			last_selected_index = element.index();
		}

		selected_entries = [];
		$('.checked-entry').each(function() {
			selected_entries.push(current_folder+$(this).find(".entry-name").text());
		});

		let l = selected_entries.length
		$('#copy').prop('disabled', !l);
		$('#cut').prop('disabled', !l);
		$('#delete').prop('disabled', !l);
		$('#rename').prop('disabled', l!=1);
		console.log(selected_entries);
		fill_info(selected_entries);
	}

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

	function fill_table() {
		last_selected_index = -1;
		let content = '';
		files.forEach(function(entry) {
			content += '<tr class="entry">';
			content += '<td class="entry-name type-'+entry['type']+'">'+entry['name']+'</td>';
			content += '<td>'+entry['size']+'</td>';
			content += '<td>'+entry['last_mod']+'</td>';
			content += '</tr>';
		});

		$('#table-files tbody').html(content);
	}

	function fill_grid() {
		last_selected_index = -1;
		let content = '';
		let pic;
		files.forEach(function(entry) {
			content += '<div class="entry grid-element">';
			if (entry['name'].endsWith(".jpg") || entry['name'].endsWith(".png")) {
				pic = '<img src="/cloud/get-file/'+current_folder+entry['name']+'" class="grid-pic-horizontal">';
			} else {
				pic = entry['type'];
			}
			content += '<div class="grid-pic">'+pic+'</div>';
			content += '<div class="grid-text entry-name type-'+entry['type']+'">'+entry['name']+'</div>';
			content += '</div>';
		});
		$('#grid-container').html(content);
		$('.grid-pic-horizontal').each(function () {
			if ($(this).height()>$(this).width()) {
				$(this).attr("class", "grid-pic-vertical");
			}
		});
	}
});