from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django import forms
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import os
from datetime import datetime
from shutil import copy as sh_copy
import json

@login_required
def index(request, folder = ''):
	print(folder)
	return render(request, 'cloud/index.html', {'folder':folder})

def login_action(request):
    username = request.POST['usr']
    password = request.POST['pwd']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('/cloud')
    else:
        return "nope"

def login_user(request):
	return render(request, 'cloud/login.html')	

def google_consent(request):
	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
		'/home/gabriele/Desktop/client_secret.json', 
		scopes=['https://www.googleapis.com/auth/photoslibrary'])
	flow.redirect_uri = 'http://localhost:8000/cloud/oauth2callback'
	authorization_url, state = flow.authorization_url(
		access_type='offline',
		include_granted_scopes='true')
	with open("code_verifier", 'w') as f:
		f.write(flow.code_verifier)
	return redirect(authorization_url)

def oauth2_callback(request):
	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
		'/home/gabriele/Desktop/client_secret.json', 
		scopes=None)
	with open("code_verifier", 'r') as f:
		flow.code_verifier = f.read()
	flow.redirect_uri = 'http://localhost:8000/cloud/oauth2callback'
	flow.fetch_token(code=request.GET['code'])
	# ACTION ITEM: In a production app, you likely want to save these
	#              credentials in a persistent database instead.

	with open("credentials.json", 'w') as f:
		json.dump(credentials_to_dict(flow.credentials), f)

	return HttpResponse(status=204)

def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

def get_folder(request):
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
	except KeyError:
		return HttpResponse(status=400)
	
	try:
		files = scan_folder(folder)
	except OSError as e:
		print(e)
		print(os.getcwd())
		return HttpResponse(status=422)

	return JsonResponse(files, safe=False)

def delete(request): #what if it has to delete a folder
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		for path in os.path.join(settings.ROOT_PATH, request.POST['to_delete[]']):
			old = os.path.join(settings.ROOT_PATH, path)
			new = os.path.join(settings.TRASH_PATH, os.path.basename(path))
			while(os.path.exists(new)): new += '.copy'
			os.rename(old, new)

		# manage trash
		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except KeyError:
		return HttpResponse(status=400)

	except OSError:
		return HttpResponse(status=422)

def rename(request):
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		old = os.path.join(settings.ROOT_PATH, request.POST['old_path'])
		new = os.path.join(settings.ROOT_PATH, request.POST['new_path'])
		while(os.path.exists(new)): new += '.copy'
		os.rename(old, new)

		files = scan_folder(folder)
		return JsonResponse(files, safe=False)
		
	except OSError:
		return HttpResponse(status=422)
		
	except KeyError:
		return HttpResponse(status=400)

def create_folder(request):
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		full_path = os.path.join(folder, request.POST['name'])
		os.makedirs(full_path)

		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except OSError:
		return HttpResponse(status=422)
		
	except KeyError:
		return HttpResponse(status=400)

def copy(request):
	try:
		paths = []
		for path in request.POST.getlist('to_copy[]'):
			print('path', path)
			paths.append(os.path.join(settings.ROOT_PATH, path))
	except KeyError:
		return HttpResponse(status=400)
	request.session['clipboard'] = paths
	request.session['clipboard_mode'] = 'copy'
	return HttpResponse(status=204)

def cut(request):
	try:
		paths = []
		for path in request.POST.getlist('to_cut[]'):
			paths.append(os.path.join(settings.ROOT_PATH, path))
	except KeyError:
		return HttpResponse(status=400)
	request.session['clipboard'] = paths
	request.session['clipboard_mode'] = 'cut'
	return HttpResponse(status=204)

def paste(request):
	try:
		destination = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		mode = request.session['clipboard_mode']
		for path in request.session['clipboard']:
			new_path = os.path.join(destination, os.path.basename(path))
			while(os.path.exists(new_path)): new_path += '.copy'
			if mode == 'cut': os.rename(path, new_path)
			elif mode == 'copy': sh_copy(path, new_path)
		if mode == 'cut': del request.session['clipboard']
		files = scan_folder(destination)
		return JsonResponse(files, safe=False)

	except KeyError:
		return HttpResponse(status=400)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)

def upload_files(request):
	# print(request.POST.keys())
	# print(request.FILES.keys())
	folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
	for uploaded_file in request.FILES.getlist('files[]'):
		full_path = os.path.join(folder, uploaded_file.name)
		with open(full_path, 'wb+') as f:
			for chunk in uploaded_file.chunks():
				f.write(chunk)
	files = scan_folder(folder)
	return JsonResponse(files, safe=False)


def upload_folder(request):
	return HttpResponse('ok')

def scan_folder(path):
	files = []
	for entry in os.scandir(path):
		files.append({
			'type': 'dir' if entry.is_dir() else 'file',
			'name': entry.name,
			'size': readable_size(get_size(entry)),
			'last_mod': get_last_mod(entry)
		})
	return files

def get_size(entry): 
	if entry.is_file():
		return os.stat(entry.path).st_size
	else:
		size = 0
		for i in os.scandir(entry.path):
			size += get_size(i)
	return size

def readable_size(size):
	for i in ("B", "KB", "MB", "GB", "TB"):
		if size/1000>=1:	
			size/=1000
		else:
			break
	return str(round(size, 1))+i

def get_last_mod(entry):
	timestamp = os.stat(entry.path).st_mtime
	return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')