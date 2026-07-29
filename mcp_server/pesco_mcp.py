import os
import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PESCO Taxonomy Auditor MCP")


@mcp.tool()
def get_pending_summary(db_path: str = "db.sqlite3") -> str:
    """Devuelve un resumen del estado de auditoría de brechas taxonómicas en la base de datos."""
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        return f"Base de datos no encontrada en: {db_path}"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT 
            SUM(CASE WHEN clase IS NULL OR clase = '' THEN 1 ELSE 0 END),
            SUM(CASE WHEN familia IS NULL OR familia = '' THEN 1 ELSE 0 END),
            SUM(CASE WHEN subfamilia IS NULL OR subfamilia = '' THEN 1 ELSE 0 END),
            COUNT(*)
        FROM taxonomy_skuitem
        ''')
        row = cursor.fetchone()
        conn.close()

        if not row or row[3] == 0:
            return "No se encontraron registros en la tabla taxonomy_skuitem."

        sin_clase = row[0] or 0
        sin_familia = row[1] or 0
        sin_subfamilia = row[2] or 0
        total = row[3] or 0

        return f"Total: {total} | Sin Clase: {sin_clase} | Sin Familia: {sin_familia} | Sin SubFamilia: {sin_subfamilia}"
    except Exception as e:
        return f"Error al consultar la base de datos: {str(e)}"


if __name__ == "__main__":
    mcp.run()
