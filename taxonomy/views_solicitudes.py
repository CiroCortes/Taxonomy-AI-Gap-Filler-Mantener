# -*- coding: utf-8 -*-
"""
views_solicitudes.py
Modulo de Solicitudes: Login, Creacion de Codigos y Compras.
"""
import json
import re
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from decimal import Decimal
from google import genai
from google.genai import types as genai_types

from taxonomy.models import SKUItem, CodeCreationRequest, PurchaseRequest


def is_admin(user):
    return user.is_active and user.is_staff


def login_view(request):
    error = None
    if request.user.is_authenticated:
        return redirect('taxonomy:solicitudes_dashboard') if is_admin(request.user) else redirect('taxonomy:solicitudes_nueva_codigo')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username',''), password=request.POST.get('password',''))
        if user:
            login(request, user)
            return redirect('taxonomy:solicitudes_dashboard') if is_admin(user) else redirect('taxonomy:solicitudes_nueva_codigo')
        else:
            error = "Usuario o contrasena incorrectos."
    return render(request, 'solicitudes/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('taxonomy:login')


@login_required
@user_passes_test(is_admin, login_url='/login/')
def solicitudes_dashboard_view(request):
    status_filter = request.GET.get('status', 'pendiente')
    code_requests = CodeCreationRequest.objects.all()
    purchase_requests = PurchaseRequest.objects.all()
    if status_filter != 'all':
        code_requests = code_requests.filter(status=status_filter)
        purchase_requests = purchase_requests.filter(status=status_filter)
    context = {
        'code_requests': code_requests,
        'purchase_requests': purchase_requests,
        'status_filter': status_filter,
        'pending_codes_count': CodeCreationRequest.objects.filter(status='pendiente').count(),
        'pending_purchases_count': PurchaseRequest.objects.filter(status='pendiente').count(),
    }
    return render(request, 'solicitudes/dashboard_admin.html', context)


@login_required
@user_passes_test(is_admin, login_url='/login/')
def approve_code_request(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    obj = get_object_or_404(CodeCreationRequest, pk=pk)
    action = request.POST.get('action')
    obj.admin_notes = request.POST.get('admin_notes', '').strip()
    if action == 'approve':
        obj.status = 'aprobado'
    elif action == 'reject':
        obj.status = 'rechazado'
    obj.save()
    return JsonResponse({'success': True, 'new_status': obj.get_status_display()})


@login_required
@user_passes_test(is_admin, login_url='/login/')
def approve_purchase_request(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    obj = get_object_or_404(PurchaseRequest, pk=pk)
    action = request.POST.get('action')
    obj.admin_notes = request.POST.get('admin_notes', '').strip()
    if action == 'approve':
        obj.status = 'aprobado'
    elif action == 'reject':
        obj.status = 'rechazado'
    obj.save()
    return JsonResponse({'success': True, 'new_status': obj.get_status_display()})


@login_required
def nueva_solicitud_codigo_view(request):
    if request.method == 'POST':
        data = request.POST
        base_sku = None
        base_sku_id = data.get('base_sku_id')
        if base_sku_id:
            try:
                base_sku = SKUItem.objects.get(pk=int(base_sku_id))
            except (SKUItem.DoesNotExist, ValueError):
                pass
        solicitud = CodeCreationRequest.objects.create(
            base_sku=base_sku,
            generated_code=data.get('generated_code', '').strip(),
            solicitante_nombre=data.get('solicitante_nombre', '').strip(),
            proposed_description=data.get('proposed_description', '').strip(),
            justification=data.get('justification', '').strip(),
            clase_propuesta=data.get('clase_propuesta', '').strip() or None,
            familia_propuesta=data.get('familia_propuesta', '').strip() or None,
            subfamilia_propuesta=data.get('subfamilia_propuesta', '').strip() or None,
            categoria_propuesta=data.get('categoria_propuesta', '').strip() or None,
        )
        _enviar_correo_creacion(solicitud)
        return JsonResponse({'success': True, 'id': solicitud.pk})
    return render(request, 'solicitudes/form_creacion_codigo.html')


def _enviar_correo_creacion(solicitud):
    dest = getattr(settings, 'ABASTECIMIENTO_EMAIL', 'abastecimiento@pesco.cl')
    base_info = f"Base: {solicitud.base_sku.item_code} - {solicitud.base_sku.item_name}" if solicitud.base_sku else "Sin codigo base"
    try:
        send_mail(
            subject=f"[PESCO] Nueva Solicitud de Codigo #{solicitud.pk} - {solicitud.solicitante_nombre}",
            message=(
                f"Nueva solicitud de creacion de codigo SAP.\n\n"
                f"ID: #{solicitud.pk}\nSolicitante: {solicitud.solicitante_nombre}\n"
                f"Codigo propuesto: {solicitud.generated_code or 'Pendiente'}\n"
                f"Descripcion: {solicitud.proposed_description}\n"
                f"Motivo: {solicitud.justification}\n{base_info}\n\n"
                f"Portal: http://127.0.0.1:8000/solicitudes/"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[dest],
            fail_silently=True,
        )
    except Exception:
        pass


@login_required
def nueva_solicitud_compra_view(request):
    if request.method == 'POST':
        data = request.POST
        try:
            cant = Decimal(str(data.get('cantidad_solicitada','0') or '0'))
            cu = Decimal(str(data.get('costo_unitario','0') or '0'))
            ct = cant * cu
        except Exception:
            cant, cu, ct = 0, 0, 0
        solicitud = PurchaseRequest.objects.create(
            solicitante_nombre=data.get('solicitante_nombre','').strip(),
            proveedor=data.get('proveedor','').strip() or None,
            codigo_compra=data.get('codigo_compra','').strip() or None,
            descripcion=data.get('descripcion','').strip(),
            cantidad_solicitada=cant,
            costo_unitario=cu,
            costo_total=ct,
            tipo_compra=data.get('tipo_compra','stock'),
            justification=data.get('justification','').strip() or None,
        )
        dest = getattr(settings, 'ABASTECIMIENTO_EMAIL', 'abastecimiento@pesco.cl')
        try:
            send_mail(
                subject=f"[PESCO] Nueva Solicitud de Compra #{solicitud.pk} - {solicitud.solicitante_nombre}",
                message=(
                    f"Nueva solicitud de compra.\n\n"
                    f"ID: #{solicitud.pk}\nSolicitante: {solicitud.solicitante_nombre}\n"
                    f"Proveedor: {solicitud.proveedor or '-'}\nCodigo: {solicitud.codigo_compra or '-'}\n"
                    f"Descripcion: {solicitud.descripcion}\nCantidad: {solicitud.cantidad_solicitada}\n"
                    f"Costo Unit.: ${solicitud.costo_unitario}\nCosto Total: ${solicitud.costo_total}\n"
                    f"Tipo: {solicitud.get_tipo_compra_display()}\n\nPortal: http://127.0.0.1:8000/solicitudes/"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[dest],
                fail_silently=True,
            )
        except Exception:
            pass
        return JsonResponse({'success': True, 'id': solicitud.pk})
    return render(request, 'solicitudes/form_compra.html')


def api_next_correlative(request, base_sku_code):
    try:
        base_sku = get_object_or_404(SKUItem, item_code=base_sku_code)
        code = base_sku.item_code.strip()
        match = re.match(r'^([A-Za-z\-_\.]+)(\d+)$', code)
        if not match:
            match = re.match(r'^(\d{1,6})(\d{4,})$', code)
        if match:
            prefix = match.group(1)
            num_part = match.group(2)
            num_len = len(num_part)
            similar = SKUItem.objects.filter(item_code__startswith=prefix)
            max_num = 0
            for sku in similar:
                m2 = re.match(rf'^{re.escape(prefix)}(\d+)$', sku.item_code.strip())
                if m2:
                    n = int(m2.group(1))
                    if n > max_num:
                        max_num = n
            next_code = f"{prefix}{str(max_num + 1).zfill(num_len)}"
        else:
            next_code = f"{code}_NUEVO"
        return JsonResponse({
            'success': True,
            'base_code': code,
            'next_code': next_code,
            'base_item_name': base_sku.item_name,
            'base_clase': base_sku.clase or '',
            'base_familia': base_sku.familia or '',
            'base_subfamilia': base_sku.subfamilia or '',
            'base_categoria': base_sku.categoria or '',
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def api_buscar_skus(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    qs = SKUItem.objects.filter(
        Q(item_code__icontains=q) | Q(item_name__icontains=q)
    ).values('id', 'item_code', 'item_name', 'clase', 'familia', 'subfamilia', 'categoria')[:15]
    return JsonResponse({'results': list(qs)})


@require_POST
def api_ai_assistant(request):
    try:
        body = json.loads(request.body)
        descripcion = body.get('descripcion', '').strip()
        justificacion = body.get('justificacion', '').strip()
        base_item_name = body.get('base_item_name', '').strip()
        tipo = body.get('tipo', 'codigo')

        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            return JsonResponse({'success': False, 'error': 'API Key no configurada.'}, status=500)

        client = genai.Client(api_key=api_key)

        if tipo == 'codigo':
            prompt = f"""Eres un experto en catalogos de maestros de articulos para una empresa industrial y de construccion (PESCO S.A.).
Mejora y estandariza la descripcion del nuevo articulo siguiendo el estilo SAP de PESCO.

Articulo base de referencia: "{base_item_name}"
Descripcion ingresada: "{descripcion}"
Justificacion: "{justificacion}"

Responde SOLO en JSON sin texto adicional:
{{
  "descripcion_mejorada": "descripcion estandarizada en mayusculas, concisa (max 100 caracteres)",
  "sugerencias": ["consejo 1", "consejo 2"],
  "advertencias": ["advertencia si hay riesgo de duplicado o info faltante"],
  "completitud_score": 85
}}"""
        else:
            prompt = f"""Eres un experto en compras y abastecimiento industrial para PESCO S.A.
Analiza y mejora esta solicitud de compra.

Articulo: "{descripcion}"
Justificacion: "{justificacion}"

Responde SOLO en JSON sin texto adicional:
{{
  "descripcion_mejorada": "descripcion tecnica clara del articulo",
  "sugerencias": ["consejo 1", "consejo 2"],
  "advertencias": ["advertencia si falta info critica"],
  "completitud_score": 85
}}"""

        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            )
        )
        result = json.loads(response.text)
        return JsonResponse({'success': True, **result})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
