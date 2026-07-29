import json
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DynamicTaxonomyFill(BaseModel):
    clase: Optional[str] = Field(None, description="Clase asignada si faltaba")
    familia: Optional[str] = Field(None, description="Familia asignada dentro del catálogo PESCO")
    subfamilia: Optional[str] = Field(None, description="Subfamilia/Marca asignada")
    categoria: Optional[str] = Field(None, description="Categoría operacional")
    confidence: float = Field(..., description="Nivel de certeza de 0.0 a 1.0")
    rationale: str = Field(..., description="Explicación técnica del resultado")


class GeminiGapClassifier:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.use_google_genai = False
        self.use_google_generativeai = False

        # Attempt to initialize google.genai first (new SDK), fallback to google.generativeai
        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
            self.use_google_genai = True
        except (ImportError, Exception):
            try:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=api_key)
                self.legacy_model = genai_legacy.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    generation_config={"response_mime_type": "application/json", "temperature": 0.0}
                )
                self.use_google_generativeai = True
            except Exception as e:
                raise RuntimeError(f"No se pudo inicializar la API de Gemini: {str(e)}")

    def fill_missing_fields(
        self,
        item_name: str,
        grupo: str,
        current_data: Dict[str, Any],
        missing_fields: List[str],
        rag_context: List[Dict[str, Any]]
    ) -> DynamicTaxonomyFill:
        examples_str = "\n".join([
            f"- Similar: {item.get('item_name', '')} -> Familia: {item.get('familia', '')}, SubFamilia: {item.get('subfamilia', '')}"
            for item in rag_context
        ]) if rag_context else "Ninguno disponible."

        schema_repr = (
            DynamicTaxonomyFill.model_json_schema()
            if hasattr(DynamicTaxonomyFill, 'model_json_schema')
            else DynamicTaxonomyFill.schema_json()
        )

        prompt = f'''
Eres un especialista en catalogación de maquinaria pesada y repuestos para PESCO S.A.
Rellena EXCLUSIVAMENTE los campos faltantes: {missing_fields}

SKU: {item_name} | Grupo: {grupo} | Datos Actuales: {json.dumps(current_data, ensure_ascii=False)}
Ejemplos RAG Reales:
{examples_str}

Responde siguiendo la estructura JSON:
{schema_repr}
'''

        if self.use_google_genai:
            for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-flash-latest']:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={
                            'response_mime_type': 'application/json',
                            'temperature': 0.0,
                        }
                    )
                    return DynamicTaxonomyFill.model_validate_json(response.text)
                except Exception:
                    continue
            raise RuntimeError("No se pudo obtener respuesta de ningún modelo Gemini disponible.")
        elif self.use_google_generativeai:
            response = self.legacy_model.generate_content(prompt)
            return DynamicTaxonomyFill.model_validate_json(response.text)
        else:
            raise RuntimeError("Motor de IA no inicializado.")
