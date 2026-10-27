"""
Database Models for CodeCraft Compiler Lab.
Stores persistent compiler analysis history and preset code examples.
"""

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class AnalysisRecord(models.Model):
    """
    Stores a complete run of the compiler pipeline, associated with a user or guest.
    Enforces ownership isolation so users only access their own history.
    """
    MODE_CHOICES = [
        ('all', 'Full Pipeline (Lexical + Syntax + Semantic + TAC + Optimization)'),
        ('lexical', 'Lexical Analysis Only'),
        ('syntax', 'Syntax Analysis (AST) Only'),
        ('semantic', 'Semantic Analysis & Symbol Table'),
        ('tac', 'Intermediate Code Generation (TAC)'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analyses',
        null=True,
        blank=True,
        help_text="User who executed this analysis. Null for guest runs."
    )
    title = models.CharField(max_length=120, default="Compiler Analysis")
    language = models.CharField(max_length=50, default="c_subset")
    source_code = models.TextField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='all')
    is_success = models.BooleanField(default=True)
    error_stage = models.CharField(max_length=30, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    token_count = models.PositiveIntegerField(default=0)
    execution_time_ms = models.FloatField(default=0.0)

    # Structured compiler outputs stored as JSON
    tokens_json = models.JSONField(default=list, blank=True)
    ast_json = models.JSONField(default=dict, blank=True)
    mermaid_graph = models.TextField(blank=True)
    text_tree = models.TextField(blank=True)
    symbols_json = models.JSONField(default=list, blank=True)
    semantic_errors = models.JSONField(default=list, blank=True)
    semantic_warnings = models.JSONField(default=list, blank=True)
    tac_instructions = models.JSONField(default=list, blank=True)
    quadruples_json = models.JSONField(default=list, blank=True)
    optimized_tac = models.JSONField(default=list, blank=True)
    optimizations_json = models.JSONField(default=list, blank=True)
    metrics_json = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Analysis Record'
        verbose_name_plural = 'Analysis Records'

    def __str__(self):
        user_str = self.user.username if self.user else "Guest"
        status_str = "Success" if self.is_success else f"Error ({self.error_stage})"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {user_str} - {self.title} ({status_str})"

    def get_absolute_url(self):
        return reverse('compiler_lab:history_detail', kwargs={'pk': self.pk})

    @property
    def snippet(self) -> str:
        first_line = self.source_code.strip().split('\n')[0]
        if len(first_line) > 55:
            return first_line[:55] + "..."
        return first_line or "(empty code)"


class CodeExample(models.Model):
    """
    Curated sample code snippets for demonstration, testing, and lab assignments.
    """
    CATEGORY_CHOICES = [
        ('basic', 'Basic Expressions & Declarations'),
        ('control', 'Control Flow (If-Else & While)'),
        ('semantic', 'Semantic Type & Scope Demonstrations'),
        ('optimization', 'Constant Folding & Code Optimization'),
        ('errors', 'Syntax & Lexical Error Handling'),
    ]

    title = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='basic')
    description = models.TextField(blank=True)
    code = models.TextField()
    expected_stage = models.CharField(max_length=30, default='all')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Code Example'
        verbose_name_plural = 'Code Examples'

    def __str__(self):
        return f"{self.title} [{self.get_category_display()}]"
