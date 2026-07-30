# INFORME EJECUTIVO: CLASIFICACIÓN Y OPTIMIZACIÓN DEL MAESTRO DE ARTÍCULOS SAP ERP
## Fase Prioritaria de Implementación: Materiales de PAÑOL & Insumos Operacionales

**Preparado para:** Jefatura y Gerencia PESCO S.A.  
**Fecha de Emisión:** Julio 2026  
**Área de Impacto:** Operaciones, Pañol, TI y Compras  
**Estado del Proyecto:** En Fase de Despliegue Piloto  

---

## 1. ¿Qué es la Clasificación del Maestro de Artículos (Taxonomía)?

En términos sencillos de gestión empresarial, la **Clasificación de Materiales** (o taxonomía) es la **organización jerárquica y estandarizada de todos los repuestos y materiales en SAP ERP**. Consiste en asignar a cada código SKU cuatro atributos clave que definen con precisión su naturaleza:

| Atributo en SAP | Definición Sencilla | Ejemplo Práctico en PESCO |
| :--- | :--- | :--- |
| **Clase** | Tipo general al que pertenece el producto. | *Herramientas, EPP, Adhesivos, Insumos* |
| **Familia** | Subgrupo especializado dentro de la clase. | *Brocas, Filtros, Guantes de Seguridad* |
| **SubFamilia (Marca)** | Marca fabricante oficial del repuesto. | *Bosch, 3M, Caterpillar, Altec* |
| **Categoría Operacional** | Ámbito o destino de uso en la empresa. | *Gestión Pañol, Taller, Operaciones* |

> 🎯 **¿Por qué es vital para la Gerencia?**  
> Un maestro de materiales incompleto genera duplicidad de compras, repuestos "fantasmas" en bodegas y dificultad para cotizar con proveedores. Completar estos campos en SAP permite **comprar mejor, controlar inventarios y automatizar reportes financieros de costos.**

---

## 2. Diagnóstico del Maestro General vs. Enfoque Prioritario en PAÑOL

A nivel global, la base de datos de PESCO cuenta con **20.297 SKUs en SAP**, de los cuales el **60,5% (12.275 SKUs)** ya se encuentran clasificados y un **39,5% (8.022 SKUs)** presenta brechas por completar.

Conforme a las prioridades definidas por la Jefatura para avanzar de inmediato en las áreas operacionales críticas, hemos aislado y priorizado el **bloque de materiales de PAÑOL**:

| Métrica en Materiales de PAÑOL | Cantidad de SKUs | Porcentaje (%) | Estado de Gestión |
| :--- | :---: | :---: | :--- |
| **Total Registros de Pañol en SAP** | **2.493** | 100,0% | Base Total Identificada |
| **Materiales Ya Clasificados (Completos)** | **1.565** | 62,8% | Conformes en SAP ERP |
| **Materiales Pendientes por Clasificar** | **928** | 37,2% | **Objetivo Inmediato del Plan** |

---

## 3. Desglose Numérico por Grupos de PAÑOL

A continuación se presenta el desglose exacto de los **6 grupos de materiales de Pañol** almacenados en SAP ERP, ordenados por el nivel de prioridad y volumen de registros pendientes por completar:

| Grupo SAP Pañol | Total SKUs | Pendientes | Sin Familia | Sin Marca | Sin Categoría |
| :--- | :-: | :-: | :-: | :-: | :-: |
| **PAÑOL MAT. E INSUMOS** | 1.413 | **530** | 135 | 160 | 434 |
| **PAÑOL INS. VARIABLES** | 646 | **253** | 156 | 147 | 226 |
| **PAÑOL HERRAMIENTAS** | 208 | **78** | 2 | 5 | 73 |
| **PAÑOL EPP** | 181 | **46** | 5 | 5 | 43 |
| **PAÑOL IZAJE** | 44 | **20** | 8 | 8 | 14 |
| **CONSIGNACIONES PAÑOL** | 1 | **1** | 1 | 1 | 1 |
| **TOTALES PAÑOL** | **2.493** | **928** | **307** | **326** | **791** |

---

## 4. Metodología de Clasificación Inteligente y Supervisada

Para garantizar una velocidad de avance sin precedentes y al mismo tiempo **cero margen de error** en SAP, hemos estructurado la metodología en 3 pilares clave:

1. **Algoritmo de IA Asistida (Gemini) con Catálogo Cerrado SAP:**  
   La Inteligencia Artificial no inventa categorías ni familias. Se le ha restringido estrictamente a seleccionar únicamente opciones dentro de la lista oficial de SAP de PESCO S.A. (28 Clases y 124 Familias homologadas).
2. **Plataforma Web Dashboard de Gestión y Edición Manual:**  
   Disponemos de un centro de control visual en tiempo real donde el equipo puede auditar cada sugerencia de la IA o realizar modificaciones manuales directas mediante ventanas de edición interactivas.
3. **Emisión de Informes de Actualización para TI:**  
   Una vez completado y verificado un grupo de materiales, el sistema genera automáticamente un archivo Excel con el formato estándar listo para que el equipo de TI realice la carga y modificación masiva directa en SAP ERP.

---

## 5. Plan de Acción Ejecución Gradual (Roadmap Pañol)

Procesar los 928 materiales de Pañol en un solo bloque masivo no es aconsejable debido al riesgo de saturación de sistemas. En su lugar, proponemos una **ejecución gradual por fases priorizadas** con revisiones de calidad:

| Fase del Plan | Grupos de Pañol Incluidos | Cant. SKUs | Plazo Estimado | Entregable |
| :--- | :--- | :-: | :-: | :--- |
| **Fase 1: Piloto Rápido** | • Pañol Herramientas (78)<br/>• Pañol EPP (46)<br/>• Pañol Izaje (20) | **144 SKUs** | **48 Horas** | Excel Carga SAP 1 + Informe de Auditoría |
| **Fase 2: Insumos Variables** | • Pañol Ins. Variables (253) | **253 SKUs** | **3 Días** | Excel Carga SAP 2 |
| **Fase 3: Materiales Masivos** | • Pañol Mat. e Insumos (530) | **531 SKUs** | **5 Días** | Excel Carga SAP 3 (Cierre Pañol) |

---

> **Conclusión:** Al aprobar este plan gradual comenzando por la **Fase 1 de Pañol**, en menos de 48 horas contaremos con el primer entregable oficial verificado para que el equipo de TI actualice masivamente el maestro en SAP, estableciendo un estándar de orden y control operacional para toda la empresa.
