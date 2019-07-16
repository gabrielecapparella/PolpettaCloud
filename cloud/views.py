from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from django.conf import settings
import os
from datetime import datetime

def index(request):
	return render(request, 'cloud/index.html')

def get_folder(request):
	folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
	files = scan_folder(folder)
	return JsonResponse(files, safe=False)

def delete(request): #what if it has to delete a folder
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		old = os.path.join(settings.ROOT_PATH, request.POST['path'])
		new = os.path.join(settings.TRASH_PATH, os.path.basename(request.POST['path']))
	except KeyError:
		return HttpResponse(status=400)

	while(os.path.exists(new)): new += '.copy'
		
	try:
		os.rename(old, new)
	except OSError:
		return HttpResponse(status=400)

	# manage trash

	files = scan_folder(folder)
	return JsonResponse(files, safe=False)

def rename(request):
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		old = os.path.join(settings.ROOT_PATH, request.POST['old_path'])
		new = os.path.join(settings.ROOT_PATH, request.POST['new_path'])
		os.rename(old, new)
	except (KeyError, OSError):
		return HttpResponse(status=400)
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


def move(request): #TODO
	try:
		folder = os.path.join(settings.ROOT_PATH, request.POST['folder'])
		old_path = request.POST['old_path']
		new_path = request.POST['new_path']

	except KeyError:
		raise Http404("Path not found")

	return HttpResponse('ok') #should return updated files	

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
		files.append([
			entry.name,
			readable_size(get_size(entry)),
			get_last_mod(entry)
		])
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