"""
URL configuration for learning app.
"""

from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.learning_hub, name='hub'),
    path('grammar/', views.grammar_reference, name='grammar'),
    path('about/', views.about_view, name='about'),
]
