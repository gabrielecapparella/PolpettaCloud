from django.urls import path

from . import views

app_name = 'cloud'
#path('', views.index),
urlpatterns = [
	path('', views.index),
	path('-/<path:folder>/', views.index),
	path('get-folder', views.get_folder),
	path('delete', views.delete),
	path('rename', views.rename),
	path('create-folder', views.create_folder),
	path('copy', views.copy),
	path('cut', views.cut),
	path('paste', views.paste),
	path('upload-files', views.upload_files)
]