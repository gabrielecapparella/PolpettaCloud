from django.urls import path
from django.views.generic import RedirectView

import cloud.google_api
from . import views
from . import google_api

app_name = 'cloud'
urlpatterns = [
	path('', views.index),
	path('-/<path:folder>', views.index),
	path('-/', RedirectView.as_view(url='/cloud')),

	path('login-action/', views.login_action),
	path('login/', views.login_user),
	path('logout/', views.logout_action),
	path('get-avatar', views.get_avatar),

	path('get-folder', views.get_folder),
	path('delete', views.delete),
	path('rename', views.rename),
	path('create-folder', views.create_folder),
	path('copy', views.copy),
	path('cut', views.cut),
	path('paste', views.paste),
	path('upload-files', views.upload_files),

	path('get-file/<path:file_path>', views.get_file),

	path('test', google_api.test_endpoint),
	path('gp-sync', cloud.google_api.google_sync_now),
	path('get-gp-sync-status', cloud.google_api.get_google_sync_status),
	path('google-consent', cloud.google_api.google_consent),
	path('oauth2callback', cloud.google_api.oauth2_callback)
	
]
