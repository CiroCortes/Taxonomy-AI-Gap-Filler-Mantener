from django.urls import path
from taxonomy import views
from taxonomy import views_solicitudes

app_name = 'taxonomy'

urlpatterns = [
    # ─── Maestro / Dashboard IA ────────────────────────────────────────────────
    path('', views.sku_list_view, name='sku_list'),
    path('api/kpi-stats/', views.get_kpi_stats_view, name='get_kpi_stats'),
    path('upload/excel/', views.upload_sap_excel_view, name='upload_sap_excel'),
    path('batch-ai/', views.batch_ai_view, name='batch_ai'),
    path('batch-ai/process/', views.process_batch_ai_ajax, name='process_batch_ai'),
    path('sku/<int:pk>/process_ai/', views.process_single_sku_ai, name='process_single_sku_ai'),
    path('sku/<int:pk>/update_taxonomy/', views.update_sku_taxonomy, name='update_sku_taxonomy'),
    path('export/excel/', views.export_ti_excel_view, name='export_ti_excel'),

    # ─── Autenticación ─────────────────────────────────────────────────────────
    path('login/', views_solicitudes.login_view, name='login'),
    path('logout/', views_solicitudes.logout_view, name='logout'),

    # ─── Portal de Solicitudes ─────────────────────────────────────────────────
    path('solicitudes/', views_solicitudes.solicitudes_dashboard_view, name='solicitudes_dashboard'),
    path('solicitudes/nuevo-codigo/', views_solicitudes.nueva_solicitud_codigo_view, name='solicitudes_nueva_codigo'),
    path('solicitudes/nueva-compra/', views_solicitudes.nueva_solicitud_compra_view, name='solicitudes_nueva_compra'),

    # ─── Acciones de Aprobación (Admin) ────────────────────────────────────────
    path('solicitudes/codigo/<int:pk>/accion/', views_solicitudes.approve_code_request, name='approve_code_request'),
    path('solicitudes/compra/<int:pk>/accion/', views_solicitudes.approve_purchase_request, name='approve_purchase_request'),

    # ─── APIs Internas ─────────────────────────────────────────────────────────
    path('api/next-correlative/<str:base_sku_code>/', views_solicitudes.api_next_correlative, name='api_next_correlative'),
    path('api/buscar-skus/', views_solicitudes.api_buscar_skus, name='api_buscar_skus'),
    path('api/ai-assistant/', views_solicitudes.api_ai_assistant, name='api_ai_assistant'),
]
