let current_folder = window.location.pathname
	.replace(/^(\/cloud\/)/, "").replace(/^(-)/, "").replace(/\/$/, "");

$(document).ready(function() {
	if (current_folder) $('#parent').show();
	else $('#parent').hide();

	$('#delete, #rename, #copy, #cut, #download').hide();

	$.ajax({
		type: "POST",
		url: "/cloud/get-folder",
		data: { 'folder': current_folder },
		success: function(data) {
			pc = new PolpettaCloud(current_folder, "grid", data);
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
		if (!current_folder) {
			window.location.href = window.location.origin+"/cloud/-/"+$(this).html();
		} else {
			window.location.href = window.location.origin+"/cloud/-"+current_folder+"/"+$(this).html();
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

	$('#rename').click(pc.action_rename);

	$('#create-folder').click(pc.action_create_folder);

	$('#copy').click(pc.action_copy);

	$('#cut').click(pc.action_cut);

	$('#paste').click(pc.action_paste);

	$('#upload-files').click(function() {
		$('#upload-files-hidden').trigger('click');
	});

	$('#upload-files-hidden').change(pc.action_upload_file());

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