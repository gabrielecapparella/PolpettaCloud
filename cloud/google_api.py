import google.oauth2.credentials
from google.auth.transport.requests import AuthorizedSession

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from cloud.models import GDrive_Index

from os.path import basename, join, exists
from os import scandir as os_scandir
import requests
import json


@login_required
def test_endpoint(request):
	# res = gdrive_create_file(request.user, '/home/gabriele/Desktop/cpqonbah7fp31.jpg')
	# print('gdrive_create_file ', res.content)
	# g_id = res.json()['id']
	g_id = "1PiX0pttGPwlfVbp-_v36nlbFYVJIojtH"
	res2 = gdrive_update_file(request.user, 'gluglu.jpg', g_id)
	print('gdrive_upload_file ', res2.content)
	return HttpResponse(status=204)

def create_session(user):
	credentials = google.oauth2.credentials.Credentials(
		token = user.g_token, 
		refresh_token = user.g_refresh_token,
		client_id = settings.CLIENT_ID,
		client_secret = settings.CLIENT_SECRET,
		token_uri = settings.TOKEN_URI
	)
	return AuthorizedSession(credentials)

def gdrive_check(user):
	remote_changes = gdrive_changes_list(user)
	dirty_entries = GDrive_Index.objects.filter(user=user, dirty=True)

	for entry in remote_changes: # TODO
		if entry.id in dirty_entries: 
			pass # both local and remote is dirty, ask user
		else: # download
			gdrive_download_file(user, entry.id)
	
	for entry in dirty_entries:
		full_path = join(user.root_path, entry.path)
		if not exists(full_path): # file was deleted
			if entry.gdrive_id:
				gdrive_delete(user, entry.gdrive_id)
			entry.delete()
		elif entry.gdrive_id=="": # not yet uploaded
			gdrive_create_file(user, full_path)
		else: # file was modified
			pass #TODO: update file content
		entry.is_dirty = False
		entry.save()

def gdrive_delete(user, g_id): 
	pass # TODO

def gdrive_download_file(user, g_id):
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/files/{}".format(g_id)
	res = session.get(url).json()
	if res["mimeType"] == "application/vnd.google-apps.folder":
		pass # TODO: it's a folder
	else:
		file_path = GDrive_Index.objects.get(user=user, gdrive_id=g_id).values("path")
		req = requests.get(res["webContentLink"])
		if req.status_code==200:
				dest = join(user.root_path, file_path)
				with open(dest, 'wb') as f:
					f.write(req.content)

def gdrive_synch_file_or_folder(user, relative_path):
	full_path = join(user.root_path, relative_path)
	for entry in os_scandir(full_path):
		entry_rel_path = join(relative_path, entry.name)
		if entry.is_dir():
			gdrive_synch_file_or_folder(user, entry_rel_path)
		else:
			if not GDrive_Index.objects.filter(user=user, path=entry_rel_path).exists():
				new_entry = GDrive_Index(
					user = user,
					gdrive_id = None,
					parent_gdrive_id = None,
					path = entry_rel_path,
					is_dirty = True,
					is_dir = False
				)
				new_entry.save()

def gdrive_create_file(user, file_path):
	# should take care of parent_id and update DB
	session = create_session(user)
	url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=media"
	session.headers["Content-type"] = "image/jpeg"
	#session.headers["Content-Length"] = "50447"
	with open(file_path, 'rb') as f:
		body = f.read()

	res = session.post(url, body)
	gdrive_update_file(user, basename(file_path), res.json()["id"])

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
	pass

def gdrive_changes_start_page(user):
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/changes/startPageToken"
	res = session.get(url).json()
	print("res ", res)
	return res["startPageToken"]

def gdrive_changes_list(user):
	global p # REMOVE BEFORE FLIGHT
	session = create_session(user)
	url = "https://www.googleapis.com/drive/v3/changes"
	res = session.get(url, params={ "pageToken": p }).json()
	p = res["newStartPageToken"]
	return res


def check_gphotos_soft(user):
	local_photos = GoogleSync.objects.filter(
		user=user, gphotos=True, is_dir=False
		).only("path")

	local_photos = [basename(photo.path) for photo in local_photos]
	remote_photos = list_photos(user)
	folder = join(user.root_path, user.pics_default)
	for photo in remote_photos:
		if not photo["filename"] in local_photos: # perhaps I should use google id
			print('downloading ', photo["filename"])
			req = requests.get(photo["baseUrl"])
			if req.status_code==200:
				dest = join(folder, photo["filename"])
				with open(dest, 'wb') as f:
					f.write(req.content)


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


'''
# filepath is relative to user's root folder
def upload_photo(user: CloudUser, filepath: str):
	url_upload = 'https://photoslibrary.googleapis.com/v1/uploads'
	url_create = 'https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate'
	full_path = join(user.root_path, filepath)
	album_id = get_album_from_path(user, full_path)
	session = create_session(user)

	session.headers["Content-type"] = "application/octet-stream"
	session.headers["X-Goog-Upload-Protocol"] = "raw"
	session.headers["X-Goog-Upload-File-Name"] = basename(full_path)
	with open(full_path, 'rb') as f:
		fcontent = f.read()
	upload_token = session.post(url_upload, fcontent)
	print('upload_token ', upload_token.content)

	del(session.headers["X-Goog-Upload-Protocol"])
	del(session.headers["X-Goog-Upload-File-Name"])
	session.headers["Content-type"] = "application/json"
	body = {
		"albumId":album_id, 
		"newMediaItems": [{
			"description": "",
			"simpleMediaItem": {
				"uploadToken":upload_token.content.decode()
			}
		}]
	}
	body = json.dumps(body)
	create_photo = session.post(url_create, body)
	print('create_photo ', create_photo)
	session.close()
'''