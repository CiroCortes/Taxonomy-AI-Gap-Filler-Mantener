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
    ai_confidence_score = models.FloatField(default=0.0)
    ai_rationale = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def check_incomplete(self):
        missing = []
        if not self.clase: missing.append("clase")
        if not self.familia: missing.append("familia")
        if not self.subfamilia: missing.append("subfamilia")
        if not self.categoria: missing.append("categoria")
        self.pending_fields = missing
        self.is_incomplete = len(missing) > 0
        return self.is_incomplete

    def __str__(self):
        return f"{self.item_code} - {self.item_name}"
