let current_folder = window.location.pathname.replace(/^(\/cloud\/)/, "").replace(/\/$/, "");
let trash;

$(document).ready(function() {
	if (current_folder.startsWith("--")) {
		trash = true;
		current_folder = current_folder.replace(/^(--)/, "");
		$('#menu-trash').addClass("checked-menu");
	} else {
		trash = false;
		current_folder = current_folder.replace(/^(-)/, "");
		$('#menu-files').addClass("checked-menu");
	}
	current_folder = current_folder.replace(/^\//, "");

	console.log("current_folder: "+current_folder);

	if (current_folder) $('#parent').show();
	else $('#parent').hide();
	let root = "trash://";
	if (!trash) {
		$('#upload-files, #upload-folder').show();
		root = "files://";
	} else {
		$('#paste').hide();
	}

	$.ajax({
		type: "POST",
		url: "/cloud/get-folder",
		data: { 'folder': root + current_folder },
		success: function(data) {
			pc = new PolpettaCloud(root, current_folder, "grid", data, trash);
			set_buttons_triggers();
		}
	});

	$.getJSON( "/cloud/get-gp-sync-status", display_gp_sync);

	$('#sync-now').click(function(){
		$('#sync-last > span').text("synching...")
		let gp_sync = $('#gp-sync');
		gp_sync.css('cursor', 'progress');
		$.getJSON( "/cloud/gp-sync", function (data) {
			display_gp_sync(data);
			$('#gp-sync').css('cursor', 'default');
			if (data["pics_folder"]===current_folder) pc.update_folder();
		});
		gp_sync.css('cursor', 'default');
	});

	$('#main').on("dblclick", ".type-dir", function() {
		let t = "";
		if (trash) t = "-";
		if (!current_folder) {
			window.location.href = window.location.origin+"/cloud/-"+t+"/"+$(this).html();
		} else {
			window.location.href = window.location.origin+"/cloud/-"+t+"/"+current_folder+"/"+$(this).html();
		}
	});

});

function set_buttons_triggers() {
	$('#parent').click(function(){
		window.location.href = window.location.href.replace(/\/[^/]+$/, ''); // magic
	});

	$('#table-container, #grid-container').on("mousedown", function(e) {
		if (e.shiftKey) e.preventDefault();
	});

	$('#table-files').on("click", "tbody tr", function(event) {
		pc.click_entry(event, $(this), '#table-files tbody tr');
	});

	$('#grid-container').on("click", ".grid-element", function(event) {
		pc.click_entry(event, $(this), '#grid-container>.grid-element');
	});

	$('#delete').click(pc.action_delete);

	$('#restore').click(pc.action_restore);

	$('#perm-delete').click(pc.action_perm_delete);

	$('#download').click(pc.action_download);

	$('#rename').click(pc.action_rename);

	$('#create-folder').click(pc.action_create_folder);

	$('#copy').click(pc.action_copy);

	$('#cut').click(pc.action_cut);

	$('#paste').click(pc.action_paste);

	$('#upload-files').click(function() {
		$('#upload-files-hidden').trigger('click');
	});

	//$('#upload-files-hidden').change(pc.action_upload_file());

	$('#show-grid').click(function(){
		pc.set_visualization_mode("grid");
	});

	$('#show-table').click(function(){
		pc.set_visualization_mode("table");
	});
}

function display_gp_sync(sync_state) {
	let last_p = $('#sync-last > span');
	let res = "red";
	$('#sync-status > p').hide();
	if (sync_state["last_sync_result"]==null) {
		last_p.text("NEVER");
		if (sync_state["last_sync"] === "NO_CONSENT") $('#sync-no-consent').show();
	} else {
		last_p.text(sync_state["last_sync"]);
		if (sync_state["last_sync_result"]) {
			res = "green";
			if (sync_state["num_downloaded"]>=0) {
				$('#sync-ok > span').text(sync_state["num_downloaded"]);
				$('#sync-ok').show();
			}
		} else {
			$('#sync-unsucc').show();
		}
	}
	last_p.attr("class", res);
}