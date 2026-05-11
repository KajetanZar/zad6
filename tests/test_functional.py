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


def test_get_monthly_debtors_report_returns_only_overdue_tenants():
    manager = Manager(Parameters())
    manager.transfers = [transfer for transfer in manager.transfers if transfer.tenant == 'tenant-1']

    debtors = manager.get_debtors_for_month(2025, 1)
    debtor_names = {debtor.tenant for debtor in debtors}

    assert debtor_names == {'Adam Kowalski', 'Ewa Adamska'}
    assert all(debtor.balance_pln > 0 for debtor in debtors)
    assert all(debtor.month == 1 and debtor.year == 2025 for debtor in debtors)


def test_get_annual_financial_summary_returns_totals_for_given_year():
    manager = Manager(Parameters())
    summary = manager.get_annual_financial_summary(2025)

    assert summary == {
        'year': 2025,
        'total_bills_pln': 910.0,
        'total_transfers_pln': 7500.0,
        'balance_pln': 6590.0
    }
