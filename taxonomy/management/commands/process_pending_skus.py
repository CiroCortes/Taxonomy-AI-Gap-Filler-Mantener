import os
import time
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from taxonomy.models import SKUItem
from ai_engine.gap_classifier import GeminiGapClassifier

load_dotenv()


class Command(BaseCommand):
    help = "Procesa únicamente los SKUs que tienen atributos incompletos mediante el motor de IA Gemini + RAG."

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, required=False, default=None, help="Clave de la API de Google Gemini.")
        parser.add_argument('--limit', type=int, default=500, help="Límite máximo de SKUs a procesar en esta tanda.")

    def handle(self, *args, **options):
        api_key = options.get('api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.stderr.write("Error: Se requiere una API Key de Gemini. Proporciónala vía --api-key o variable de entorno GEMINI_API_KEY.")
            return

        classifier = GeminiGapClassifier(api_key=api_key)
        incomplete_skus = SKUItem.objects.filter(is_incomplete=True)[:options['limit']]
        
        total_pending = len(incomplete_skus)
        if total_pending == 0:
            self.stdout.write(self.style.SUCCESS("No hay SKUs pendientes de clasificación."))
            return

        self.stdout.write(f"Procesando {total_pending} SKUs pendientes con el motor Gemini...")

        processed_ok = 0
        errors = 0

        for sku in incomplete_skus:
            # RAG Local: Recuperar hasta 3 ejemplos de SKUs ya completos pertenecientes al mismo grupo
            rag_matches = list(SKUItem.objects.filter(
                is_incomplete=False,
                nombre_grupo=sku.nombre_grupo
            ).values('item_name', 'familia', 'subfamilia')[:3])

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
                    rag_matches
                )

                if "clase" in sku.pending_fields and result.clase:
                    sku.clase = result.clase
                if "familia" in sku.pending_fields and result.familia:
                    sku.familia = result.familia
                if "subfamilia" in sku.pending_fields and result.subfamilia:
                    sku.subfamilia = result.subfamilia
                if "categoria" in sku.pending_fields and result.categoria:
                    sku.categoria = result.categoria

                sku.ai_confidence_score = result.confidence
                sku.ai_rationale = result.rationale
                sku.check_incomplete()
                sku.save()

                processed_ok += 1
                self.stdout.write(f"[OK] SKU {sku.item_code} | Confianza: {result.confidence:.2f} | Razonamiento: {result.rationale}")

            except Exception as e:
                errors += 1
                self.stderr.write(f"[ERROR] SKU {sku.item_code}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(
            f"\nEjecución finalizada:\n"
            f"- Procesados exitosamente: {processed_ok}\n"
            f"- Errores: {errors}"
        ))
