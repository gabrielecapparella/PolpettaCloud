from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
import os
from datetime import datetime
from shutil import copy as sh_copy

def index(request, folder = ''):
	print(folder)
	return render(request, 'cloud/index.html', {'folder':folder})

def get_folder(request):
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
	except KeyError:
		return HttpResponse(status=400)
	
	try:
		files = scan_folder(folder)
	except OSError:
		return HttpResponse(status=422)

	return JsonResponse(files, safe=False)

def delete(request): #what if it has to delete a folder
	try:
		print(request.POST.keys())
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		old = os.path.join(settings.ROOT_PATH, request.POST['path'])
		new = os.path.join(settings.TRASH_PATH, os.path.basename(request.POST['path']))
	except KeyError:
		return HttpResponse(status=400)

	while(os.path.exists(new)): new += '.copy'
		
	try:
		os.rename(old, new)
	except OSError:
		return HttpResponse(status=422)

	# manage trash

	files = scan_folder(folder)
	return JsonResponse(files, safe=False)

def rename(request):
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		old = os.path.join(settings.ROOT_PATH, request.POST['old_path'])
		new = os.path.join(settings.ROOT_PATH, request.POST['new_path'])
	except KeyError:
		return HttpResponse(status=400)
	
	try: os.rename(old, new)
	except OSError: return HttpResponse(status=422)

	files = scan_folder(folder)
	return JsonResponse(files, safe=False)

def create_folder(request):
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		full_path = os.path.join(folder, request.POST['name'])
		os.makedirs(full_path)
	except (KeyError, FileExistsError):
		return HttpResponse(status=400)
	files = scan_folder(folder)
	return JsonResponse(files, safe=False)

def copy(request):
	try:
		path = os.path.join(settings.ROOT_PATH, request.POST['path'])
	except KeyError:
		return HttpResponse(status=400)
	request.session['clipboard'] = path
	request.session['clipboard_mode'] = 'copy'
	return HttpResponse(status=204)

def cut(request):
	try:
		path = os.path.join(settings.ROOT_PATH, request.POST['path'])
	except KeyError:
		return HttpResponse(status=400)
	request.session['clipboard'] = path
	request.session['clipboard_mode'] = 'cut'
	return HttpResponse(status=204)

def paste(request):
	try:
		destination = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		old_path = request.session['clipboard']
	except KeyError:
		return HttpResponse(status=400)
	new_path = os.path.join(destination, os.path.basename(old_path))

	try:
		if request.session['clipboard_mode'] == 'cut':
			os.rename(old_path, new_path)
			del request.session['clipboard']
			del request.session['clipboard_mode']
		elif request.session['clipboard_mode'] == 'copy':
			sh_copy(old_path, new_path)
	except OSError:
		return HttpResponse(status=422)

	files = scan_folder(destination)
	return JsonResponse(files, safe=False)

def upload_file(request):
	uploaded_file  = request.FILES['file']
	folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
	full_path = os.path.join(folder, uploaded_file.name)
	with open(full_path, 'wb+') as f:
		for chunk in uploaded_file.chunks():
			f.write(chunk)

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