# from os.path import basename, join, exists, isdir
# from os.path import split as os_split
# from os.path import getsize as os_getsize
# from os import scandir as os_scandir
# import json

from os.path import join

import google.oauth2.credentials
from google.auth.transport.requests import AuthorizedSession

from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from cloud.models import GoogleTokens


@login_required
def test_endpoint(request):
	photos = list_photos(request.user)
	print(photos)
	download_photos(request.user, photos)
	return HttpResponse(status=204)


def create_session(tokens):  # should I delete these after use?
	credentials = google.oauth2.credentials.Credentials(
		token=tokens.g_token,
		refresh_token=tokens.g_refresh_token,
		client_id=settings.CLIENT_ID,
		client_secret=settings.CLIENT_SECRET,
		token_uri=settings.TOKEN_URI
	)
	return AuthorizedSession(credentials)

"""
# only creates entries in the DB
def gdrive_synch_file_or_folder(user, relative_path):
	full_path = join(user.root_path, relative_path)
	relative_path = relative_path.rstrip('/')
	parent_id = gdrive_get_parent_id(user, relative_path)

	if not GDrive_Index.objects.filter(user=user, path=relative_path).exists():
		new_entry = GDrive_Index(
			user=user,
			gdrive_id="",
			parent_gdrive_id=parent_id,
			path=relative_path,
			is_dirty=True,
			is_dir=isdir(full_path)
		)
		new_entry.save()

	if isdir(full_path):
		for entry in os_scandir(full_path):
			entry_rel_path = join(relative_path, entry.name)
			gdrive_synch_file_or_folder(user, entry_rel_path)


# checks if a file that is about to be created has to be synched as well
# a new file has to be synched if is inside a synched folder
def gdrive_check_if_has_to_be_synched(user, relative_path):
	possible_parent_id = gdrive_get_parent_id(user, relative_path)
	if not possible_parent_id == None:
		gdrive_synch_file_or_folder(user, relative_path)


def gdrive_check_dirty(user):
	dirty_entries = list(GDrive_Index.objects.filter(user=user, is_dirty=True))

	# TODO
	# remote_changes = gdrive_changes_list(user)
	# for entry in remote_changes:
	# 	# move, delete, rename, create
	# 	if entry["fileId"] in dirty_entries:
	# 		pass # both local and remote is dirty, ask user
	# 	else: 
	# 		gdrive_download_file(user, entry.id, None)

	for entry in dirty_entries:
		full_path = join(user.root_path, entry.path)
		if not exists(full_path):  # file was deleted
			if entry.gdrive_id:
				gdrive_delete(user, entry.gdrive_id)
			entry.delete()
		elif entry.gdrive_id == "":  # not yet uploaded
			if entry.parent_gdrive_id == "":
				parent_id = gdrive_get_parent_id(user, entry.path)
				if parent_id == "":
					dirty_entries.append(entry)
					continue
			else:
				parent_id = entry.parent_gdrive_id
			gdrive_upload_file(user, entry)
		else:  # file or folder was modified
			gdrive_upload_file(user, entry)
		entry.is_dirty = False
		entry.save()


def gdrive_delete(user, index_entry):  # works on folders too
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/files/{}".format(index_entry.gdrive_id)
	res = session.delete(url)
	index_entry.delete()
	return res


def gdrive_download_file(user, index_entry):  # TODO: what about folders?
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/files/{}?alt=media".format(index_entry.gdrive_id)
	res = session.get(url)
	if res.status_code == 200:
		dest = join(user.root_path, index_entry.path)
		with open(dest, 'wb') as f:
			f.write(res.content)
	return res


def gdrive_upload_file(user, index_entry):  # TODO: what about folders?
	full_path = join(user.root_path, index_entry.path)
	session = create_session(user)
	session.headers["Content-type"] = "application/json; charset=UTF-8"
	session.headers["Content-Length"] = str(os_getsize(full_path))

	parents = [index_entry.parent_gdrive_id] if index_entry.parent_gdrive_id else []
	body = json.dumps({
		'name': basename(index_entry.path),
		'parents[]': parents
	})

	if index_entry.gdrive_id == "":  # first upload
		url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"
		res = session.post(url, body)
	else:  # update
		url = "https://www.googleapis.com/upload/drive/v3/files/{}?uploadType=resumable" \
			.format(index_entry.gdrive_id)
		res = session.patch(url, body)

	session_uri = res.headers['location']  # should save this somewhere to resume
	del session.headers["Content-type"]
	with open(full_path, 'rb') as f:
		body = f.read()
	res = session.put(session_uri, body).json()
	index_entry.gdrive_id = res["id"]
	index_entry.save()
	return res


def gdrive_move_file(user, index_entry, new_parent_id):
	session = create_session(user)
	session.headers["Content-type"] = "application/json; charset=UTF-8"
	url = "https://www.googleapis.com/drive/v3/files/{}?addParents={}&removeParents={}" \
		.format(index_entry.gdrive_id, new_parent_id, index_entry.parent_gdrive_id)
	index_entry.parent_gdrive_id = new_parent_id
	index_entry.save()
	res = session.patch(url, json.dumps({}))
	return res


def gdrive_changes_start_page(user):
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/changes/startPageToken"
	res = session.get(url).json()
	user_tokens = Google_Tokens.objects.get(user=user)
	user_tokens.gdrive_changes_token = res["startPageToken"]
	user_tokens.save()
	return res


def gdrive_changes_list(user):
	user_tokens = Google_Tokens.objects.get(user=user)
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/changes"
	params = {
		"pageToken": user_tokens.gdrive_changes_token,
		"restrictToMyDrive": True}
	res = session.get(url, params=params).json()
	user_tokens.gdrive_changes_token = res["newStartPageToken"]
	user_tokens.save()
	return res["changes"]


def gdrive_list(user):
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/files"
	res = session.get(url).json()
	return res


def gdrive_get_parent_id(user, relative_path):
	parent_path = os_split(relative_path)[0]
	try:
		possible_parent = GDrive_Index.objects.get(user=user, path=parent_path)
		parent_id = possible_parent.gdrive_id
	except GDrive_Index.DoesNotExist:
		parent_id = None
	return parent_id
"""

# def gdrive_get_info(user, file_id):
# 	session = create_session(user)
# 	url = "https://www.googleapis.com/drive/v3/files/{}?fields=parents".format(file_id)
# 	res = session.get(url).json()
# 	return res


# def check_gphotos_soft(user):
# 	local_photos = GoogleSync.objects.filter(
# 		user=user, gphotos=True, is_dir=False
# 		).only("path")

# 	local_photos = [basename(photo.path) for photo in local_photos]
# 	remote_photos = list_photos(user)
# 	folder = join(user.root_path, user.pics_default)
# 	for photo in remote_photos:
# 		if not photo["filename"] in local_photos: # perhaps I should use google id
# 			print('downloading ', photo["filename"])
# 			req = requests.get(photo["baseUrl"])
# 			if req.status_code==200:
# 				dest = join(folder, photo["filename"])
# 				with open(dest, 'wb') as f:
# 					f.write(req.content)


def list_photos(user):
	tokens = GoogleTokens.objects.get(user=user)
	tokens.last_pic = "gluglu" # REMOVE BEFORE FLIGHT
	session = create_session(tokens)
	url = 'https://photoslibrary.googleapis.com/v1/mediaItems'
	params = {
		"pageSize": 10,
		"pageToken": ""
	}

	first_id = None
	last_id = tokens.last_pic
	to_download = []
	quack = True

	while quack:
		page = session.get(url, params=params).json()
		for photo in page['mediaItems']:
			if not first_id: first_id = photo["id"]
			if photo["id"] == last_id:
				quack = False
				break
			to_download.append((photo["baseUrl"], photo["filename"]))
		if 'nextPageToken' in page: params["pageToken"] = page["nextPageToken"]
		else: break

	if first_id:
		tokens.last_pic = first_id
		tokens.save()

	session.close()
	return to_download


def download_photos(user, to_download: list):
	tokens = GoogleTokens.objects.get(user=user)
	session = create_session(tokens)
	for photo_url, photo_name in to_download:
		res = session.get(photo_url+"=d")
		if res.status_code == 200:
			dest = join(user.pics_default, photo_name)
			with open(dest, 'wb') as f:
				f.write(res.content)

# def list_albums(user):
# 	session = create_session(user)
# 	url = 'https://photoslibrary.googleapis.com/v1/albums'
# 	params = {
# 		"pageSize": 50,
# 		"pageToken": ""
# 	}
# 	result = []
# 	while True:
# 		page = session.get(url, params=params).json()
# 		result += page['albums']
# 		if 'nextPageToken' in page:
# 			params["pageToken"] = page["nextPageToken"]
# 		else:
# 			break
# 	session.close()
# 	return result
