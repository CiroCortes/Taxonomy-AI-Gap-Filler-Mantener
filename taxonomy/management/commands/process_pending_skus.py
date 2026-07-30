import os
import time
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from django.utils import timezone
from taxonomy.models import SKUItem
from ai_engine.gap_classifier import GeminiGapClassifier

load_dotenv()


class Command(BaseCommand):
    help = "Procesa los SKUs pendientes por atributos incompletos filtrados opcionalmente por Grupo SAP."

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, required=False, default=None, help="Clave de la API de Google Gemini.")
        parser.add_argument('--limit', type=int, default=500, help="Límite máximo de SKUs a procesar en esta tanda.")
        parser.add_argument('--grupo', type=str, default=None, help="Filtrar por nombre exacto del Grupo SAP (ej: 'PAÑOL EPP').")
        parser.add_argument('--grupo-contains', type=str, default=None, help="Filtrar por coincidencia parcial en el Grupo SAP (ej: 'PAÑOL').")
        parser.add_argument('--delay', type=float, default=0.5, help="Pausa en segundos entre consultas a la API de Gemini.")

    def handle(self, *args, **options):
        api_key = options.get('api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.stderr.write("Error: Se requiere una API Key de Gemini. Proporciónala vía --api-key o variable de entorno GEMINI_API_KEY.")
            return

        classifier = GeminiGapClassifier(api_key=api_key)
        
        incomplete_qs = SKUItem.objects.filter(is_incomplete=True)

        grupo_exact = options.get('grupo')
        grupo_contains = options.get('grupo_contains')

        if grupo_exact:
            incomplete_qs = incomplete_qs.filter(nombre_grupo=grupo_exact.strip())
            self.stdout.write(f"Filtrando por Grupo exacto: '{grupo_exact}'")
        elif grupo_contains:
            incomplete_qs = incomplete_qs.filter(nombre_grupo__icontains=grupo_contains.strip())
            self.stdout.write(f"Filtrando por Grupos que contienen: '{grupo_contains}'")

        incomplete_skus = list(incomplete_qs.order_by('item_code')[:options['limit']])
        
        total_pending = len(incomplete_skus)
        if total_pending == 0:
            self.stdout.write(self.style.SUCCESS("No se encontraron SKUs pendientes que coincidan con los filtros."))
            return

        self.stdout.write(f"Procesando {total_pending} SKUs pendientes con el motor Gemini...")

        # Obtener listas oficiales de Clases y Familias existentes en SAP ERP
        allowed_clases = list(SKUItem.objects.exclude(clase__isnull=True).exclude(clase='').values_list('clase', flat=True).distinct())
        allowed_familias = list(SKUItem.objects.exclude(familia__isnull=True).exclude(familia='').values_list('familia', flat=True).distinct())

        processed_ok = 0
        errors = 0
        delay_sec = options['delay']

        for idx, sku in enumerate(incomplete_skus, start=1):
            # RAG Local: Recuperar hasta 3 ejemplos de SKUs ya completos pertenecientes al mismo grupo
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

            try:
                result = classifier.fill_missing_fields(
                    sku.item_name,
                    sku.nombre_grupo or "",
                    current_data,
                    sku.pending_fields,
                    rag_matches,
                    allowed_clases=allowed_clases,
                    allowed_familias=allowed_familias
                )

                # Validar que clase y familia pertenezcan a la lista oficial
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

                processed_ok += 1
                self.stdout.write(f"[{idx}/{total_pending}] [OK] SKU {sku.item_code} | Grupo: {sku.nombre_grupo} | Confianza: {result.confidence:.2f} | Razonamiento: {result.rationale}")

            except Exception as e:
                errors += 1
                self.stderr.write(f"[{idx}/{total_pending}] [ERROR] SKU {sku.item_code}: {str(e)}")

            if delay_sec > 0 and idx < total_pending:
                time.sleep(delay_sec)

        self.stdout.write(self.style.SUCCESS(
            f"\nEjecución finalizada:\n"
            f"- Procesados exitosamente: {processed_ok}\n"
            f"- Errores: {errors}"
        ))
