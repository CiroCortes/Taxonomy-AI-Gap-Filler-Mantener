import json
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DynamicTaxonomyFill(BaseModel):
    clase: Optional[str] = Field(None, description="Clase asignada elegida strictly del catálogo oficial de SAP PESCO")
    familia: Optional[str] = Field(None, description="Familia asignada elegida estrictamente del catálogo oficial de SAP PESCO")
    subfamilia: Optional[str] = Field(None, description="Subfamilia/Marca asignada")
    categoria: Optional[str] = Field(None, description="Categoría operacional")
    confidence: float = Field(..., description="Nivel de certeza de 0.0 a 1.0")
    rationale: str = Field(..., description="Explicación técnica del resultado")


class GeminiGapClassifier:
    def __init__(self, api_key: str):
        self.api_key = api_key
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key

        self.use_google_genai = False
        self.use_google_generativeai = False

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
        rag_context: List[Dict[str, Any]],
        allowed_clases: Optional[List[str]] = None,
        allowed_familias: Optional[List[str]] = None
    ) -> DynamicTaxonomyFill:
        examples_str = "\n".join([
            f"- Similar: {item.get('item_name', '')} -> Clase: {item.get('clase', '')}, Familia: {item.get('familia', '')}, SubFamilia: {item.get('subfamilia', '')}"
            for item in rag_context
        ]) if rag_context else "Ninguno disponible."

        schema_repr = (
            DynamicTaxonomyFill.model_json_schema()
            if hasattr(DynamicTaxonomyFill, 'model_json_schema')
            else DynamicTaxonomyFill.schema_json()
        )

        clases_str = json.dumps(allowed_clases, ensure_ascii=False) if allowed_clases else "Cualquiera adecuada"
        familias_str = json.dumps(allowed_familias, ensure_ascii=False) if allowed_familias else "Cualquiera adecuada"

        prompt = f'''
Eres un especialista estricto en catalogación de repuestos y equipos para PESCO S.A.
Rellena EXCLUSIVAMENTE los campos faltantes: {missing_fields}

REGLAS DE ORO ANTI-ALUCINACIÓN (ESTRICTO SAP ERP PESCO):
1. Para el campo 'clase', DEBES seleccionar EXCLUSIVAMENTE un valor contenido dentro de esta lista oficial de SAP:
{clases_str}
NO INVENTES NINGUNA CLASE QUE NO ESTÉ EN ESTA LISTA.

2. Para el campo 'familia', DEBES seleccionar EXCLUSIVAMENTE un valor contenido dentro de esta lista oficial de SAP:
{familias_str}
NO INVENTES NINGUNA FAMILIA QUE NO ESTÉ EN ESTA LISTA. (Por ejemplo: NUNCA uses 'Químicos' si no pertenece a la lista).

3. Si no encuentras una coincidencia oficial válida en las listas con alta certeza, no asignes valores inventados.

DATOS DEL ARTÍCULO:
- SKU / Descripción: {item_name}
- Grupo SAP: {grupo}
- Datos Actuales: {json.dumps(current_data, ensure_ascii=False)}

EJEMPLOS DE CATALOGACIÓN REAL PESCO (RAG):
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
            # Fallback to legacy model if google.genai model fails
            try:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=self.api_key)
                m = genai_legacy.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json", "temperature": 0.0}
                )
                res = m.generate_content(prompt)
                return DynamicTaxonomyFill.model_validate_json(res.text)
            except Exception as ex:
                raise RuntimeError(f"No se pudo obtener respuesta de ningún modelo Gemini disponible: {str(ex)}")
        elif self.use_google_generativeai:
            response = self.legacy_model.generate_content(prompt)
            return DynamicTaxonomyFill.model_validate_json(response.text)
        else:
            raise RuntimeError("Motor de IA no inicializado.")
