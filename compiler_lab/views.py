"""
Views and API endpoints for CodeCraft Compiler Lab.
Includes the interactive Workbench, AJAX analysis API, and Analysis History management.
"""

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils.html import escape
from .models import AnalysisRecord, CodeExample
from .engine import CompilerPipeline


def workbench_view(request):
    """
    Renders the primary CodeCraft Compiler Workbench IDE.
    Loads examples, optional preset/history code, and configurations.
    """
    examples = CodeExample.objects.all().order_by('order', 'id')
    
    # Preloaded code logic
    initial_code = ""
    initial_title = ""
    initial_mode = "all"

    # Load from example parameter
    example_id = request.GET.get('example')
    if example_id:
        try:
            ex = CodeExample.objects.get(id=example_id)
            initial_code = ex.code
            initial_title = ex.title
            initial_mode = ex.expected_stage
        except CodeExample.DoesNotExist:
            pass

    # Load from previous history record (with ownership check)
    record_id = request.GET.get('record')
    if record_id and request.user.is_authenticated:
        try:
            rec = AnalysisRecord.objects.get(id=record_id, user=request.user)
            initial_code = rec.source_code
            initial_title = f"Rerun: {rec.title}"
            initial_mode = rec.mode
        except AnalysisRecord.DoesNotExist:
            pass

    # Fallback to default example if empty
    if not initial_code:
        first_ex = examples.first()
        if first_ex:
            initial_code = first_ex.code
            initial_title = first_ex.title
        else:
            initial_code = (
                "// CodeCraft Compiler Design Lab Sample\n"
                "int a = 15;\n"
                "int b = 4;\n"
                "int c = (a + b) * 2 - 8;\n"
                "if (c > 20) {\n"
                "    int result = c * 2;\n"
                "}\n"
            )
            initial_title = "Basic Arithmetic & Control Flow"

    context = {
        'examples': examples,
        'initial_code': initial_code,
        'initial_title': initial_title,
        'initial_mode': initial_mode,
        'active_nav': 'workbench'
    }
    return render(request, 'compiler_lab/workbench.html', context)


@require_POST
def api_analyze_view(request):
    """
    Primary API endpoint for code analysis.
    Accepts JSON or POST parameters, runs the compiler pipeline,
    and returns rich structured JSON results with persistence for logged-in users.
    """
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST

        source_code = data.get('source_code', '')
        mode = data.get('mode', 'all')
        title = data.get('title', '').strip() or 'Interactive Analysis'
        run_optimizer = data.get('optimize', True)
        if isinstance(run_optimizer, str):
            run_optimizer = run_optimizer.lower() in ('true', '1', 'yes')

        # Run compilation pipeline
        pipeline = CompilerPipeline(
            source_code=source_code,
            mode=mode,
            run_optimizer=run_optimizer
        )
        result = pipeline.execute()

        # Persist record for authenticated users
        record_id = None
        if request.user.is_authenticated and source_code.strip():
            record = AnalysisRecord.objects.create(
                user=request.user,
                title=title[:120],
                language='c_subset',
                source_code=source_code,
                mode=mode,
                is_success=result['is_success'],
                error_stage=result.get('error_stage'),
                error_message=result.get('error_message'),
                token_count=len(result.get('tokens', [])),
                execution_time_ms=result.get('total_time_ms', 0.0),
                tokens_json=result.get('tokens', []),
                ast_json=result.get('ast') or {},
                mermaid_graph=result.get('mermaid_graph', ''),
                text_tree=result.get('text_tree', ''),
                symbols_json=result.get('symbols', []),
                semantic_errors=result.get('semantic_errors', []),
                semantic_warnings=result.get('semantic_warnings', []),
                tac_instructions=result.get('tac_instructions', []),
                quadruples_json=result.get('quadruples', []),
                optimized_tac=result.get('optimized_tac', []),
                optimizations_json=result.get('optimizations', []),
                metrics_json=result.get('metrics', {})
            )
            record_id = record.id

        result['record_id'] = record_id
        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({
            'is_success': False,
            'error_stage': 'request',
            'error_message': 'Malformed JSON request body.'
        }, status=400)
    except Exception as e:
        # Safe exception handling without leaking tracebacks
        return JsonResponse({
            'is_success': False,
            'error_stage': 'server',
            'error_message': f'Server analysis error: {str(e)}'
        }, status=500)


def api_example_detail(request, pk):
    """Returns the code and metadata of a code example."""
    example = get_object_or_404(CodeExample, pk=pk)
    return JsonResponse({
        'id': example.id,
        'title': example.title,
        'category': example.category,
        'description': example.description,
        'code': example.code,
        'expected_stage': example.expected_stage
    })


@login_required
def history_list_view(request):
    """
    Displays the paginated analysis history for the current authenticated user only.
    Prevents any unauthorized cross-user data leakage.
    """
    records = AnalysisRecord.objects.filter(user=request.user)

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        records = records.filter(title__icontains=q) | records.filter(source_code__icontains=q)

    # Status filter
    status = request.GET.get('status')
    if status == 'success':
        records = records.filter(is_success=True)
    elif status == 'failed':
        records = records.filter(is_success=False)

    # Mode filter
    mode = request.GET.get('mode')
    if mode in ['all', 'lexical', 'syntax', 'semantic', 'tac']:
        records = records.filter(mode=mode)

    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': q,
        'status_filter': status,
        'mode_filter': mode,
        'total_count': records.count(),
        'active_nav': 'history'
    }
    return render(request, 'compiler_lab/history_list.html', context)


@login_required
def history_detail_view(request, pk):
    """
    Detailed inspection of a past analysis record.
    Enforces strict ownership check: users can only view their own records.
    """
    record = get_object_or_404(AnalysisRecord, pk=pk, user=request.user)
    context = {
        'record': record,
        'active_nav': 'history'
    }
    return render(request, 'compiler_lab/history_detail.html', context)


@login_required
@require_POST
def history_delete_view(request, pk):
    """
    Deletes an analysis record with strict ownership verification.
    """
    record = get_object_or_404(AnalysisRecord, pk=pk, user=request.user)
    title = record.title
    record.delete()
    messages.success(request, f"Analysis record '{title}' was permanently deleted.")
    return redirect('compiler_lab:history_list')


@login_required
def history_export_json(request, pk):
    """
    Exports a specific analysis record as a downloadable JSON file.
    """
    record = get_object_or_404(AnalysisRecord, pk=pk, user=request.user)
    data = {
        'id': record.id,
        'title': record.title,
        'created_at': record.created_at.isoformat(),
        'mode': record.mode,
        'is_success': record.is_success,
        'source_code': record.source_code,
        'tokens': record.tokens_json,
        'ast': record.ast_json,
        'mermaid_graph': record.mermaid_graph,
        'text_tree': record.text_tree,
        'symbols': record.symbols_json,
        'semantic_errors': record.semantic_errors,
        'semantic_warnings': record.semantic_warnings,
        'tac_instructions': record.tac_instructions,
        'quadruples': record.quadruples_json,
        'optimized_tac': record.optimized_tac,
        'optimizations': record.optimizations_json,
        'metrics': record.metrics_json
    }
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    filename = f"codecraft_analysis_{record.id}_{record.created_at.strftime('%Y%m%d_%H%M%S')}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
