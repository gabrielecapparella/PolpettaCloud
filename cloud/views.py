from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from cloud.models import GoogleTokens
import cloud.google_api as google_api
import google_auth_oauthlib.flow
import os
from datetime import datetime
from shutil import copy as sh_copy


@login_required
def index(request, folder=''):
	print(folder)
	return render(request, 'cloud/index.html', {'folder': folder})


def login_action(request):
	username = request.POST['usr']
	password = request.POST['pwd']
	user = authenticate(request, username=username, password=password)
	if user is not None:
		login(request, user)
		return redirect('/cloud')
	return HttpResponse(status=403)


def login_user(request):
	return render(request, 'cloud/login.html')


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

	user_tokens = GoogleTokens.objects.get_or_create(user=request.user)[0]
	user_tokens.g_token = flow.code_verifier
	user_tokens.save()

	return redirect(authorization_url)


def oauth2_callback(request):
	user_tokens = GoogleTokens.objects.get(user=request.user)
	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
		'client_secret.json',
		scopes=None)
	flow.code_verifier = user_tokens.g_token
	flow.redirect_uri = 'http://localhost/cloud/oauth2callback'
	flow.fetch_token(code=request.GET['code'])

	user_tokens.g_token = flow.credentials.token
	user_tokens.g_refresh_token = flow.credentials.refresh_token
	user_tokens.save()

	return redirect('/cloud')


@login_required
def get_info(request):  # TODO
	# as of now it only returns info about sync

	# root = request.user.root_path
	try:
		path = request.POST['path']
	except KeyError:
		return HttpResponse(status=400)
	info = {}
	# q = GDrive_Index.objects.filter(user=request.user, path=path).exists()
	# if q:
	# 	info = {"gdrive_sync": True}
	# else:
	# 	info = {"gdrive_sync": False}

	return JsonResponse(info, safe=False)


def get_folder(request):
	root = request.user.root_path
	try:
		folder = os.path.join(root, request.POST['folder'])
	except KeyError:
		return HttpResponse(status=400)

	try:
		files = scan_folder(folder)
	except OSError as e:
		print(e)
		print(os.getcwd())
		return HttpResponse(status=422)

	return JsonResponse(files, safe=False)


@login_required
def delete(request):  # what if it has to delete a folder, like pics_default?
	try:
		folder = os.path.join(request.user.root_path, request.POST['folder'])
		for path in request.POST.getlist('to_delete[]'):  # path is relative to user root
			old = os.path.join(request.user.root_path, path)
			new = os.path.join(request.user.trash_path, os.path.basename(path))
			while os.path.exists(new): new += '.copy'
			os.rename(old, new)

			# try:
			# 	entry = GDrive_Index.objects.get(user=request.user, path=path)
			# 	entry.is_dirty = True
			# 	entry.save()
			# except GDrive_Index.DoesNotExist:
			# 	pass

		# TODO: manage trash		

		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except KeyError:
		return HttpResponse(status=400)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)


@login_required
def rename(request):
	try:
		folder = os.path.join(request.user.root_path, request.POST['folder'])
		old = os.path.join(request.user.root_path, request.POST['old_path'])
		new = os.path.join(request.user.root_path, request.POST['new_path'])
		while os.path.exists(new): new += '.copy'
		os.rename(old, new)

		# try:
		# 	entry = GDrive_Index.objects.get(user=request.user,
		# 									 path=request.POST['old_path'])
		# 	entry.is_dirty = True
		# 	entry.path = request.POST['new_path']
		# 	entry.save()
		# except GDrive_Index.DoesNotExist:
		# 	pass

		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except OSError:
		return HttpResponse(status=422)

	except KeyError:
		return HttpResponse(status=400)


@login_required
def create_folder(request):
	try:
		folder = os.path.join(request.user.root_path, request.POST['folder'])
		full_path = os.path.join(folder, request.POST['name'])
		os.makedirs(full_path)

		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except OSError:
		return HttpResponse(status=422)

	except KeyError:
		return HttpResponse(status=400)


@login_required
def copy(request):
	try:
		paths = []
		for path in request.POST.getlist('to_copy[]'):
			paths.append(os.path.join(request.user.root_path, path))
	except KeyError:
		return HttpResponse(status=400)
	request.session['clipboard'] = paths
	request.session['clipboard_mode'] = 'copy'
	return HttpResponse(status=204)


@login_required
def cut(request):
	try:
		paths = []
		for path in request.POST.getlist('to_cut[]'):
			paths.append(os.path.join(request.user.root_path, path))
	except KeyError:
		return HttpResponse(status=400)
	request.session['clipboard'] = paths
	request.session['clipboard_mode'] = 'cut'
	return HttpResponse(status=204)


@login_required
def paste(request):
	try:
		destination = os.path.join(request.user.root_path, request.POST['folder'])
		mode = request.session['clipboard_mode']
		for path in request.session['clipboard']:
			new_path = os.path.join(destination, os.path.basename(path))
			while os.path.exists(new_path): new_path += '.copy'
			if mode == 'cut':
				os.rename(path, new_path)
				# try:
				# 	entry = GDrive_Index.objects.get(user=request.user, path=path)
				# 	entry.is_dirty = True
				# 	entry.path = new_path
				# 	entry.save()
				# except GDrive_Index.DoesNotExist:
				# 	pass
			elif mode == 'copy':
				sh_copy(path, new_path)
		if mode == 'cut': del request.session['clipboard']
		files = scan_folder(destination)
		return JsonResponse(files, safe=False)

	except KeyError:
		return HttpResponse(status=400)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)


@login_required
def upload_files(request):
	folder = os.path.join(request.user.root_path, request.POST['folder'])
	for uploaded_file in request.FILES.getlist('files[]'):
		full_path = os.path.join(folder, uploaded_file.name)
		with open(full_path, 'wb+') as f:
			for chunk in uploaded_file.chunks():
				f.write(chunk)

	files = scan_folder(folder)
	return JsonResponse(files, safe=False)


@login_required
def upload_folder(request):  # TODO
	return HttpResponse('ok')


@login_required
def get_file(request, file_path):
	# path: /username/path/to/file.txt
	if request.user.username == "test":
		response = HttpResponse()
		response['X-Accel-Redirect'] = '/files/' + file_path #request.path.replace("/cloud/get-file/", "")
		return response
	else:
		return HttpResponse(status=403)


def scan_folder(path):
	files = []
	for entry in os.scandir(path):
		file_size = get_size(entry)
		files.append({
			'type': 'dir' if entry.is_dir() else 'file',
			'name': entry.name,
			'size': readable_size(file_size),
			'raw_size': file_size,
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
		if size / 1000 >= 1:
			size /= 1000
		else:
			break
	return str(round(size, 1)) + i


def get_last_mod(entry):
	timestamp = os.stat(entry.path).st_mtime
	return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
