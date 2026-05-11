import pytest
from src.manager import Manager
from src.models import Parameters 
def test_apartment_bill_and_tenant_shares_match(): 
    manager = Manager(Parameters()) 
    apartment_key = 'apart-polanka' 
    year = 2025 
    month = 1 
    apartment_total = manager.get_apartment_costs(apartment_key, year, month) 
    assert apartment_total == 910.0 
    apartment_settlement = manager.get_settlement(apartment_key, year, month) 
    assert apartment_settlement is not None 
    assert apartment_settlement.total_due_pln == apartment_total 
    tenant_settlements = manager.create_tenants_settlements(apartment_settlement) 
    assert isinstance(tenant_settlements, list) 
    assert len(tenant_settlements) == 3 
    tenant_total = sum(ts.total_due_pln for ts in tenant_settlements) 
    
    assert tenant_total == pytest.approx(apartment_total) 
    assert all(ts.total_due_pln == apartment_total / len(tenant_settlements) for ts in tenant_settlements)
