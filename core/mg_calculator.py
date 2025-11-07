"""
core/mg_calculator.py
MG캐피탈 전용 리스료 계산기

메리츠와 완전히 독립적인 계산 방식:
- PMT (원리금균등상환) 방식
- numpy_financial.pmt() 사용
- 감가상각과 금융비용을 분리하지 않음
"""

import numpy_financial as npf
from typing import Dict, Optional


class MGLeaseCalculator:
    """MG캐피탈 방식 리스료 계산기"""

    def calculate(
        self,
        vehicle_price: int,
        residual_rate: float,
        contract_months: int,
        annual_mileage: int,
        annual_interest_rate: float,
        down_payment_rate: float = 0.0,
        region: str = "서울",
        is_ev: bool = False,
        is_hybrid: bool = False,
        company_lease: bool = False,
        **kwargs
    ) -> Dict:
        """
        MG 방식 리스료 계산 (PMT)

        Args:
            vehicle_price: 차량가
            residual_rate: 잔존율 (0~1)
            contract_months: 계약 기간 (개월)
            annual_mileage: 연간 주행거리
            annual_interest_rate: 연 금리 (0~1, 예: 0.0515 = 5.15%)
            down_payment_rate: 선납금 비율 (0~1)
            region: 지역 (공채 계산용)
            is_ev: 전기차 여부
            is_hybrid: 하이브리드 여부
            company_lease: 법인 리스 여부

        Returns:
            Dict: 계산 결과
        """
        # 1. 취득원가 계산
        acquisition_cost_details = self._calculate_acquisition_cost(
            vehicle_price=vehicle_price,
            region=region,
            is_ev=is_ev,
            is_hybrid=is_hybrid,
            company_lease=company_lease
        )

        acquisition_cost = acquisition_cost_details["total"]
        acquisition_tax = acquisition_cost_details["acquisition_tax"]
        bond_cost = acquisition_cost_details["bond_cost"]
        registration_fee = acquisition_cost_details["registration_fee"]

        # 2. 선납금 계산
        down_payment = int(acquisition_cost * down_payment_rate)

        # 3. 금융 대상 금액
        financed_amount = acquisition_cost - down_payment

        # 4. 잔존가치 (차량가 기준, MG 방식)
        residual_value = int(vehicle_price * residual_rate)

        # 5. PMT 계산 (원리금균등상환)
        # Excel: =PMT(연금리/12, 개월수, -금융대상, 잔존가치)
        monthly_payment = -npf.pmt(
            rate=annual_interest_rate / 12,
            nper=contract_months,
            pv=financed_amount,
            fv=-residual_value
        )

        # 반올림 (MG는 백원 단위로 내림)
        monthly_payment = int(monthly_payment)
        monthly_payment = (monthly_payment // 100) * 100

        # 6. 총 납부액
        total_payment = down_payment + (monthly_payment * contract_months)

        # 7. 실차량비용 (총납부 - 잔존가치)
        net_vehicle_cost = total_payment - residual_value

        # 8. 자동차세 (연납)
        annual_car_tax = self._calculate_annual_car_tax(
            vehicle_price=vehicle_price,
            is_ev=is_ev,
            is_hybrid=is_hybrid
        )
        monthly_car_tax = int(annual_car_tax / 12)

        # 9. 결과 반환
        return {
            "monthly_payment": monthly_payment,
            "down_payment": down_payment,
            "total_payment": total_payment,
            "residual_value": residual_value,
            "net_vehicle_cost": net_vehicle_cost,
            "acquisition_cost": acquisition_cost,
            "financed_amount": financed_amount,
            "monthly_car_tax": monthly_car_tax,
            "annual_car_tax": annual_car_tax,
            "breakdown": {
                "vehicle_price": vehicle_price,
                "acquisition_tax": acquisition_tax,
                "bond_cost": bond_cost,
                "registration_fee": registration_fee,
                "down_payment_rate": down_payment_rate,
                "residual_rate": residual_rate,
                "annual_interest_rate": annual_interest_rate,
                "contract_months": contract_months,
                "annual_mileage": annual_mileage,
            }
        }

    def _calculate_acquisition_cost(
        self,
        vehicle_price: int,
        region: str,
        is_ev: bool,
        is_hybrid: bool,
        company_lease: bool
    ) -> Dict:
        """
        취득원가 계산 (MG 방식)

        Returns:
            Dict: {
                'acquisition_tax': int,
                'bond_cost': int,
                'registration_fee': int,
                'total': int
            }
        """
        # 취득세 계산
        acquisition_tax = self._calculate_acquisition_tax(
            vehicle_price, is_ev, is_hybrid, company_lease
        )

        # 공채 계산
        bond_cost = self._calculate_bond_cost(vehicle_price, region)

        # 등록비 (MG 엑셀에서는 0원)
        registration_fee = 0

        # 취득원가 = 차량가 + 취득세 + 공채 + 등록비
        total = vehicle_price + acquisition_tax + bond_cost + registration_fee

        return {
            "acquisition_tax": acquisition_tax,
            "bond_cost": bond_cost,
            "registration_fee": registration_fee,
            "total": total
        }

    def _calculate_acquisition_tax(
        self,
        vehicle_price: int,
        is_ev: bool,
        is_hybrid: bool,
        company_lease: bool
    ) -> int:
        """
        취득세 계산 (MG 방식)

        MG는 VAT 제외 가격으로 취득세 계산:
        - acquisition_tax = ROUNDDOWN((vehicle_price / 1.1) * tax_rate, -1)
        - 일반 차량: 7%
        - 전기차: 7% → 감면 (4% or 140만원 중 낮은 값)
        - 하이브리드: 5%
        """
        # VAT 제외 가격 (소비자가 / 1.1)
        price_excl_vat = vehicle_price / 1.1

        base_rate = 0.07  # 기본 7%

        if is_ev:
            # 전기차 감면
            full_tax = price_excl_vat * base_rate
            # 10원 단위 내림
            full_tax = int(full_tax // 10 * 10)

            discount_option1 = int((price_excl_vat * 0.04) // 10 * 10)
            discount_option2 = 1400000
            discount = min(discount_option1, discount_option2)
            return max(full_tax - discount, 0)

        elif is_hybrid:
            # 하이브리드 5%
            tax = price_excl_vat * 0.05
            return int(tax // 10 * 10)  # 10원 단위 내림

        else:
            # 일반 차량 7%
            tax = price_excl_vat * base_rate
            return int(tax // 10 * 10)  # 10원 단위 내림

    def _calculate_bond_cost(self, vehicle_price: int, region: str) -> int:
        """
        공채 계산 (지역별)

        MG는 공채를 포함하는 경우가 있지만, 엑셀에서는 0으로 표시됨
        기본값 0 반환
        """
        # MG 엑셀에서는 공채비용이 0
        return 0

    def _calculate_annual_car_tax(
        self,
        vehicle_price: int,
        is_ev: bool,
        is_hybrid: bool
    ) -> int:
        """
        연간 자동차세 계산 (MG 방식)

        - 전기차: 13만원 (고정)
        - 일반/하이브리드: 차량가 × 1.32% (간이 계산)
        """
        if is_ev:
            # 전기차 고정세
            return 130000
        else:
            # 일반 차량 (간이 계산)
            return int(vehicle_price * 0.0132)


def main():
    """테스트 실행"""
    print("=" * 80)
    print("MG캐피탈 계산기 테스트")
    print("=" * 80)

    calc = MGLeaseCalculator()

    # BMW X5 30d xLine (엑셀 예시)
    result = calc.calculate(
        vehicle_price=115_500_000,
        residual_rate=0.58,  # 60개월, 20,000km, 고잔가
        contract_months=60,
        annual_mileage=20000,
        annual_interest_rate=0.0515,  # 5.15%
        down_payment_rate=0.0,  # 선납 없음
        region="서울",
        is_ev=False,
        is_hybrid=False
    )

    print("\n차량: BMW X5 30d xLine")
    print(f"차량가: {result['breakdown']['vehicle_price']:,}원")
    print(f"계약조건: {result['breakdown']['contract_months']}개월 / {result['breakdown']['annual_mileage']:,}km")
    print(f"잔존율: {result['breakdown']['residual_rate']*100:.1f}%")
    print(f"금리: {result['breakdown']['annual_interest_rate']*100:.2f}%")

    print(f"\n취득원가: {result['acquisition_cost']:,}원")
    print(f"  - 차량가: {result['breakdown']['vehicle_price']:,}원")
    print(f"  - 취득세: {result['breakdown']['acquisition_tax']:,}원")
    print(f"  - 공채: {result['breakdown']['bond_cost']:,}원")
    print(f"  - 등록비: {result['breakdown']['registration_fee']:,}원")

    print(f"\n금융조건:")
    print(f"  - 선납금: {result['down_payment']:,}원")
    print(f"  - 금융대상: {result['financed_amount']:,}원")
    print(f"  - 잔존가치: {result['residual_value']:,}원")

    print(f"\n📊 계산 결과:")
    print(f"  월 리스료: {result['monthly_payment']:,}원")
    print(f"  총 납부액: {result['total_payment']:,}원")
    print(f"  실차량비용: {result['net_vehicle_cost']:,}원")
    print(f"  자동차세(월): {result['monthly_car_tax']:,}원")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
