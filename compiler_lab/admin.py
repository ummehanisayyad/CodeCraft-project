"""
Django Admin registration for compiler_lab models.
"""

from django.contrib import admin
from .models import AnalysisRecord, CodeExample


@admin.register(AnalysisRecord)
class AnalysisRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'mode', 'is_success', 'token_count', 'execution_time_ms', 'created_at')
    list_filter = ('is_success', 'mode', 'created_at')
    search_fields = ('title', 'source_code', 'user__username', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'execution_time_ms')


@admin.register(CodeExample)
class CodeExampleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'order')
    list_filter = ('category',)
    search_fields = ('title', 'description', 'code')
