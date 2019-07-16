from django.urls import path

from . import views

app_name = 'cloud'
urlpatterns = [
    path('', views.index),
	path('get-folder', views.get_folder),
	path('delete', views.delete),
	path('rename', views.rename),
	path('create-folder', views.create_folder),
]