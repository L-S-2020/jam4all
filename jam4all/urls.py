"""
URL configuration for jam4all project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.start_auth_spotify, name='start_auth_spotify'),
    path('login', views.login_spotify, name='login_spotify'),
    path('callback', views.callback_spotify, name='callback_spotify'),
    path('home', views.home, name='home'),
    path('api/create_jam', views.create_jam, name='create_jam'),
    path('jam/<str:jam_code>', views.jam_details, name='jam_details'),
    path('join', views.join_jam, name='join_jam'),
    path('search', views.search_song, name='search_song'),
    path('api/add_queue', views.add_song_to_queue, name='add_song_to_queue'),
]