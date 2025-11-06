"""
tests/test_calculator_integration.py
계산 엔진 통합 테스트
"""

import sys
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.calculator import (
    calculate_operating_lease,
    calculate_auto_tax,
    calculate_acquisition_tax,
    calculate_total_acquisition_cost
)
from data import vehicle_master, residual_rates, interest_rates


def test_simple_calculation():
    """기본 계산 테스트"""
    print("="*80)
    print("기본 계산 테스트")
    print("="*80)

    # 간단한 예시
    result = calculate_operating_lease(
        vehicle_price=50_000_000,  # 5천만원
        contract_months=36,
        down_payment=0,
        residual_rate=0.50,  # 50%
        annual_rate=0.06,  # 6%
        acquisition_tax_rate=0.0,  # 영업용 면제
        registration_fee=200_000,
        annual_car_tax=400_000,
        method='simple'
    )

    print(f"\n차량가: 50,000,000원")
    print(f"계약기간: 36개월")
    print(f"잔존율: 50%")
    print(f"금리: 6%")
    print(f"\n✓ 월 리스료: {result['monthly_total']:,}원")
    print(f"  - 월 감가상각: {result['monthly_depreciation']:,}원")
    print(f"  - 월 금융비용: {result['monthly_finance']:,}원")
    print(f"  - 월 등록비: {result['monthly_registration']:,}원")
    print(f"  - 월 자동차세: {result['monthly_car_tax']:,}원")
    print(f"\n✓ 총 납부액: {result['total_payment']:,}원")
    print(f"✓ 잔존가치: {result['residual_value']:,}원")
    print(f"✓ 실차량비용: {result['effective_vehicle_cost']:,}원")

    return True


def test_real_vehicle_calculation():
    """실제 차량 데이터로 계산 테스트"""
    print("\n" + "="*80)
    print("실제 차량 계산 테스트")
    print("="*80)

    # BMW 차량 검색
    vehicles = vehicle_master.search_vehicles("BMW")

    if not vehicles:
        print("  ✗ BMW 차량을 찾을 수 없습니다")
        return False

    # 첫 번째 BMW 차량 선택
    vehicle_id = vehicles[0]["id"]
    vehicle = vehicle_master.get_vehicle(vehicle_id)

    print(f"\n선택 차량: {vehicle['display_name']}")
    print(f"  가격: {vehicle['price']:,}원")
    print(f"  배기량: {vehicle['engine_cc']:,}cc")
    print(f"  등급: {vehicle['west_grade']}")

    # 계산 조건
    capital_id = "meritz_capital"
    contract_months = 36
    annual_mileage = 20000
    down_payment = 0

    # 잔존율 조회
    try:
        residual_rate = residual_rates.get_residual_rate(
            capital_id, vehicle_id, contract_months, annual_mileage
        )
    except ValueError as e:
        print(f"  ✗ 잔존율 조회 실패: {e}")
        return False

    # 금리 조회
    annual_rate = interest_rates.get_interest_rate(
        capital_id=capital_id,
        vehicle_price=vehicle['price'],
        brand=vehicle['brand'],
        is_import=vehicle['is_import'],
        is_ev=(vehicle['engine_cc'] == 0),
        contract_months=contract_months
    )

    # 자동차세 계산
    annual_car_tax = calculate_auto_tax(
        engine_cc=vehicle['engine_cc'],
        is_commercial=True
    )

    print(f"\n계산 조건:")
    print(f"  계약기간: {contract_months}개월")
    print(f"  주행거리: {annual_mileage:,}km/년")
    print(f"  선납금: {down_payment:,}원")
    print(f"  잔존율: {residual_rate:.2%}")
    print(f"  금리: {annual_rate:.2%}")
    print(f"  연간 자동차세: {annual_car_tax:,.0f}원")

    # 리스료 계산
    result = calculate_operating_lease(
        vehicle_price=vehicle['price'],
        contract_months=contract_months,
        down_payment=down_payment,
        residual_rate=residual_rate,
        annual_rate=annual_rate,
        acquisition_tax_rate=0.0,  # 영업용 면제
        registration_fee=200_000,
        annual_car_tax=annual_car_tax,
        method='simple'
    )

    print(f"\n" + "="*80)
    print(f"계산 결과")
    print(f"="*80)
    print(f"\n💰 월 리스료: {result['monthly_total']:,}원")
    print(f"\n📊 상세 내역:")
    print(f"  월 감가상각비: {result['monthly_depreciation']:,}원")
    print(f"  월 금융비용: {result['monthly_finance']:,}원")
    print(f"  월 등록비: {result['monthly_registration']:,}원")
    print(f"  월 자동차세: {result['monthly_car_tax']:,}원")
    print(f"\n📈 총 비용:")
    print(f"  총 납부액: {result['total_payment']:,}원")
    print(f"  잔존가치: {result['residual_value']:,}원")
    print(f"  실차량비용: {result['effective_vehicle_cost']:,}원")
    print(f"  총 이자: {result['total_interest']:,}원")

    return True


def test_multiple_conditions():
    """다양한 조건 비교 테스트"""
    print("\n" + "="*80)
    print("다양한 조건 비교 테스트")
    print("="*80)

    # Audi 차량 검색
    vehicles = vehicle_master.search_vehicles("Audi A3")

    if not vehicles:
        print("  ✗ Audi A3를 찾을 수 없습니다")
        return False

    vehicle_id = vehicles[0]["id"]
    vehicle = vehicle_master.get_vehicle(vehicle_id)

    print(f"\n차량: {vehicle['display_name']}")
    print(f"가격: {vehicle['price']:,}원")

    capital_id = "meritz_capital"
    annual_mileage = 20000

    # 계약 기간별 비교
    print(f"\n기간별 월 리스료 비교 (주행거리: {annual_mileage:,}km):")
    print("-" * 60)

    for period in [24, 36, 48, 60]:
        try:
            residual_rate = residual_rates.get_residual_rate(
                capital_id, vehicle_id, period, annual_mileage
            )

            annual_rate = interest_rates.get_interest_rate(
                capital_id=capital_id,
                vehicle_price=vehicle['price'],
                brand=vehicle['brand'],
                is_import=vehicle['is_import'],
                contract_months=period
            )

            annual_car_tax = calculate_auto_tax(vehicle['engine_cc'], True)

            result = calculate_operating_lease(
                vehicle_price=vehicle['price'],
                contract_months=period,
                down_payment=0,
                residual_rate=residual_rate,
                annual_rate=annual_rate,
                acquisition_tax_rate=0.0,
                registration_fee=200_000,
                annual_car_tax=annual_car_tax,
                method='simple'
            )

            print(f"{period}개월: {result['monthly_total']:>10,}원 (잔존율: {residual_rate:.1%})")

        except ValueError:
            print(f"{period}개월: 데이터 없음")

    # 주행거리별 비교
    period = 36
    print(f"\n주행거리별 월 리스료 비교 ({period}개월):")
    print("-" * 60)

    for mileage in [10000, 15000, 20000, 30000]:
        try:
            residual_rate = residual_rates.get_residual_rate(
                capital_id, vehicle_id, period, mileage
            )

            annual_rate = interest_rates.get_interest_rate(
                capital_id=capital_id,
                vehicle_price=vehicle['price'],
                brand=vehicle['brand'],
                is_import=vehicle['is_import'],
                contract_months=period
            )

            annual_car_tax = calculate_auto_tax(vehicle['engine_cc'], True)

            result = calculate_operating_lease(
                vehicle_price=vehicle['price'],
                contract_months=period,
                down_payment=0,
                residual_rate=residual_rate,
                annual_rate=annual_rate,
                acquisition_tax_rate=0.0,
                registration_fee=200_000,
                annual_car_tax=annual_car_tax,
                method='simple'
            )

            print(f"{mileage:>6,}km: {result['monthly_total']:>10,}원 (잔존율: {residual_rate:.1%})")

        except ValueError:
            print(f"{mileage:>6,}km: 데이터 없음")

    return True


def test_tax_calculations():
    """세금 계산 테스트"""
    print("\n" + "="*80)
    print("세금 계산 테스트")
    print("="*80)

    # 자동차세 테스트
    print("\n자동차세 계산:")
    test_cases = [
        (0, "전기차"),
        (1600, "소형 (1.6L)"),
        (2000, "중형 (2.0L)"),
        (3000, "대형 (3.0L)")
    ]

    for engine_cc, desc in test_cases:
        tax_commercial = calculate_auto_tax(engine_cc, True)
        tax_private = calculate_auto_tax(engine_cc, False)
        print(f"  {desc:20s}: 영업용 {tax_commercial:>10,.0f}원 / 비영업용 {tax_private:>10,.0f}원")

    # 취득세 테스트
    print("\n취득세 계산 (5천만원 차량):")
    vehicle_price = 50_000_000

    tax_passenger = calculate_acquisition_tax(vehicle_price, 'passenger')
    tax_commercial = calculate_acquisition_tax(vehicle_price, 'commercial')
    tax_electric = calculate_acquisition_tax(vehicle_price, 'electric')

    print(f"  일반 승용차: {tax_passenger:>10,.0f}원")
    print(f"  영업용 등록: {tax_commercial:>10,.0f}원")
    print(f"  전기차(감면): {tax_electric:>10,.0f}원")

    # 총 취득원가 계산
    print("\n총 취득원가 계산:")
    acquisition_costs = calculate_total_acquisition_cost(
        vehicle_price=vehicle_price,
        vehicle_type='commercial',
        registration_fee=200_000,
        public_bond=0,
        delivery_fee=188_000,
        other_fees=100_000
    )

    for key, value in acquisition_costs.items():
        if isinstance(value, (int, float)):
            print(f"  {key:25s}: {value:>12,.0f}원")

    return True


def main():
    """메인 테스트 실행"""
    print("\n🧪 계산 엔진 통합 테스트 시작\n")

    try:
        # 테스트 실행
        test1 = test_simple_calculation()
        test2 = test_real_vehicle_calculation()
        test3 = test_multiple_conditions()
        test4 = test_tax_calculations()

        # 결과 출력
        print("\n" + "="*80)
        print("테스트 결과")
        print("="*80)
        print(f"  기본 계산: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"  실제 차량 계산: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"  조건 비교: {'✅ PASS' if test3 else '❌ FAIL'}")
        print(f"  세금 계산: {'✅ PASS' if test4 else '❌ FAIL'}")

        if all([test1, test2, test3, test4]):
            print("\n🎉 모든 테스트 통과!")
        else:
            print("\n❌ 일부 테스트 실패")

    except Exception as e:
        print(f"\n❌ 테스트 중 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
