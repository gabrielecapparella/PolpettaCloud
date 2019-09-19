import google.oauth2.credentials
from google.auth.transport.requests import AuthorizedSession

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from cloud.models import GoogleSync

from os.path import basename, join
import requests
import json

@login_required
def test_endpoint(request):
	p = list_albums(request.user)
	print("list_albums ", p)
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