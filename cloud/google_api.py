
from os.path import basename, join, exists, isdir
from os.path import split as os_split
from os.path import getsize as os_getsize
from os import scandir as os_scandir
import json

import google.oauth2.credentials
from google.auth.transport.requests import AuthorizedSession

from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from cloud.models import GDrive_Index, Google_Tokens


@login_required
def test_endpoint(request):
	#print(gdrive_list(request.user))
	#gdrive_changes_start_page(request.user)
	#c = gdrive_changes_list(request.user)
	#print(c)
	gdrive_download_file(request.user, "1vW0YRxjRMXXiLF-hYLIom3xaRaZqV8Ld", "polpetta/yayyay.png")

	return HttpResponse(status=204)


def create_session(user):
	tokens = Google_Tokens.objects.get(user = user)
	credentials = google.oauth2.credentials.Credentials(
		token = tokens.g_token,
		refresh_token = tokens.g_refresh_token,
		client_id = settings.CLIENT_ID,
		client_secret = settings.CLIENT_SECRET,
		token_uri = settings.TOKEN_URI
	)
	return AuthorizedSession(credentials)


def gdrive_list(user):
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/files"
	res = session.get(url).json()
	return res


def gdrive_synch_file_or_folder(user, relative_path): #TODO: test
	full_path = join(user.root_path, relative_path)
	relative_path = relative_path.rstrip('/')

	parent_path = os_split(relative_path)[0]
	possible_parent = GDrive_Index.objects.filter(user=user, path=parent_path)
	if possible_parent.exists(): parent_id = possible_parent.gdrive_id
	else: parent_id = None

	if not GDrive_Index.objects.filter(user=user, path=relative_path).exists():
		new_entry = GDrive_Index(
			user = user,
			gdrive_id = None,
			parent_gdrive_id = parent_id,
			path = relative_path,
			is_dirty = True,
			is_dir = False
		)
		new_entry.save()

	if isdir(relative_path):
		for entry in os_scandir(full_path):
			entry_rel_path = join(relative_path, entry.name)
			gdrive_synch_file_or_folder(user, entry_rel_path)


def gdrive_check(user): #TODO: test
	remote_changes = gdrive_changes_list(user)
	dirty_entries = GDrive_Index.objects.filter(user=user, dirty=True)

	for entry in remote_changes: # TODO
		# move, delete, rename, create
		if entry["fileId"] in dirty_entries:
			pass # both local and remote is dirty, ask user
		else: 
			gdrive_download_file(user, entry.id, None)

	for entry in dirty_entries:
		full_path = join(user.root_path, entry.path)
		if not exists(full_path): # file was deleted
			if entry.gdrive_id:
				gdrive_delete(user, entry.gdrive_id)
			entry.delete()
		elif entry.gdrive_id=="": # not yet uploaded
			gdrive_create_file(user, full_path, entry.parent_gdrive_id)
		else: # file was modified
			pass #TODO: update file content
		entry.is_dirty = False
		entry.save()


def gdrive_delete(user, g_id): # works on folders too
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/files/{}".format(g_id)
	res = session.delete(url)
	return res


def gdrive_download_file(user, g_id, relative_path):
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/files/{}?alt=media".format(g_id)
	res = session.get(url)
	if res.status_code==200:
		dest = join(user.root_path, relative_path)
		with open(dest, 'wb') as f:
			f.write(res.content)
	return res


def gdrive_create_file(user, file_path, parent_gdrive_id):
	# should take care of parent_id and update DB
	session = create_session(user)
	url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"
	session.headers["Content-type"] = "application/json; charset=UTF-8"
	session.headers["Content-Length"] = os_getsize(file_path)
	body = json.dumps({
		'name': basename(file_path),
		'parents[]': [parent_gdrive_id]
		})
	res = session.post(url, body)
	print('res1 ',res.json())
	session_uri = res.headers['location'] # should save this somewhere to resume

	del session.headers["Content-type"]
	with open(file_path, 'rb') as f:
		body = f.read()
	res = session.put(session_uri, body)
	print('res2 ',res.json())


def gdrive_update_file(user, name, gdrive_id):
	# TODO: As of now it only changes the file name
	session = create_session(user)
	session.headers["Content-type"] = "application/json"
	url = "https://www.googleapis.com/drive/v3/files/{}".format(gdrive_id)
	body = json.dumps({
	 	'name': name
	})
	res = session.patch(url, body)
	return res

def gdrive_move_file(file_id, old_parent_id, new_parent_id):
	pass #TODO

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
		"restrictToMyDrive": True }
	res = session.get(url, params=params).json()
	user_tokens.gdrive_changes_token = res["newStartPageToken"]
	user_tokens.save()
	return res["changes"]


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
	session = create_session(user)
	url = 'https://photoslibrary.googleapis.com/v1/mediaItems'
	params = {
		"pageSize": 100,
		"pageToken": ""
	}
	result = []
	while True:
		page = session.get(url, params=params).json()
		result += page['mediaItems']
		if 'nextPageToken' in page:
			params["pageToken"] = page["nextPageToken"]
		else:
			break
	session.close()
	return result


def list_albums(user):
	session = create_session(user)
	url = 'https://photoslibrary.googleapis.com/v1/albums'
	params = {
		"pageSize": 50,
		"pageToken": ""
	}
	result = []
	while True:
		page = session.get(url, params=params).json()
		result += page['albums']
		if 'nextPageToken' in page:
			params["pageToken"] = page["nextPageToken"]
		else:
			break
	session.close()
	return result