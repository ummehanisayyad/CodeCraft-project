"""
Context processors for CodeCraft platform.
Provides academic metadata, current platform statistics, and navigation helpers.
"""

def site_context(request):
    return {
        'SITE_NAME': 'CodeCraft',
        'SITE_TAGLINE': 'Interactive Compiler Design and Code Analysis Platform',
        'ACADEMIC_COURSE': 'Compiler Design (TEC)',
        'ACADEMIC_YEAR': 'Third Year B.E. CSE',
        'ACADEMIC_SEMESTER': 'Semester V',
        'SUPPORTED_LANGUAGE': 'C-Subset Language (Edu-C)',
    }
