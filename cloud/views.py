from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
from datetime import datetime
from shutil import copy2 as sh_copy, copytree, make_archive
import zipfile
from tempfile import TemporaryDirectory


CLOUD_ROOT = settings.CLOUD_ROOT


@login_required
def index(request, folder=''):
	return render(request, 'cloud/index.html')


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


def logout_action(request):
	logout(request)
	return redirect('/cloud/login/')


@login_required
def get_folder(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
	except KeyError as e:
		print(e)
		return HttpResponse(status=400)

	try:
		files = scan_folder(folder)
	except OSError as e:
		print(e)
		return HttpResponse(status=422)

	return JsonResponse(files, safe=False)


@login_required
def perm_delete(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
		for filename in request.POST.getlist('to_delete[]'):
			os.remove(os.path.join(folder, filename))
		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except KeyError as e:
		print(e)
		return HttpResponse(status=400)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)


@login_required
def delete(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
		for filename in request.POST.getlist('to_delete[]'):
			old = os.path.join(folder, filename)
			new = os.path.join(get_user_trash(request.user), filename)
			while os.path.exists(new): new += '.copy'
			os.rename(old, new)

		# TODO: manage trash		

		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except KeyError as e:
		print(e)
		return HttpResponse(status=400)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)


@login_required
def restore(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
		for filename in request.POST.getlist('to_restore[]'):
			old = os.path.join(folder, filename)
			new = os.path.join(get_user_root(request.user), filename)
			while os.path.exists(new): new += '.copy'
			os.rename(old, new)

		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except KeyError as e:
		print(e)
		return HttpResponse(status=400)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)


@login_required
def rename(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
		old = os.path.join(folder, request.POST['old_path'])
		new = os.path.join(folder, request.POST['new_path'])
		while os.path.exists(new): new += '.copy'
		os.rename(old, new)

		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)

	except KeyError as e:
		print(e)
		return HttpResponse(status=400)


@login_required
def create_folder(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
		full_path = os.path.join(folder, request.POST['name'])
		os.makedirs(full_path)

		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)

	except KeyError as e:
		print(e)
		return HttpResponse(status=400)


@login_required
def copy(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
		paths = []
		for filename in request.POST.getlist('to_copy[]'):
			paths.append(os.path.join(folder, filename))
	except KeyError as e:
		print(e)
		return HttpResponse(status=400)
	request.session['clipboard'] = paths
	request.session['clipboard_mode'] = 'copy'
	return HttpResponse(status=204)


@login_required
def cut(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
		paths = []
		for filename in request.POST.getlist('to_cut[]'):
			paths.append(os.path.join(folder, filename))
	except KeyError as e:
		print(e)
		return HttpResponse(status=400)
	request.session['clipboard'] = paths
	request.session['clipboard_mode'] = 'cut'
	return HttpResponse(status=204)


@login_required
def paste(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
		mode = request.session['clipboard_mode']
		for path in request.session['clipboard']:
			new_path = os.path.join(folder, os.path.basename(path))
			while os.path.exists(new_path): new_path += '.copy'
			if mode == 'cut':
				os.rename(path, new_path)
			elif mode == 'copy':
				sh_copy(path, new_path)
		if mode == 'cut': del request.session['clipboard']
		files = scan_folder(folder)
		return JsonResponse(files, safe=False)

	except KeyError as e:
		print(e)
		return HttpResponse(status=400)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)


@login_required
def upload_files(request):
	folder = get_full_path(request.user, request.POST['folder'])
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
	response = HttpResponse()
	response['X-Accel-Redirect'] = '/files/'+str(request.user.id)+"/files/"+file_path
	return response


@login_required
def download(request):
	try:
		folder = get_full_path(request.user, request.POST['folder'])
		to_download = request.POST.getlist('to_download[]')
		num_files = len(to_download)

		if num_files == 0: return HttpResponse(status=422)
		if num_files == 1:
			file_path = os.path.join(folder, to_download[0])
			if os.path.isfile(file_path):
				response = FileResponse(open(file_path, 'rb'))
				response["FILENAME"] = to_download[0]
			else:
				with TemporaryDirectory() as temp_dir:
					zip_path = make_archive(os.path.join(temp_dir, to_download[0]), "zip", file_path)
					response = FileResponse(open(zip_path, 'rb'))
					response["FILENAME"] = to_download[0]+".zip"
		else:
			with TemporaryDirectory() as temp_dir:
				tmp_files = os.path.join(temp_dir, "files")
				os.mkdir(tmp_files)
				for f in to_download:
					f_path = os.path.join(folder, f)
					if os.path.isfile(f_path): sh_copy(f_path, tmp_files)
					else: copytree(f_path, os.path.join(tmp_files, f))
				zip_path = make_archive(os.path.join(temp_dir, "archive"), "zip", tmp_files)
				response = FileResponse(open(zip_path, 'rb'))
				response["FILENAME"] = "download.zip"

		return response

	except KeyError as e:
		print(e)
		return HttpResponse(status=400)

	except OSError as e:
		print(e)
		return HttpResponse(status=422)


@login_required
def get_trash(request, file_path):
	response = HttpResponse()
	response['X-Accel-Redirect'] = '/files/'+str(request.user.id)+"/trash/"+file_path
	return response


@login_required
def get_avatar(request):
	response = HttpResponse()
	response['X-Accel-Redirect'] = '/files/'+str(request.user.id)+"/avatar.png"
	return response


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


def get_user_root(user):
	return os.path.join(CLOUD_ROOT, str(user.id)+"/files")


def get_user_trash(user):
	return os.path.join(CLOUD_ROOT, str(user.id)+"/trash")


def get_full_path(user, path):
	if path.startswith("files://"):
		return path.replace("files://", CLOUD_ROOT + str(user.id) + "/files/")
	elif path.startswith("trash://"):
		return path.replace("trash://", CLOUD_ROOT + str(user.id) + "/trash/")
