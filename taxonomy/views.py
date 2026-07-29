import json
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Count
from taxonomy.models import SKUItem
from ai_engine.gap_classifier import GeminiGapClassifier
import os
from dotenv import load_dotenv

load_dotenv()


def sku_list_view(request):
    """Vista principal del Dashboard del Maestro de Artículos PESCO."""
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')  # all, incomplete, complete
    clase_filter = request.GET.get('clase', '')
    familia_filter = request.GET.get('familia', '')

    skus = SKUItem.objects.all().order_by('item_code')

    if query:
        skus = skus.filter(Q(item_code__icontains=query) | Q(item_name__icontains=query) | Q(nombre_grupo__icontains=query))

    if status_filter == 'incomplete':
        skus = skus.filter(is_incomplete=True)
    elif status_filter == 'complete':
        skus = skus.filter(is_incomplete=False)

    if clase_filter:
        skus = skus.filter(clase=clase_filter)

    if familia_filter:
        skus = skus.filter(familia=familia_filter)

    # MÃ©tricas KPI para el Dashboard
    total_count = SKUItem.objects.count()
    sin_clase_count = SKUItem.objects.filter(Q(clase__isnull=True) | Q(clase='')).count()
    sin_familia_count = SKUItem.objects.filter(Q(familia__isnull=True) | Q(familia='')).count()
    sin_subfamilia_count = SKUItem.objects.filter(Q(subfamilia__isnull=True) | Q(subfamilia='')).count()
    incomplete_total = SKUItem.objects.filter(is_incomplete=True).count()

    paginator = Paginator(skus, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'clase_filter': clase_filter,
        'familia_filter': familia_filter,
        'total_count': total_count,
        'sin_clase_count': sin_clase_count,
        'sin_familia_count': sin_familia_count,
        'sin_subfamilia_count': sin_subfamilia_count,
        'incomplete_total': incomplete_total,
        'clases_list': SKUItem.objects.exclude(clase__isnull=True).exclude(clase='').values_list('clase', flat=True).distinct()[:30],
    }
    return render(request, 'taxonomy/sku_list.html', context)


def process_single_sku_ai(request, pk):
    """Vista AJAX para procesar la IA en un Ãºnico SKU."""
    if request.method != 'POST':
        return JsonResponse({'error': 'MÃ©todo no permitido'}, status=405)

    sku = get_object_or_404(SKUItem, pk=pk)
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        return JsonResponse({'success': False, 'error': 'No se configurÃ³ la GEMINI_API_KEY en .env'}, status=400)

    try:
        classifier = GeminiGapClassifier(api_key=api_key)
        rag_matches = list(SKUItem.objects.filter(
            is_incomplete=False,
            nombre_grupo=sku.nombre_grupo
        ).values('item_name', 'familia', 'subfamilia')[:3])

        current_data = {
            "clase": sku.clase,
            "familia": sku.familia,
            "subfamilia": sku.subfamilia,
            "categoria": sku.categoria
        }

        result = classifier.fill_missing_fields(
            sku.item_name,
            sku.nombre_grupo or "",
            current_data,
            sku.pending_fields,
            rag_matches
        )

        if "clase" in sku.pending_fields and result.clase:
            sku.clase = result.clase
        if "familia" in sku.pending_fields and result.familia:
            sku.familia = result.familia
        if "subfamilia" in sku.pending_fields and result.subfamilia:
            sku.subfamilia = result.subfamilia
        if "categoria" in sku.pending_fields and result.categoria:
            sku.categoria = result.categoria

        sku.ai_confidence_score = result.confidence
        sku.ai_rationale = result.rationale
        sku.check_incomplete()
        sku.save()

        return JsonResponse({
            'success': True,
            'clase': sku.clase,
            'familia': sku.familia,
            'subfamilia': sku.subfamilia,
            'categoria': sku.categoria,
            'confidence': sku.ai_confidence_score,
            'rationale': sku.ai_rationale,
            'is_incomplete': sku.is_incomplete,
            'pending_fields': sku.pending_fields,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
