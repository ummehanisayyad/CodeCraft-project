"""
Views for dashboard app: user analytics, pipeline metrics, and activity charts.
"""

import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum
from compiler_lab.models import AnalysisRecord, CodeExample


@login_required
def dashboard_index(request):
    """
    Renders user dashboard with execution metrics, status breakdowns, and Chart.js visuals.
    """
    user = request.user
    user_analyses = AnalysisRecord.objects.filter(user=user)

    total_analyses = user_analyses.count()
    success_count = user_analyses.filter(is_success=True).count()
    failed_count = user_analyses.filter(is_success=False).count()
    success_rate = round((success_count / total_analyses * 100), 1) if total_analyses > 0 else 100.0

    recent_records = user_analyses[:6]

    # Aggregations for charts
    mode_counts = dict(
        user_analyses.values('mode').annotate(count=Count('id')).values_list('mode', 'count')
    )
    chart_modes = {
        'all': mode_counts.get('all', 0),
        'lexical': mode_counts.get('lexical', 0),
        'syntax': mode_counts.get('syntax', 0),
        'semantic': mode_counts.get('semantic', 0),
        'tac': mode_counts.get('tac', 0),
    }

    # Error stage breakdown
    error_stages = dict(
        user_analyses.filter(is_success=False).values('error_stage').annotate(count=Count('id')).values_list('error_stage', 'count')
    )

    avg_latency = user_analyses.aggregate(avg=Avg('execution_time_ms'))['avg'] or 0.0
    total_tokens = user_analyses.aggregate(sum=Sum('token_count'))['sum'] or 0

    examples = CodeExample.objects.all()[:4]

    context = {
        'total_analyses': total_analyses,
        'success_count': success_count,
        'failed_count': failed_count,
        'success_rate': success_rate,
        'recent_records': recent_records,
        'avg_latency': round(avg_latency, 2),
        'total_tokens': total_tokens,
        'chart_modes_json': json.dumps(chart_modes),
        'error_stages_json': json.dumps(error_stages),
        'examples': examples,
        'active_nav': 'dashboard'
    }
    return render(request, 'dashboard/index.html', context)
