import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import json
from django.http import JsonResponse, HttpResponse
from cloud.models import GoogleSync
from os.path import basename, join
import requests

def check_gphotos_soft(request):
	local_photos = GoogleSync.objects.filter(
		user=request.user, gphotos=True, is_dir=False
		).only("path")

	local_photos = [basename(photo.path) for photo in local_photos]
	remote_photos = list_photos()
	folder = join(request.user.root_path, request.user.pics_default)
	for photo in remote_photos:
		if not photo["filename"] in local_photos: # perhaps I should use google id
			print('downloading ', photo["filename"])
			req = requests.get(photo["baseUrl"])
			if req.status_code==200:
				dest = join(folder, photo["filename"])
				with open(dest, 'wb') as f:
					f.write(req.content)

	return HttpResponse(status=204)
	



def list_photos():
	with open("credentials.json", 'r') as f:
		credentials = google.oauth2.credentials.Credentials(**json.load(f))
	s = build('photoslibrary', 'v1', credentials=credentials)

	page_token = ""
	result = []
	while True:
		page = s.mediaItems().list(pageSize=2, pageToken=page_token).execute()
		result += page['mediaItems']
		page_token = page.get('nextPageToken', False)
		if not page_token: break
	
	with open("list_photos_out.json", 'w') as f:
		json.dump(result, f, indent=4)
	
	return result

def list_albums(request):
	with open("credentials.json", 'r') as f:
		credentials = google.oauth2.credentials.Credentials(**json.load(f))
	s = build('photoslibrary', 'v1', credentials=credentials)

	page_token = ""
	result = []
	while True:
		page = s.albums().list(pageSize=2, pageToken=page_token).execute()
		result += page['albums']
		page_token = page.get('nextPageToken', False)
		if not page_token: break
	
	with open("list_albums_out.json", 'w') as f:
		json.dump(result, f, indent=4)
	
	return HttpResponse(status=204)

def get_album_photos(request):
	with open("credentials.json", 'r') as f:
		credentials = google.oauth2.credentials.Credentials(**json.load(f))
	s = build('photoslibrary', 'v1', credentials=credentials)

	page_token = ""
	result = []
	while True:
		searchbody = {
			"albumId":"APebepgoBahDToUHaCGLHh7RZuSQe4uzwd-nB2Xqi-L4OjSpDSz7fKIbBKqWSoi3X_-kWXw-jNjM",
			"pageSize":2,
			"pageToken":page_token
		}
		page = s.mediaItems().search(body=searchbody).execute()
		result += page['mediaItems']
		page_token = page.get('nextPageToken', False)
		if not page_token: break
	
	with open("get_album_photos_out.json", 'w') as f:
		json.dump(result, f, indent=4)
	
	return HttpResponse(status=204)