from os.path import join
from datetime import datetime

import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.auth.transport.requests import AuthorizedSession

from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from cloud.models import GooglePhotosSync
from cloud.views import get_user_root


@login_required
def test_endpoint(request):
	GooglePhotosSync.objects.all().delete()
	#fetch_new_photos(request.user)
	return HttpResponse(status=204)


def create_session(g_token, g_refresh_token):
	credentials = google.oauth2.credentials.Credentials(
		token=g_token,
		refresh_token=g_refresh_token,
		client_id=settings.CLIENT_ID,
		client_secret=settings.CLIENT_SECRET,
		token_uri=settings.TOKEN_URI
	)
	return AuthorizedSession(credentials)


@login_required
def get_google_sync_status(request, num_downloaded=-1):
	try:
		gp_data = GooglePhotosSync.objects.get(user=request.user)
		if gp_data.last_sync:
			last = readable_delta(timezone.now() - gp_data.last_sync)+"ago"
		else:
			last = "NEVER"
		res = {
			"last_sync": last,
			"last_sync_result": gp_data.last_sync_result,
			"num_downloaded": num_downloaded
		}
	except GooglePhotosSync.DoesNotExist:
		res = {"last_sync": "NO_CONSENT"}
	return JsonResponse(res)


@login_required
def google_sync_now(request):
	res = fetch_new_photos(request.user)
	if res<0: redirect('/cloud/google-consent')
	return get_google_sync_status(request, res)


def fetch_new_photos(user):
	gp_data = GooglePhotosSync.objects.get(user=user)
	session = create_session(gp_data.g_token, gp_data.g_refresh_token)
	new_photos = list_new_photos(session, gp_data)
	if new_photos == False:
		gp_data.last_sync_result = False
		gp_data.last_sync = timezone.now()
		gp_data.save()
		return -1
	download_photos(session, gp_data.pics_folder, new_photos)
	session.close()
	gp_data.last_sync_result = True
	gp_data.save()
	return len(new_photos)

def list_new_photos(session, gp_data):
	#gp_data.last_pic = "gluglu" # REMOVE BEFORE FLIGHT
	url = 'https://photoslibrary.googleapis.com/v1/mediaItems'
	params = {
		"pageSize": 10,
		"pageToken": ""
	}

	first_id = None
	last_id = gp_data.last_pic
	to_download = []
	quack = True

	while quack:
		page = session.get(url, params=params)
		if page.status_code != 200: return False
		for photo in page.json()['mediaItems']:
			if not first_id: first_id = photo["id"]
			if photo["id"] == last_id:
				quack = False
				break
			to_download.append((photo["baseUrl"], photo["filename"]))
		if 'nextPageToken' in page: params["pageToken"] = page["nextPageToken"]
		else: break

	if first_id:
		gp_data.last_pic = first_id
		gp_data.last_sync = datetime.now()
		gp_data.save()

	return to_download


def download_photos(session, folder, to_download: list):
	for photo_url, photo_name in to_download:
		res = session.get(photo_url+"=d")
		if res.status_code == 200:
			dest = join(folder, photo_name)
			with open(dest, 'wb') as f:
				f.write(res.content)


@login_required
def google_consent(request):
	scopes = [
		'https://www.googleapis.com/auth/photoslibrary.readonly'
	]
	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
		'client_secret.json',
		scopes=scopes)
	flow.redirect_uri = 'http://localhost/cloud/oauth2callback'
	authorization_url, state = flow.authorization_url(
		access_type='offline',
		include_granted_scopes='true')

	user_tokens = GooglePhotosSync.objects.get_or_create(user=request.user)[0]
	user_tokens.g_token = flow.code_verifier
	user_tokens.save()

	return redirect(authorization_url)


def oauth2_callback(request):
	user_tokens = GooglePhotosSync.objects.get(user=request.user)
	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
		'client_secret.json',
		scopes=None)
	flow.code_verifier = user_tokens.g_token
	flow.redirect_uri = 'http://localhost/cloud/oauth2callback'
	flow.fetch_token(code=request.GET['code'])

	user_tokens.g_token = flow.credentials.token
	user_tokens.g_refresh_token = flow.credentials.refresh_token
	user_tokens.pics_folder = get_user_root(request.user)+"/Pictures"
	user_tokens.last_sync_result = True
	user_tokens.save()

	return redirect('/cloud')


def readable_delta(delta):
	ts = [delta.days] + [0] * 3
	ts[1], ts[2] = divmod(delta.seconds, 3600)
	ts[2] //= 60
	ts_readable = ""
	for i, s in enumerate(["d", "h", "m"]):
		if ts[i] == 0 and i < 2: continue
		ts_readable += str(ts[i]) + s + " "
	return ts_readable
