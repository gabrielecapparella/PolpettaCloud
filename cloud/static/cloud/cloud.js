$(document).ready(function() {
	let current_folder = window.location.pathname
		.replace(/^(\/cloud\/)/, "").replace(/^(-)/, "").replace(/\/$/, "");
	let last_selected_index = -1;
	let files = [];
	let selected_entries = [];
	let visualization_mode = null;

	$('#parent').prop('disabled', !current_folder);

	$.ajax({
		type: "POST",
		url: "/cloud/get-folder",
		data: { 'folder': current_folder },
		success: function(data) {
			set_visualization_mode("grid");
			update_files(data);
			fill_info([]);
			build_path_bar();
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
			window.location.href = window.location.origin+"/cloud/-/"+$(this).html();
		} else {
			window.location.href = window.location.origin+"/cloud/-"+current_folder+"/"+$(this).html();
		}
	});

	$('#parent').click(function(){
		window.location.href = window.location.href.replace(/\/[^/]+$/, ''); // magic
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

	function build_path_bar() {
		let nav_path = $("#nav-path");
		let cur_path = "";
		nav_path.html("");
		current_folder.split("/").forEach(function(folder) {
			cur_path += folder+"/";
			nav_path.append($("<div class='nav-path-button' data-path='"+cur_path+"'>").text(folder+"/"));
		});
		$(".nav-path-button").click(function(){
			window.location.href = window.location.origin + "/cloud/-" + $(this).attr("data-path");
		});
	}

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
		let selected_indexes = [];
		$('.checked-entry').each(function() {
			selected_entries.push(current_folder+$(this).find(".entry-name").text());
			selected_indexes.push($(this).index());
		});

		let l = selected_entries.length;
		$('#copy').prop('disabled', !l);
		$('#cut').prop('disabled', !l);
		$('#delete').prop('disabled', !l);
		$('#rename').prop('disabled', l!=1);

		fill_info(selected_indexes);
	}

	function fill_info(selected_indexes) {
		let name, img;
		let size = 0;
		if (selected_indexes.length<1) {
			name = current_folder || "/";
			img = "/static/cloud/pics/folder.png";
			files.forEach(function(entry) {
				size += entry["raw_size"];
			});
			size = readable_size(size);
		} else if (selected_indexes.length==1) {
			let sel = files[selected_indexes[0]];
			name = sel['name'];
			img = get_icon_url(sel["name"], sel["type"]);
			size = sel["size"];
		} else {
			name = "Multiple files";
			img = "/static/cloud/pics/files.png";
			selected_indexes.forEach(function(i) {
				size +=files[i]["raw_size"];
			});
			size = readable_size(size);
		}
		$('#info-name').text(name);
		$('#info-img').html('<img src="'+img+'" class="grid-pic-horizontal">');
		$('#info-size').text("Size: "+size);
		let img_el = $('#info-img > img').first();
		if (img_el.height()<img_el.width()) {
			img_el.attr("class", "grid-pic-vertical");
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
			pic = '<img src="'+get_icon_url(entry['name'], entry['type'])+'" class="grid-pic-horizontal">';
			content += '<div class="grid-pic">'+pic+'</div>';
			content += '<div class="grid-text entry-name type-'+entry['type']+'">'+entry['name']+'</div>';
			content += '</div>';
		});
		$('#grid-container').html(content);
		$('.grid-pic > .grid-pic-horizontal').each(function () {
			if ($(this).height()>$(this).width()) {
				$(this).attr("class", "grid-pic-vertical");
			}
		});
	}

	function get_icon_url(filename, filetype) {
		if (filetype=="dir") {
			return '/static/cloud/pics/folder.png';
		} else if (filename.endsWith(".jpg") || filename.endsWith(".png")) {
			return '/cloud/get-file/'+current_folder+filename;
		} else if (filename.endsWith(".pdf")) {
			return '/static/cloud/pics/pdf.png';
		} else if (filename.endsWith(".txt")) {
			return '/static/cloud/pics/txt.png';
		} else {
			return '/static/cloud/pics/file.png';
		}
	}

	function readable_size(raw_size) {
		let unit = ["B", "KB", "MB", "GB", "TB"];
		let i = 0;
		while ((raw_size/1000)>=1) {
			i++;
			raw_size /= 1000;
		}
		return raw_size.toFixed(2)+unit[i];
	}
});