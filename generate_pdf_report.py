import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pesco_project.settings')
django.setup()

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from taxonomy.models import SKUItem
from django.db.models import Count, Q

class NumberedCanvas(canvas.Canvas):
    """Canvas de ReportLab que calcula el número total de páginas y agrega pie de página ejecutivo."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Franja superior decorativa
        self.setFillColor(colors.HexColor("#1F4E78"))
        self.rect(0, 775, 612, 17, fill=True, stroke=False)
        
        # Encabezado secundario en páginas > 1
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawString(54, 760, "PESCO S.A. | Informe Ejecutivo - Clasificación del Maestro de Artículos SAP")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 754, 558, 754)

        # Pie de página ejecutivo
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 30, "Documento Confidencial - Reservado para Jefatura y Gerencia PESCO S.A.")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 30, page_text)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 42, 558, 42)
        
        self.restoreState()


def build_pdf():
    pdf_filename = "Informe_Ejecutivo_Clasificacion_SAP_PAÑOL.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Estilos Ejecutivos Personalizados
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1F4E78"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0ea5e9"),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'ExecutiveH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'ExecutiveBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B")
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    table_cell_center = ParagraphStyle(
        'TableCellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
        alignment=1
    )

    story = []

    # --- ENCABEZADO PRINCIPAL ---
    story.append(Spacer(1, 10))
    story.append(Paragraph("INFORME EJECUTIVO: CLASIFICACIÓN Y OPTIMIZACIÓN DEL MAESTRO DE ARTÍCULOS SAP ERP", title_style))
    story.append(Paragraph("Fase Prioritaria de Implementación: Materiales de PAÑOL & Insumos Operacionales", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1F4E78"), spaceAfter=12))

    # Meta Info Box
    meta_data = [
        [
            Paragraph("<b>Preparado para:</b> Jefatura y Gerencia PESCO S.A.", body_style),
            Paragraph("<b>Fecha de Emisión:</b> Julio 2026", body_style)
        ],
        [
            Paragraph("<b>Área de Impacto:</b> Operaciones, Pañol, TI y Compras", body_style),
            Paragraph("<b>Estado del Proyecto:</b> En Fase de Despliegue Piloto", body_style)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[270, 234])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BORDER', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    # --- SECCIÓN 1: DEFINICIÓN DE CONCEPTOS ---
    story.append(Paragraph("1. ¿Qué es la Clasificación del Maestro de Artículos (Taxonomía)?", h1_style))
    story.append(Paragraph(
        "En términos sencillos de gestión empresarial, la <b>Clasificación de Materiales</b> (o taxonomía) es la "
        "<b>organización jerárquica y estandarizada de todos los repuestos y materiales en SAP ERP</b>. Consiste en asignar "
        "a cada código SKU cuatro atributos clave que definen con precisión su naturaleza:",
        body_style
    ))

    concepts_data = [
        [Paragraph("<b>Atributo en SAP</b>", table_header_style), Paragraph("<b>Definición Sencilla</b>", table_header_style), Paragraph("<b>Ejemplo Práctico en PESCO</b>", table_header_style)],
        [Paragraph("<b>Clase</b>", table_cell_bold), Paragraph("Tipo general al que pertenece el producto.", table_cell_style), Paragraph("<i>Herramientas, EPP, Adhesivos, Insumos</i>", table_cell_style)],
        [Paragraph("<b>Familia</b>", table_cell_bold), Paragraph("Subgrupo especializado dentro de la clase.", table_cell_style), Paragraph("<i>Brocas, Filtros, Guantes de Seguridad</i>", table_cell_style)],
        [Paragraph("<b>SubFamilia (Marca)</b>", table_cell_bold), Paragraph("Marca fabricante oficial del repuesto.", table_cell_style), Paragraph("<i>Bosch, 3M, Caterpillar, Altec</i>", table_cell_style)],
        [Paragraph("<b>Categoría Operacional</b>", table_cell_bold), Paragraph("Ámbito o destino de uso en la empresa.", table_cell_style), Paragraph("<i>Gestión Pañol, Taller, Operaciones</i>", table_cell_style)],
    ]
    t_concepts = Table(concepts_data, colWidths=[110, 244, 150])
    t_concepts.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F4E78")),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_concepts)
    story.append(Spacer(1, 10))

    # Importancia de la Clasificación Box
    callout_data = [[
        Paragraph(
            "<b>🎯 ¿Por qué es vital para la Gerencia?</b><br/>"
            "Un maestro de materiales incompleto genera duplicidad de compras, repuestos 'fantasmas' en bodegas y "
            "dificultad para cotizar con proveedores. Completar estos campos en SAP permite <b>comprar mejor, controlar inventarios "
            "y automatizar reportes financieros de costos.</b>",
            callout_style
        )
    ]]
    t_callout = Table(callout_data, colWidths=[504])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0F9FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0EA5E9")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_callout)
    story.append(Spacer(1, 14))

    # --- SECCIÓN 2: DIAGNÓSTICO GENERAL Y ENFOQUE EN PAÑOL ---
    story.append(Paragraph("2. Diagnóstico del Maestro General vs. Enfoque Prioritario en PAÑOL", h1_style))
    story.append(Paragraph(
        "A nivel global, la base de datos de PESCO cuenta con <b>20.297 SKUs en SAP</b>, de los cuales el <b>60,5% (12.275 SKUs)</b> "
        "ya se encuentran clasificados y un <b>39,5% (8.022 SKUs)</b> presenta brechas por completar.",
        body_style
    ))
    story.append(Paragraph(
        "Conforme a las prioridades definidas por la Jefatura para avanzar de inmediato en las áreas operacionales críticas, "
        "hemos aislado y priorizado el <b>bloque de materiales de PAÑOL</b>:",
        body_style
    ))

    # Consultar DB para datos exactos de Pañol
    panol_qs = SKUItem.objects.filter(nombre_grupo__icontains='PAÑOL')
    total_panol = panol_qs.count()
    incompletos_panol = panol_qs.filter(is_incomplete=True).count()
    completos_panol = panol_qs.filter(is_incomplete=False).count()
    pct_completos = (completos_panol / total_panol) * 100
    pct_incompletos = (incompletos_panol / total_panol) * 100

    kpi_table_data = [
        [
            Paragraph("<b>Métrica en Materiales de PAÑOL</b>", table_header_style),
            Paragraph("<b>Cantidad de SKUs</b>", table_header_style),
            Paragraph("<b>Porcentaje (%)</b>", table_header_style),
            Paragraph("<b>Estado de Gestión</b>", table_header_style)
        ],
        [
            Paragraph("<b>Total Registros de Pañol en SAP</b>", table_cell_bold),
            Paragraph(f"{total_panol:,}", table_cell_center),
            Paragraph("100,0%", table_cell_center),
            Paragraph("Base Total Identificada", table_cell_style)
        ],
        [
            Paragraph("<b>Materiales Ya Clasificados (Completos)</b>", table_cell_bold),
            Paragraph(f"{completos_panol:,}", table_cell_center),
            Paragraph(f"{pct_completos:.1f}%", table_cell_center),
            Paragraph("<font color='#10B981'><b>Conformes en SAP</b></font>", table_cell_style)
        ],
        [
            Paragraph("<b>Materiales Pendientes por Clasificar</b>", table_cell_bold),
            Paragraph(f"{incompletos_panol:,}", table_cell_center),
            Paragraph(f"{pct_incompletos:.1f}%", table_cell_center),
            Paragraph("<font color='#EF4444'><b>Objetivo Inmediato del Plan</b></font>", table_cell_style)
        ]
    ]
    t_kpi = Table(kpi_table_data, colWidths=[180, 100, 90, 134])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F4E78")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 14))

    # --- SECCIÓN 3: DESGLOSE DETALLADO DE GRUPOS DE PAÑOL ---
    story.append(Paragraph("3. Desglose Numérico por Grupos de PAÑOL", h1_style))
    story.append(Paragraph(
        "A continuación se presenta el desglose exacto de los <b>6 grupos de materiales de Pañol</b> almacenados en SAP ERP, "
        "ordenados por el nivel de prioridad y volumen de registros pendientes por completar:",
        body_style
    ))

    groups_data = panol_qs.values('nombre_grupo').annotate(
        total=Count('id'),
        pending=Count('id', filter=Q(is_incomplete=True)),
        sin_clase=Count('id', filter=Q(clase__isnull=True)|Q(clase='')),
        sin_familia=Count('id', filter=Q(familia__isnull=True)|Q(familia='')),
        sin_subfam=Count('id', filter=Q(subfamilia__isnull=True)|Q(subfamilia='')),
        sin_cat=Count('id', filter=Q(categoria__isnull=True)|Q(categoria=''))
    ).order_by('-pending')

    panol_table_rows = [
        [
            Paragraph("<b>Grupo SAP Pañol</b>", table_header_style),
            Paragraph("<b>Total SKUs</b>", table_header_style),
            Paragraph("<b>Pendientes</b>", table_header_style),
            Paragraph("<b>Sin Familia</b>", table_header_style),
            Paragraph("<b>Sin Marca</b>", table_header_style),
            Paragraph("<b>Sin Categoría</b>", table_header_style)
        ]
    ]

    for g in groups_data:
        panol_table_rows.append([
            Paragraph(f"<b>{g['nombre_grupo']}</b>", table_cell_bold),
            Paragraph(f"{g['total']:,}", table_cell_center),
            Paragraph(f"<b><font color='#EF4444'>{g['pending']:,}</font></b>", table_cell_center),
            Paragraph(f"{g['sin_familia']:,}", table_cell_center),
            Paragraph(f"{g['sin_subfam']:,}", table_cell_center),
            Paragraph(f"{g['sin_cat']:,}", table_cell_center)
        ])

    # Fila de Totales
    panol_table_rows.append([
        Paragraph("<b>TOTALES PAÑOL</b>", table_cell_bold),
        Paragraph(f"<b>{total_panol:,}</b>", table_cell_center),
        Paragraph(f"<b><font color='#EF4444'>{incompletos_panol:,}</font></b>", table_cell_center),
        Paragraph(f"<b>{sum(g['sin_familia'] for g in groups_data):,}</b>", table_cell_center),
        Paragraph(f"<b>{sum(g['sin_subfam'] for g in groups_data):,}</b>", table_cell_center),
        Paragraph(f"<b>{sum(g['sin_cat'] for g in groups_data):,}</b>", table_cell_center)
    ])

    t_panol_groups = Table(panol_table_rows, colWidths=[150, 70, 74, 70, 70, 70])
    t_panol_groups.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor("#F8FAFC")]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_panol_groups)
    story.append(Spacer(1, 14))

    # --- SECCIÓN 4: METODOLOGÍA DE TRABAJO ---
    story.append(Paragraph("4. Metodología de Clasificación Inteligente y Supervisada", h1_style))
    story.append(Paragraph(
        "Para garantizar una velocidad de avance sin precedentes y al mismo tiempo <b>cero margen de error</b> en SAP, "
        "hemos estructurado la metodología en 3 pilares clave:",
        body_style
    ))

    methodology_text = (
        "<b>1. Algoritmo de IA Asistida (Gemini) con Catálogo Cerrado SAP:</b><br/>"
        "La Inteligencia Artificial no inventa categorías ni familias. Se le ha restringido estrictamente a seleccionar "
        "únicamente opciones dentro de la lista oficial de SAP de PESCO S.A. (28 Clases y 124 Familias homologadas).<br/><br/>"
        "<b>2. Plataforma Web Dashboard de Gestión y Edición Manual:</b><br/>"
        "Disponemos de un centro de control visual en tiempo real donde el equipo puede auditar cada sugerencia de la IA o realizar "
        "modificaciones manuales directas mediante ventanas de edición interactivas.<br/><br/>"
        "<b>3. Emisión de Informes de Actualización para TI:</b><br/>"
        "Una vez completado y verificado un grupo de materiales, el sistema genera automáticamente un archivo Excel "
        "con el formato estándar listo para que el equipo de TI realice la carga y modificación masiva directa en SAP ERP."
    )
    story.append(Paragraph(methodology_text, body_style))
    story.append(Spacer(1, 14))

    # --- SECCIÓN 5: PLAN DE ACCIÓN Y HOJA DE RUTA ---
    story.append(Paragraph("5. Plan de Acción Ejecución Gradual (Roadmap Pañol)", h1_style))
    story.append(Paragraph(
        "Procesar los 928 materiales de Pañol en un solo bloque masivo no es aconsejable debido al riesgo de saturation de sistemas. "
        "En su lugar, proponemos una <b>ejecución gradual por fases priorizadas</b> con revisiones de calidad:",
        body_style
    ))

    roadmap_data = [
        [Paragraph("<b>Fase del Plan</b>", table_header_style), Paragraph("<b>Grupos de Pañol Incluidos</b>", table_header_style), Paragraph("<b>Cant. SKUs</b>", table_header_style), Paragraph("<b>Plazo Estimado</b>", table_header_style), Paragraph("<b>Entregable</b>", table_header_style)],
        [
            Paragraph("<b>Fase 1: Piloto Rápido</b>", table_cell_bold),
            Paragraph("• Pañol Herramientas (78)<br/>• Pañol EPP (46)<br/>• Pañol Izaje (20)", table_cell_style),
            Paragraph("<b>144 SKUs</b>", table_cell_center),
            Paragraph("<b>48 Horas</b>", table_cell_center),
            Paragraph("Excel Carga SAP 1 + Informe de Auditoría", table_cell_style)
        ],
        [
            Paragraph("<b>Fase 2: Insumos Variables</b>", table_cell_bold),
            Paragraph("• Pañol Ins. Variables (253)", table_cell_style),
            Paragraph("<b>253 SKUs</b>", table_cell_center),
            Paragraph("<b>3 Días</b>", table_cell_center),
            Paragraph("Excel Carga SAP 2", table_cell_style)
        ],
        [
            Paragraph("<b>Fase 3: Materiales Masivos</b>", table_cell_bold),
            Paragraph("• Pañol Mat. e Insumos (530)", table_cell_style),
            Paragraph("<b>531 SKUs</b>", table_cell_center),
            Paragraph("<b>5 Días</b>", table_cell_center),
            Paragraph("Excel Carga SAP 3 (Cierre Pañol)", table_cell_style)
        ],
    ]
    t_roadmap = Table(roadmap_data, colWidths=[105, 155, 65, 75, 104])
    t_roadmap.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F4E78")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_roadmap)
    story.append(Spacer(1, 16))

    # --- FIRMA / CONCLUSIÓN ---
    conclusion_text = (
        "<b>Conclusión:</b> Al aprobar este plan gradual comenzando por la <b>Fase 1 de Pañol</b>, en menos de 48 horas "
        "contaremos con el primer entregable oficial verificado para que el equipo de TI actualice masivamente el maestro en SAP, "
        "estableciendo un estándar de orden y control operacional para toda la empresa."
    )
    story.append(Paragraph(conclusion_text, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generado exitosamente: {pdf_filename}")

if __name__ == "__main__":
    build_pdf()
