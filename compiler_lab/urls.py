"""
URL configuration for compiler_lab app.
"""

from django.urls import path
from . import views

app_name = 'compiler_lab'

urlpatterns = [
    path('workbench/', views.workbench_view, name='workbench'),
    path('api/analyze/', views.api_analyze_view, name='api_analyze'),
    path('api/examples/<int:pk>/', views.api_example_detail, name='api_example_detail'),
    path('history/', views.history_list_view, name='history_list'),
    path('history/<int:pk>/', views.history_detail_view, name='history_detail'),
    path('history/<int:pk>/delete/', views.history_delete_view, name='history_delete'),
    path('history/<int:pk>/export/json/', views.history_export_json, name='history_export_json'),
]
