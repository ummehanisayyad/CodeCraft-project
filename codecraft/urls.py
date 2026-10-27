"""
URL configuration for CodeCraft project.
"""

from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('', include('compiler_lab.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('learning/', include('learning.urls')),
]

handler404 = 'codecraft.views.custom_404_view'
handler500 = 'codecraft.views.custom_500_view'
