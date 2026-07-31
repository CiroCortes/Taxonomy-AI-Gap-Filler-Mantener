from django.urls import path
from taxonomy import views

app_name = 'taxonomy'

urlpatterns = [
    path('', views.sku_list_view, name='sku_list'),
    path('api/kpi-stats/', views.get_kpi_stats_view, name='get_kpi_stats'),
    path('upload/excel/', views.upload_sap_excel_view, name='upload_sap_excel'),
    path('batch-ai/', views.batch_ai_view, name='batch_ai'),
    path('batch-ai/process/', views.process_batch_ai_ajax, name='process_batch_ai'),
    path('sku/<int:pk>/process_ai/', views.process_single_sku_ai, name='process_single_sku_ai'),
    path('sku/<int:pk>/update_taxonomy/', views.update_sku_taxonomy, name='update_sku_taxonomy'),
    path('export/excel/', views.export_ti_excel_view, name='export_ti_excel'),
]
