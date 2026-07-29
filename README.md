# PESCO S.A. SKU AI Gap-Filler & Taxonomy Mantener

[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![FastMCP](https://img.shields.io/badge/FastMCP-Auditor-000000?style=for-the-badge)](https://modelcontextprotocol.io)
[![Pytest](https://img.shields.io/badge/Pytest-Passed-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)

Sistema de resoluciÃ³n incremental de brechas taxonÃ³micas (**Gap-Filling**) y catalogaciÃ³n inteligente para el **Maestro de ArtÃ­culos de PESCO S.A.** extraÃ­do desde SAP ERP ERP (20.297 SKUs), basado en **Spec-Driven Development (SDD)**.

---

## 🎯 Objetivo del Proyecto

Catalogar de forma automatizada y sin reprocesar datos previamente consolidados las brechas de taxonomÃ­a faltantes en los productos de PESCO S.A.:
- **`Clase`** (Pendientes: 1.076)
- **`Familia`** (Pendientes: 4.592)
- **`SubFamilia`** (Pendientes: 3.627)
- **`CategorÃ­a`** (Operacional)

Utiliza un enfoque anti-alucinaciÃ³n combinando **Motor Determinista + Few-Shot Prompting con Salida Estructurada JSON Schema (Gemini 2.5 Flash / Pydantic) + RAG Local** sobre los ~15.700 SKUs con taxonomÃ­a completa.

---

## 🏗️ Arquitectura del Sistema (Django MVT)

```text
mantenedor_maestro/
├── pesco_project/             # Configuración global de Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── taxonomy/                  # Aplicación principal de Taxonomía
│   ├── models.py              # Modelo SKUItem y auditoría check_incomplete()
│   ├── views.py               # Dashboard MVT y endpoint AJAX de IA
│   ├── urls.py
│   └── management/commands/
│       ├── load_sap_excel.py        # Importador masivo del Maestro (20.297 filas en 3s)
│       └── process_pending_skus.py  # Pipeline incremental IA + RAG Local
├── ai_engine/                 # Motor de Clasificación IA
│   └── gap_classifier.py      # GeminiGapClassifier + DynamicTaxonomyFill Pydantic
├── mcp_server/                # Servidor FastMCP Auditor
│   └── pesco_mcp.py           # Herramienta get_pending_summary()
├── templates/                 # Interfaz Gráfica Web (HTML5/CSS3 Dark Mode)
│   ├── base.html
│   └── taxonomy/sku_list.html
├── tests/                     # Test Harness Automatizado
│   └── test_gap_classifier.py
├── .env.example
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## 🚀 GuÃ­a de InstalaciÃ³n y EjecuciÃ³n

### 1. Clonar el Repositorio e Instalar Entorno
```powershell
git clone https://github.com/CiroCortes/Taxonomy-AI-Gap-Filler-Mantener.git
cd Taxonomy-AI-Gap-Filler-Mantener

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno
Copia la plantilla y configura tu API Key de Gemini:
```powershell
cp .env.example .env
```
En el archivo `.env`:
```env
GEMINI_API_KEY=tu_api_key_de_gemini
```

### 3. Migraciones e ImportaciÃ³n Masiva del Maestro SAP
```powershell
python manage.py migrate
python manage.py load_sap_excel --file "2907 - 00.- Maestro Articulos v7.xlsx"
```

### 4. Iniciar el Dashboard Web (MVT)
```powershell
python manage.py runserver
```
Ingresa a [http://127.0.0.1:8000/](http://127.0.0.1:8000/) en tu navegador.

### 5. Procesamiento Incremental con IA Gemini + RAG
```powershell
# Procesar una tanda de 50 SKUs incompletos
python manage.py process_pending_skus --limit 50
```

### 6. AuditorÃ­a en Tiempo Real (FastMCP)
```powershell
python -c "from mcp_server.pesco_mcp import get_pending_summary; print(get_pending_summary())"
```

---

## 🧪 Pruebas Automatizadas (Pytest)
```powershell
pytest
```

---

## 📄 Licencia
PESCO S.A. - Todos los derechos reservados.
