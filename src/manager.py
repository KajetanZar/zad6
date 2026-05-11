from src.models import Apartment, Bill, Parameters, Tenant, TenantSettlement, Transfer, ApartmentSettlement
from typing import List, Tuple

class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters 

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
       
        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment_costs(self, apartment_key: str, year: int = None, month: int = None) -> float | None:
        if month is not None and (month < 1 or month > 12):
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = 0.0
        for bill in self.bills:
            if bill.apartment == apartment_key and (year is None or bill.settlement_year == year) and (month is None or bill.settlement_month == month):
                total_cost += bill.amount_pln
        return total_cost

    def get_settlement(self, apartment_key: str, year: int, month: int) -> ApartmentSettlement | None:
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_key not in self.apartments:
            return None
        total_cost = self.get_apartment_costs(apartment_key, year, month)
        if total_cost is None:
            return None
        
        return ApartmentSettlement(
            key=f"{apartment_key}-{year}-{month}",
            apartment=apartment_key,
            year=year,
            month=month,
            total_due_pln=total_cost
        )
    
    def create_tenants_settlements(self, apartment_settlement: ApartmentSettlement) -> List[TenantSettlement] | None:
        if apartment_settlement.month < 1 or apartment_settlement.month > 12:
            raise ValueError("Month must be between 1 and 12")
        if apartment_settlement.apartment not in self.apartments:
            return None
        tenants_in_apartment = [tenant for tenant in self.tenants.values() if tenant.apartment == apartment_settlement.apartment]
        if not tenants_in_apartment:
            return []
        
        return [
            TenantSettlement(
                tenant=tenant.name,
                apartment_settlement=apartment_settlement.key,
                month=apartment_settlement.month,
                year=apartment_settlement.year,
                total_due_pln=apartment_settlement.total_due_pln / len(tenants_in_apartment)
            )
        for tenant in tenants_in_apartment ] 

    def _get_monthly_tenant_balances(self, year: int, month: int) -> List[TenantSettlement]:
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")

        przelewy_po_najemcy = {}
        for przelew in self.transfers:
            if przelew.settlement_year == year and przelew.settlement_month == month:
                przelewy_po_najemcy[przelew.tenant] = przelewy_po_najemcy.get(przelew.tenant, 0.0) + przelew.amount_pln

        najemcy_po_mieszkaniu = {}
        for tenant in self.tenants.values():
            najemcy_po_mieszkaniu.setdefault(tenant.apartment, []).append(tenant)

        saldo_najemcow: List[TenantSettlement] = []
        for tenant_key, tenant in self.tenants.items():
            suma_kosztow = self.get_apartment_costs(tenant.apartment, year, month) or 0.0
            najemcy_w_mieszkaniu = najemcy_po_mieszkaniu.get(tenant.apartment, [])
            udzial_kosztow = suma_kosztow / len(najemcy_w_mieszkaniu) if najemcy_w_mieszkaniu else 0.0
            kwota_do_zaplaty = tenant.rent_pln + udzial_kosztow
            suma_przelewow = przelewy_po_najemcy.get(tenant_key, 0.0)
            saldo_pln = kwota_do_zaplaty - suma_przelewow

            saldo_najemcow.append(
                TenantSettlement(
                    tenant=tenant.name,
                    apartment_settlement=f"{tenant.apartment}-{year}-{month}",
                    month=month,
                    year=year,
                    total_due_pln=kwota_do_zaplaty,
                    total_transfers_pln=suma_przelewow,
                    balance_pln=saldo_pln
                )
            )

        return saldo_najemcow

    def get_debtors_for_month(self, year: int, month: int) -> List[TenantSettlement]:
        monthly_balances = self._get_monthly_tenant_balances(year, month)
        return [balance for balance in monthly_balances if balance.balance_pln > 0]

    def get_annual_financial_summary(self, year: int) -> dict[str, float]:
        suma_rachunkow = sum(rachunek.amount_pln for rachunek in self.bills if rachunek.settlement_year == year)
        suma_przelewow = sum(przelew.amount_pln for przelew in self.transfers if przelew.settlement_year == year)

        return {
            "year": year,
            "total_bills_pln": suma_rachunkow,
            "total_transfers_pln": suma_przelewow,
            "balance_pln": suma_przelewow - suma_rachunkow
        }
    
    def get_tax(self, year: int, month: int, tax_rate: float) -> int:
        if month < 1 or month > 12:
            raise ValueError("Miesiac musi byc w przedziale 1 a 12")
        if tax_rate < 0 or tax_rate > 1:
            raise ValueError("musi byc pomiedzy 0 a 1")
        
        total_revenue = sum(transfer.amount_pln for transfer in self.transfers if transfer.settlement_year == year and transfer.settlement_month == month)
        tax_amount = total_revenue * tax_rate
        return int(tax_amount + 0.5)
