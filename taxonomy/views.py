import json
import os
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils import timezone
from taxonomy.models import SKUItem
from ai_engine.gap_classifier import GeminiGapClassifier
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from dotenv import load_dotenv

load_dotenv()


def sku_list_view(request):
    """Vista principal del Dashboard del Maestro de Artículos PESCO."""
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')  # all, incomplete, complete, ai_processed
    missing_filter = request.GET.get('missing', '').strip()  # clase, familia, subfamilia, categoria

    # Filtros de taxonomía
    grupo_filter = request.GET.get('grupo', '').strip()
    clase_filter = request.GET.get('clase', '').strip()
    familia_filter = request.GET.get('familia', '').strip()
    subfamilia_filter = request.GET.get('subfamilia', '').strip()
    modelo_filter = request.GET.get('modelo', '').strip()
    categoria_filter = request.GET.get('categoria', '').strip()

    skus = SKUItem.objects.all().order_by('item_code')

    if query:
        skus = skus.filter(Q(item_code__icontains=query) | Q(item_name__icontains=query) | Q(nombre_grupo__icontains=query) | Q(modelo__icontains=query))

    if status_filter == 'incomplete':
        skus = skus.filter(is_incomplete=True)
    elif status_filter == 'complete':
        skus = skus.filter(is_incomplete=False)
    elif status_filter == 'ai_processed':
        skus = skus.filter(ai_processed=True)

    # Filtrar por campo específico pendiente
    if missing_filter == 'clase':
        skus = skus.filter(Q(clase__isnull=True) | Q(clase=''))
    elif missing_filter == 'familia':
        skus = skus.filter(Q(familia__isnull=True) | Q(familia=''))
    elif missing_filter == 'subfamilia':
        skus = skus.filter(Q(subfamilia__isnull=True) | Q(subfamilia=''))
    elif missing_filter == 'categoria':
        skus = skus.filter(Q(categoria__isnull=True) | Q(categoria=''))

    # Filtros por valor de atributo
    if grupo_filter:
        skus = skus.filter(nombre_grupo=grupo_filter)
    if clase_filter:
        skus = skus.filter(clase=clase_filter)
    if familia_filter:
        skus = skus.filter(familia=familia_filter)
    if subfamilia_filter:
        skus = skus.filter(subfamilia=subfamilia_filter)
    if modelo_filter:
        skus = skus.filter(modelo=modelo_filter)
    if categoria_filter:
        skus = skus.filter(categoria=categoria_filter)

    # Métricas KPI para el Dashboard
    total_count = SKUItem.objects.count()
    sin_clase_count = SKUItem.objects.filter(Q(clase__isnull=True) | Q(clase='')).count()
    sin_familia_count = SKUItem.objects.filter(Q(familia__isnull=True) | Q(familia='')).count()
    sin_subfamilia_count = SKUItem.objects.filter(Q(subfamilia__isnull=True) | Q(subfamilia='')).count()
    sin_categoria_count = SKUItem.objects.filter(Q(categoria__isnull=True) | Q(categoria='')).count()
    incomplete_total = SKUItem.objects.filter(is_incomplete=True).count()
    ai_processed_count = SKUItem.objects.filter(ai_processed=True).count()

    # Listas distintivas para los menús desplegables de filtro
    grupos_list = SKUItem.objects.exclude(nombre_grupo__isnull=True).exclude(nombre_grupo='').values_list('nombre_grupo', flat=True).distinct().order_by('nombre_grupo')
    clases_list = SKUItem.objects.exclude(clase__isnull=True).exclude(clase='').values_list('clase', flat=True).distinct().order_by('clase')
    familias_list = SKUItem.objects.exclude(familia__isnull=True).exclude(familia='').values_list('familia', flat=True).distinct().order_by('familia')
    subfamilias_list = SKUItem.objects.exclude(subfamilia__isnull=True).exclude(subfamilia='').values_list('subfamilia', flat=True).distinct().order_by('subfamilia')
    modelos_list = SKUItem.objects.exclude(modelo__isnull=True).exclude(modelo='').values_list('modelo', flat=True).distinct().order_by('modelo')[:100]
    categorias_list = SKUItem.objects.exclude(categoria__isnull=True).exclude(categoria='').values_list('categoria', flat=True).distinct().order_by('categoria')

    paginator = Paginator(skus, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'missing_filter': missing_filter,
        'grupo_filter': grupo_filter,
        'clase_filter': clase_filter,
        'familia_filter': familia_filter,
        'subfamilia_filter': subfamilia_filter,
        'modelo_filter': modelo_filter,
        'categoria_filter': categoria_filter,
        'total_count': total_count,
        'sin_clase_count': sin_clase_count,
        'sin_familia_count': sin_familia_count,
        'sin_subfamilia_count': sin_subfamilia_count,
        'sin_categoria_count': sin_categoria_count,
        'incomplete_total': incomplete_total,
        'ai_processed_count': ai_processed_count,
        'grupos_list': grupos_list,
        'clases_list': clases_list,
        'familias_list': familias_list,
        'subfamilias_list': subfamilias_list,
        'modelos_list': modelos_list,
        'categorias_list': categorias_list,
    }
    return render(request, 'taxonomy/sku_list.html', context)


def process_single_sku_ai(request, pk):
    """Vista AJAX para procesar la IA en un único SKU con restricciones estrictas de SAP."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    sku = get_object_or_404(SKUItem, pk=pk)
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        return JsonResponse({'success': False, 'error': 'No se configuró la GEMINI_API_KEY en .env'}, status=400)

    try:
        classifier = GeminiGapClassifier(api_key=api_key)
        rag_matches = list(SKUItem.objects.filter(
            is_incomplete=False,
            nombre_grupo=sku.nombre_grupo
        ).values('item_name', 'clase', 'familia', 'subfamilia')[:3])

        current_data = {
            "clase": sku.clase,
            "familia": sku.familia,
            "subfamilia": sku.subfamilia,
            "categoria": sku.categoria
        }

        allowed_clases = list(SKUItem.objects.exclude(clase__isnull=True).exclude(clase='').values_list('clase', flat=True).distinct())
        allowed_familias = list(SKUItem.objects.exclude(familia__isnull=True).exclude(familia='').values_list('familia', flat=True).distinct())

        result = classifier.fill_missing_fields(
            sku.item_name,
            sku.nombre_grupo or "",
            current_data,
            sku.pending_fields,
            rag_matches,
            allowed_clases=allowed_clases,
            allowed_familias=allowed_familias
        )

        if "clase" in sku.pending_fields and result.clase:
            if not allowed_clases or result.clase in allowed_clases:
                sku.clase = result.clase

        if "familia" in sku.pending_fields and result.familia:
            if not allowed_familias or result.familia in allowed_familias:
                sku.familia = result.familia

        if "subfamilia" in sku.pending_fields and result.subfamilia:
            sku.subfamilia = result.subfamilia

        if "categoria" in sku.pending_fields and result.categoria:
            sku.categoria = result.categoria

        sku.ai_confidence_score = result.confidence
        sku.ai_rationale = result.rationale
        sku.ai_processed = True
        sku.ai_processed_at = timezone.now()
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


def update_sku_taxonomy(request, pk):
    """Vista AJAX para modificación manual de la taxonomía por parte del usuario."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    sku = get_object_or_404(SKUItem, pk=pk)
    try:
        data = json.loads(request.body)
        sku.clase = data.get('clase', sku.clase)
        sku.familia = data.get('familia', sku.familia)
        sku.subfamilia = data.get('subfamilia', sku.subfamilia)
        sku.modelo = data.get('modelo', sku.modelo)
        sku.categoria = data.get('categoria', sku.categoria)

        # Limpiar vacíos a None
        sku.clase = sku.clase.strip() if sku.clase and sku.clase.strip() else None
        sku.familia = sku.familia.strip() if sku.familia and sku.familia.strip() else None
        sku.subfamilia = sku.subfamilia.strip() if sku.subfamilia and sku.subfamilia.strip() else None
        sku.modelo = sku.modelo.strip() if sku.modelo and sku.modelo.strip() else None
        sku.categoria = sku.categoria.strip() if sku.categoria and sku.categoria.strip() else None

        sku.check_incomplete()
        sku.save()

        return JsonResponse({
            'success': True,
            'clase': sku.clase or '--',
            'familia': sku.familia or '--',
            'subfamilia': sku.subfamilia or '--',
            'modelo': sku.modelo or '--',
            'categoria': sku.categoria or '--',
            'is_incomplete': sku.is_incomplete,
            'pending_fields': sku.pending_fields,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def export_ti_excel_view(request):
    """Genera un archivo Excel profesional de auditoría e informe para el equipo de TI."""
    export_scope = request.GET.get('scope', 'ai_processed')  # ai_processed, all, incomplete

    if export_scope == 'ai_processed':
        skus = SKUItem.objects.filter(ai_processed=True).order_by('item_code')
    elif export_scope == 'incomplete':
        skus = SKUItem.objects.filter(is_incomplete=True).order_by('item_code')
    else:
        skus = SKUItem.objects.all().order_by('item_code')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Informe TI - Taxonomía IA"

    # Estilos de Excel
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')

    headers = [
        'ItemCode (SAP)', 'ItemName (Descripción)', 'Nombre Grupo',
        'Clase', 'Familia', 'SubFamilia (Marca)', 'Modelo', 'Categoría',
        'Confianza IA (%)', 'Razonamiento Técnico IA', 'Evaluado por IA', 'Fecha Procesamiento'
    ]

    ws.append(headers)

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')

    for sku in skus:
        proc_date = sku.ai_processed_at.strftime('%Y-%m-%d %H:%M:%S') if sku.ai_processed_at else 'N/A'
        conf_pct = f"{int(sku.ai_confidence_score * 100)}%" if sku.ai_confidence_score else 'N/A'
        
        row_data = [
            sku.item_code,
            sku.item_name,
            sku.nombre_grupo or '',
            sku.clase or '',
            sku.familia or '',
            sku.subfamilia or '',
            sku.modelo or '',
            sku.categoria or '',
            conf_pct,
            sku.ai_rationale or '',
            'SI' if sku.ai_processed else 'NO',
            proc_date
        ]
        ws.append(row_data)

    # Ajustar ancho de columnas automáticamente
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 60)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"PESCO_Informe_Taxonomia_TI_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response
