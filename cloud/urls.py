from django.urls import path

from . import views
from . import google_api

app_name = 'cloud'
#path('', views.index),
urlpatterns = [
	path('', views.index, name='cloud_index'),
	path('login-action/', views.login_action),
	path('login/', views.login_user),

	path('google-consent', views.google_consent),
	path('oauth2callback', views.oauth2_callback),
	path('-/<path:folder>/', views.index),
	path('get-folder', views.get_folder),
	path('delete', views.delete),
	path('rename', views.rename),
	path('create-folder', views.create_folder),
	path('copy', views.copy),
	path('cut', views.cut),
	path('paste', views.paste),
	path('upload-files', views.upload_files),
	path('get-info', views.get_info),

	path('test', google_api.test_endpoint),
	#path('upload-photo', google_api.upload_photo)
	#path('list-photos', google_api.list_photos),
	#path('list-albums', google_api.list_albums),
	#path('get-album-photos', google_api.get_album_photos)
	
]