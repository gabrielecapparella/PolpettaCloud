let pc;
class PolpettaCloud {
    constructor(root, current_folder, visualization_mode, files, trash) {
        pc = this;
        this.current_folder = current_folder;
        this.files = files;
        this.trash = trash;
        this.root = root;
        this.update_files(files, false);
        this.set_visualization_mode(visualization_mode);
        this.fill_info();
        this.build_path_bar();
    }

    update_files(new_files, fill=true) {
        pc.files = new_files;
        pc.last_selected_index = -1;
        pc.selected_entries = [];
        pc.selected_indexes = [];
        pc.fill_info();
        if (fill) {
			if (pc.visualization_mode === "table") pc.fill_table();
			else pc.fill_grid();
		}
    }

    update_folder() {
		$.ajax({
			type: "POST",
			url: "/cloud/get-folder",
			data: { 'folder': pc.root+pc.current_folder },
			success: pc.update_files
		});
	}

    set_visualization_mode(mode) {
		pc.visualization_mode = mode;
		if (mode==="table") {
			$('#show-table').hide();
			$('#table-container').show();
			$('#show-grid').show();
			$('#grid-container').hide();
			pc.fill_table();
		} else {
			$('#show-table').show();
			$('#table-container').hide();
			$('#show-grid').hide();
			$('#grid-container').show();
			pc.fill_grid();
		}
	}

    fill_table() {
		let content = '';
		pc.files.forEach(function(entry) {
			content += '<tr class="entry">';
			content += '<td class="entry-name type-'+entry['type']+'">'+entry['name']+'</td>';
			content += '<td>'+entry['size']+'</td>';
			content += '<td>'+entry['last_mod']+'</td>';
			content += '</tr>';
		});

		$('#table-files tbody').html(content);
	}

	fill_grid() {
		let content = '';
		let pic;
		pc.files.forEach(function(entry) {
			content += '<div class="entry grid-element" title="'+entry['name']+'">';
			pic = '<img src="'+pc.get_icon_url(entry['name'], entry['type'])+'" class="grid-pic-horizontal">';
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

	fill_info() {
        let name, img;
        let size = 0;
        if (pc.selected_indexes.length < 1) {
            name = pc.current_folder;
            img = "/static/cloud/pics/icons/folder.png";
            pc.files.forEach(function (entry) {
                size += entry["raw_size"];
            });
            size = readable_size(size);
        } else if (pc.selected_indexes.length === 1) {
            let sel = pc.files[pc.selected_indexes[0]];
            name = sel['name'];
            img = pc.get_icon_url(sel["name"], sel["type"]);
            size = sel["size"];
        } else {
            name = "Multiple files";
            img = "/static/cloud/pics/icons/files.png";
            pc.selected_indexes.forEach(function (i) {
                size += pc.files[i]["raw_size"];
            });
            size = readable_size(size);
        }
        $('#info-name').text(name).prop("title", name);
        $('#info-img').html('<img src="' + img + '" class="grid-pic-horizontal">');
        $('#info-size> span').text(size);
        let img_el = $('#info-img > img').first();
        if (img_el.height() < img_el.width()) {
            img_el.attr("class", "grid-pic-vertical");
        }
    }

	get_icon_url(filename, filetype) {
		if (filetype==="dir") {
			return '/static/cloud/pics/icons/folder.png';
		} else if (filename.endsWith(".jpg") || filename.endsWith(".png")) {
			if (trash) return '/cloud/get-trash/'+pc.current_folder+"/"+filename;
			return '/cloud/get-file/'+pc.current_folder+"/"+filename;
		} else if (filename.endsWith(".pdf")) {
			return '/static/cloud/pics/icons/pdf.png';
		} else if (filename.endsWith(".txt")) {
			return '/static/cloud/pics/icons/txt.png';
		} else {
			return '/static/cloud/pics/icons/file.png';
		}
	}

	build_path_bar() {
		let nav_path = $("#nav-path");
		nav_path.html("");
		let cur_path = "";
		let path = pc.current_folder;
		if (path.length>0) path = "/"+path;
		path.split("/").forEach(function(folder) {
			cur_path += folder+"/";
			nav_path.append($("<div class='nav-path-button' data-path='"+cur_path+"'>").text(folder+"/"));
		});
		$(".nav-path-button").click(function(){
			let t = "";
			if (trash) t = "-";
			window.location.href = window.location.origin + "/cloud/-" + t + $(this).attr("data-path");
		});
	}

	click_entry(event, element, selector) {
		if (event.ctrlKey) {
			element.toggleClass('checked-entry');
			pc.last_selected_index = element.index();
		} else if (event.shiftKey && pc.last_selected_index>-1) {
			let indexes = [element.index(), pc.last_selected_index];
			indexes.sort(function(a, b){return a-b});
			for (let i = indexes[0]; i <= indexes[1]; i++) {
				$(selector).eq(i).addClass('checked-entry');
			}
			pc.last_selected_index = -1;
		} else {
			$("#main .checked-entry").removeClass('checked-entry');
			element.addClass('checked-entry');
			pc.last_selected_index = element.index();
		}

		pc.selected_entries = [];
		pc.selected_indexes = [];
		$('.checked-entry').each(function() {
			pc.selected_entries.push($(this).find(".entry-name").text());
			pc.selected_indexes.push($(this).index());
		});

		let l = pc.selected_entries.length;
		if (l>0) {
			if (pc.trash) {
				$('#perm-delete, #restore').show();
			} else {
				$('#copy, #cut, #delete, #paste, #download').show();
				if (l === 1) $('#rename').show();
				else $('#rename').hide();
			}
		} else {
			$('#copy, #cut, #delete, #paste, #rename, #restore').hide();
		}
		pc.fill_info();
		console.log("sel_entries: "+pc.selected_entries);
	}

	action_delete() {
        if (!pc.selected_entries.length) return;
        $.ajax({
            url: '/cloud/delete',
            type: 'POST',
            data: {
                'folder': pc.root+pc.current_folder,
                'to_delete': pc.selected_entries
            },
            success: pc.update_files
        });
    }

    action_restore() {
        if (!pc.selected_entries.length) return;
        $.ajax({
            url: '/cloud/restore',
            type: 'POST',
            data: {
                'folder': pc.root+pc.current_folder,
                'to_restore': pc.selected_entries
            },
            success: pc.update_files
        });
    }

    action_perm_delete() {
        if (!pc.selected_entries.length) return;
        $.ajax({
            url: '/cloud/perm-delete',
            type: 'POST',
            data: {
                'folder': pc.root+pc.current_folder,
                'to_delete': pc.selected_entries
            },
            success: pc.update_files
        });
    }

    action_download() {
        if (!pc.selected_entries.length) return;
		let fd = new FormData();
		fd.append('folder', pc.root+pc.current_folder);
		pc.selected_entries.forEach(function(entry) {
			fd.append('to_download[]', entry);
		});
		let request = new XMLHttpRequest();
		request.open("POST", "/cloud/download");
		request.responseType = 'blob';
		request.send(fd);
		request.onload = function(e) {
			let blob = new Blob([this.response], {type: this.response.type});
			let hidden_a = $('#downloader');
			let url = window.URL.createObjectURL(blob);
			hidden_a.attr('href', url);
			hidden_a.attr('download', this.getResponseHeader("FILENAME"));
			hidden_a[0].click();
			window.URL.revokeObjectURL(url);
		};
    }

    action_rename() {
        if (pc.selected_entries.length!==1) return;
		let new_name = prompt("New name:", pc.selected_entries[0]);
		// TODO: checks on new_name
		if (new_name != null && new_name !== "") {
			$.ajax({
				url: '/cloud/rename',
				type: 'POST',
				data: {
					'folder': pc.root+pc.current_folder,
					'old_path': pc.selected_entries[0],
					'new_path': new_name
				},
				success: pc.update_files
			});
		}
    }

    action_create_folder() {
        let name = prompt("Folder name:", "polpetta");
		if (name != null && name !== "") {
			$.ajax({
				url: '/cloud/create-folder',
				type: 'POST',
				data: {
					'folder': pc.root+pc.current_folder,
					'name': name
				},
				success: pc.update_files
			});
		}
    }

    action_copy() {
        if (!pc.selected_entries.length) return;
		$.ajax({
			url: '/cloud/copy',
			type: 'POST',
			data: {
				'folder': pc.root+pc.current_folder,
				'to_copy[]': pc.selected_entries
			},
			success: function() {
				$('#paste').show();
			}
		});
    }

    action_cut() {
        if (!pc.selected_entries.length) return;
		$.ajax({
			url: '/cloud/cut',
			type: 'POST',
			data: {
				'folder': pc.root+pc.current_folder,
				'to_cut': pc.selected_entries
			},
			success: function() {
				$('#paste').show();
			}
		});
    }

    action_paste() {
        $.ajax({ url: '/cloud/paste',
			type: 'POST',
			data: {
				'folder': pc.root+pc.current_folder
			},
			success: pc.update_files
		});
    }

    action_upload_file() {
        let fd = new FormData();
		let files_to_upload = $("#upload-files-hidden")[0].files;
		for (let i = 0; i < files_to_upload.length; i++) {
			fd.append('files[]', files_to_upload[i]);
		}
		fd.append('folder', pc.root+pc.current_folder);

		$.ajax({
			url: '/cloud/upload-files',
			type: 'POST',
			data: fd,
			cache: false,
			contentType: false,
			processData: false,
			success: pc.update_files
		});
		$('#upload-files-hidden').val('');
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

