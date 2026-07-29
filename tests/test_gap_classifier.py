import pytest
from taxonomy.models import SKUItem


@pytest.mark.django_db
def test_incomplete_flag_behavior():
    sku = SKUItem.objects.create(
        item_code="PESCO-001",
        item_name="FILTRO DE ACEITE ROSENBAUER",
        clase="Repuestos",
        familia=None,
        subfamilia="ROSENBAUER"
    )
    sku.check_incomplete()
    assert sku.is_incomplete is True
    assert "familia" in sku.pending_fields
    assert "clase" not in sku.pending_fields
    assert "categoria" in sku.pending_fields


@pytest.mark.django_db
def test_complete_sku_behavior():
    sku = SKUItem.objects.create(
        item_code="PESCO-002",
        item_name="CAMION RECOLECTOR HEIL",
        clase="Equipos",
        familia="Recolectores",
        subfamilia="HEIL",
        categoria="Operaciones"
    )
    sku.check_incomplete()
    assert sku.is_incomplete is False
    assert len(sku.pending_fields) == 0
