# PESCO S.A. SKU AI Gap-Filler & Taxonomy Mantener

Sistema inteligente de resoluciÃ³n incremental de brechas taxonÃ³micas (Gap-Filling) para el Maestro de ArtÃ­culos de PESCO S.A. extraÃ­do desde SAP ERP.

## Arquitectura y TecnologÃ­as
- **Framework Core**: Django 5.2 (MVT + ORM)
- **Motor de IA**: Google Gemini 2.5 Flash / 1.5 Flash (`google-genai` / `google-generativeai`) + Salida estructurada Pydantic (`DynamicTaxonomyFill`)
- **RAG Local**: ContextualizaciÃ³n dinÃ¡mica basada en los 15.700 SKUs completos por grupo operativo.
- **Servidor MCP Auditor**: FastMCP (`mcp_server/pesco_mcp.py`) para monitoreo de brechas en tiempo real.
- **Testing**: Harness automatizado con `pytest` y `pytest-django`.

---

## GuÃ­a de Inicio RÃ¡pido

### 1. ActivaciÃ³n del Entorno Virtual
```powershell
.\venv\Scripts\activate
```

### 2. Variables de Entorno
Copia `.env.example` a `.env` y configura tu API Key de Gemini:
```env
GEMINI_API_KEY=tu_api_key_de_gemini
```

### 3. Migraciones de Base de Datos
```powershell
python manage.py migrate
```

### 4. Carga Masiva del Maestro SAP (20.297 SKUs)
Importa todos los registros del archivo Excel original en solo unos segundos:
```powershell
python manage.py load_sap_excel --file "2907 - 00.- Maestro Articulos v7.xlsx"
```

### 5. AuditorÃ­a en Tiempo Real (FastMCP)
Consulta las mÃ©tricas de brechas taxonÃ³micas:
```powershell
python -c "from mcp_server.pesco_mcp import get_pending_summary; print(get_pending_summary())"
```

### 6. Procesamiento Incremental con IA Gemini + RAG Local
Procesa los SKUs pendientes catalogando Ãºnicamente los atributos faltantes (`clase`, `familia`, `subfamilia`, `categoria`):
```powershell
python manage.py process_pending_skus --api-key "TU_GEMINI_API_KEY" --limit 100
```

### 7. EjecuciÃ³n de Tests Unitarios
```powershell
pytest
```
