"""
Views for learning app: educational modules, BNF grammar specifications, and academic about page.
"""

from django.shortcuts import render


def learning_hub(request):
    """Educational Hub covering all 6 phases of modern compiler design."""
    return render(request, 'learning/index.html', {'active_nav': 'learning'})


def grammar_reference(request):
    """Formal BNF grammar and language specification for Edu-C."""
    return render(request, 'learning/grammar.html', {'active_nav': 'grammar'})


def about_view(request):
    """Academic project documentation, methodology, and tech stack."""
    return render(request, 'learning/about.html', {'active_nav': 'about'})
