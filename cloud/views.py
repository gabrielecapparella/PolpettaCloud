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