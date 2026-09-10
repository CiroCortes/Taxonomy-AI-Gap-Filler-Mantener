from django.db import models

class SKUItem(models.Model):
    item_code = models.CharField(max_length=50, unique=True, db_index=True)
    item_name = models.TextField()
    stock = models.FloatField(default=0.0)
    costo_un = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    costo_tt = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    moneda = models.CharField(max_length=10, null=True, blank=True)
    precio_lista = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    # Atributos Taxonómicos
    cod_grupo = models.CharField(max_length=50, null=True, blank=True)
    nombre_grupo = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    clase = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    familia = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    subfamilia = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    categoria = models.CharField(max_length=100, null=True, blank=True)

    # Auditoría e IA
    is_incomplete = models.BooleanField(default=True, db_index=True)
    pending_fields = models.JSONField(default=list)
    ai_processed = models.BooleanField(default=False, db_index=True)
    ai_processed_at = models.DateTimeField(null=True, blank=True)
    ai_confidence_score = models.FloatField(default=0.0)
    ai_rationale = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def check_incomplete(self):
        missing = []
        if not self.clase or not str(self.clase).strip():
            missing.append("clase")
        if not self.familia or not str(self.familia).strip():
            missing.append("familia")
        if not self.subfamilia or not str(self.subfamilia).strip():
            missing.append("subfamilia")
        if not self.categoria or not str(self.categoria).strip():
            missing.append("categoria")
        self.pending_fields = missing
        self.is_incomplete = len(missing) > 0
        return self.is_incomplete

    def __str__(self):
        return f"{self.item_code} - {self.item_name}"


class CodeCreationRequest(models.Model):
    """Solicitud de creación de nuevo código SAP."""
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    MONEDA_CHOICES = [
        ('CLP', 'CLP – Peso Chileno'),
        ('USD', 'USD – Dólar'),
        ('EUR', 'EUR – Euro'),
        ('BRL', 'BRL – Real Brasileño'),
    ]
    INCOTERM_CHOICES = [
        ('EXW', 'EXW – Ex Works'),
        ('FOB', 'FOB – Free on Board'),
        ('CIF', 'CIF – Cost, Insurance & Freight'),
        ('DDP', 'DDP – Delivered Duty Paid'),
        ('DAP', 'DAP – Delivered at Place'),
        ('NA',  'N/A – No aplica'),
    ]

    base_sku = models.ForeignKey(
        SKUItem, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='creation_requests', help_text="Código SAP de referencia para duplicar."
    )
    generated_code = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Código correlativo sugerido por el sistema."
    )
    solicitante_nombre = models.CharField(max_length=150, help_text="Nombre real o área del solicitante.")
    grupo_material = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Grupo de materiales / área de donde proviene la solicitud (ej: EQUIPOS EPP)."
    )
    proposed_description = models.TextField(help_text="Descripción del nuevo ítem (mejorada con IA).")
    justification = models.TextField(help_text="Motivo de la creación del nuevo código.")

    # ── Datos del Proveedor ────────────────────────────────────────────────────
    proveedor_nombre = models.CharField(max_length=200, blank=True, null=True, help_text="Nombre del proveedor.")
    codigo_catalogo_proveedor = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Código del artículo en el catálogo del proveedor (ej: CSE4P-015)."
    )
    es_importado = models.BooleanField(default=False, help_text="¿El artículo es importado / internacional?")
    moneda_precio = models.CharField(max_length=5, choices=MONEDA_CHOICES, default='CLP', blank=True)
    precio_referencial = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Precio referencial unitario."
    )
    lote_minimo = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Lote mínimo de compra (cantidad mínima que acepta el proveedor)."
    )
    unidad_empaque = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Unidad/medida de empaque (ej: Caja x 12, UN, KG, MT)."
    )
    incoterm = models.CharField(max_length=5, choices=INCOTERM_CHOICES, default='NA', blank=True)

    # ── Ficha Técnica ─────────────────────────────────────────────────────────
    ficha_tecnica = models.TextField(
        blank=True, null=True,
        help_text="Especificaciones técnicas del artículo (texto libre)."
    )
    ficha_tecnica_archivo = models.FileField(
        upload_to='fichas_tecnicas/%Y/%m/',
        blank=True, null=True,
        help_text="Adjunto de ficha técnica (PDF, JPG, PNG). Máx 20 MB."
    )

    # ── Campos de taxonomía propuestos para el nuevo SKU ─────────────────────
    clase_propuesta = models.CharField(max_length=100, blank=True, null=True)
    familia_propuesta = models.CharField(max_length=100, blank=True, null=True)
    subfamilia_propuesta = models.CharField(max_length=100, blank=True, null=True)
    categoria_propuesta = models.CharField(max_length=100, blank=True, null=True)

    lote_id = models.CharField(max_length=50, blank=True, null=True, db_index=True, help_text="ID del lote de carga masiva.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente', db_index=True)
    admin_notes = models.TextField(blank=True, null=True, help_text="Notas del administrador al aprobar/rechazar.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Solicitud de Creación de Código"
        verbose_name_plural = "Solicitudes de Creación de Códigos"

    def __str__(self):
        return f"[{self.get_status_display()}] {self.generated_code or 'S/N'} - {self.solicitante_nombre}"


class PurchaseRequest(models.Model):
    """Solicitud de compra (reemplaza el flujo de correos)."""
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    TIPO_CHOICES = [
        ('stock', 'Stock'),
        ('calzada', 'Calzada'),
    ]

    solicitante_nombre = models.CharField(max_length=150)
    proveedor = models.CharField(max_length=200, blank=True, null=True)
    codigo_compra = models.CharField(max_length=50, blank=True, null=True, help_text="Código SAP del artículo a comprar.")
    descripcion = models.TextField()
    cantidad_solicitada = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tipo_compra = models.CharField(max_length=10, choices=TIPO_CHOICES, default='stock')
    justification = models.TextField(blank=True, null=True)

    lote_id = models.CharField(max_length=50, blank=True, null=True, db_index=True, help_text="ID del lote de carga masiva.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente', db_index=True)
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Solicitud de Compra"
        verbose_name_plural = "Solicitudes de Compra"

    def __str__(self):
        return f"[{self.get_status_display()}] {self.codigo_compra or 'S/C'} - {self.descripcion[:50]}"
