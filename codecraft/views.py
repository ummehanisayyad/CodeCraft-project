"""
Root views for CodeCraft: Landing Page and Error Handlers.
"""

from django.shortcuts import render
from compiler_lab.models import CodeExample


def home_view(request):
    """
    Renders the modern, interactive CodeCraft landing page.
    """
    sample_examples = CodeExample.objects.all()[:3]
    return render(request, 'landing.html', {
        'sample_examples': sample_examples,
        'active_nav': 'home'
    })


def custom_404_view(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def custom_500_view(request):
    return render(request, 'errors/500.html', status=500)
