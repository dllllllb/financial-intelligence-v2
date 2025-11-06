"""
tests/test_data_loaders.py
데이터 로더 테스트
"""

import sys
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from data import vehicle_master, residual_rates


def test_vehicle_master():
    """차량 마스터 데이터 테스트"""
    print("="*80)
    print("차량 마스터 데이터 테스트")
    print("="*80)

    # 1. 전체 차량 수
    all_ids = vehicle_master.get_all_vehicle_ids()
    print(f"\n✓ 전체 차량 수: {len(all_ids)}대")

    # 2. 브랜드 목록
    brands = vehicle_master.get_brands()
    print(f"✓ 브랜드 수: {len(brands)}개")
    print(f"  샘플: {brands[:10]}")

    # 3. 특정 차량 조회
    test_vehicle_id = all_ids[0]
    vehicle = vehicle_master.get_vehicle(test_vehicle_id)
    print(f"\n✓ 차량 조회 테스트:")
    print(f"  ID: {test_vehicle_id}")
    print(f"  이름: {vehicle['display_name']}")
    print(f"  가격: {vehicle['price']:,}원")
    print(f"  등급: {vehicle['west_grade']}")

    # 4. 브랜드별 필터링
    audi_vehicles = vehicle_master.get_vehicle_list(brand="Audi")
    print(f"\n✓ Audi 차량: {len(audi_vehicles)}대")

    # 5. 검색 테스트
    search_results = vehicle_master.search_vehicles("BMW X7")
    print(f"\n✓ 'BMW X7' 검색 결과: {len(search_results)}대")
    for result in search_results[:3]:
        print(f"  - {result['display']}: {result['price']:,}원")

    return True


def test_residual_rates():
    """잔존율 데이터 테스트"""
    print("\n" + "="*80)
    print("잔존율 데이터 테스트")
    print("="*80)

    # 1. 사용 가능한 캐피탈
    capitals = residual_rates.get_available_capitals()
    print(f"\n✓ 사용 가능한 캐피탈: {capitals}")

    if not capitals:
        print("  ✗ 캐피탈 데이터가 없습니다")
        return False

    capital_id = capitals[0]
    print(f"  테스트 캐피탈: {capital_id}")

    # 2. 차량 수
    vehicle_ids = residual_rates.get_all_vehicle_ids(capital_id)
    print(f"✓ {capital_id} 차량 수: {len(vehicle_ids)}대")

    # 3. 특정 차량의 잔존율 조회
    test_vehicle_id = vehicle_ids[0]
    residual_table = residual_rates.get_vehicle_residual_table(capital_id, test_vehicle_id)
    print(f"\n✓ 잔존율 테이블 조회:")
    print(f"  차량: {test_vehicle_id}")
    print(f"  기간: {list(residual_table.keys())}")

    # 4. 특정 조건 잔존율 조회
    rate_36_20k = residual_rates.get_residual_rate(
        capital_id, test_vehicle_id, 36, 20000
    )
    print(f"\n✓ 36개월/20,000km 잔존율: {rate_36_20k:.2%}")

    # 5. 여러 조건 비교
    print(f"\n✓ 주행거리별 잔존율 비교 (36개월):")
    for mileage in [10000, 15000, 20000, 30000]:
        rate = residual_rates.get_residual_rate(
            capital_id, test_vehicle_id, 36, mileage
        )
        print(f"  {mileage:,}km: {rate:.2%}")

    # 6. 기간별 잔존율 비교
    print(f"\n✓ 기간별 잔존율 비교 (20,000km):")
    for period in [24, 36, 48, 60]:
        rate = residual_rates.get_residual_rate(
            capital_id, test_vehicle_id, period, 20000
        )
        print(f"  {period}개월: {rate:.2%}")

    return True


def test_integration():
    """통합 테스트"""
    print("\n" + "="*80)
    print("통합 테스트 (차량 + 잔존율)")
    print("="*80)

    # BMW X7 검색
    vehicles = vehicle_master.search_vehicles("BMW X7")

    if not vehicles:
        print("  ✗ BMW X7을 찾을 수 없습니다")
        return False

    vehicle_id = vehicles[0]["id"]
    vehicle = vehicle_master.get_vehicle(vehicle_id)

    print(f"\n✓ 선택 차량: {vehicle['display_name']}")
    print(f"  가격: {vehicle['price']:,}원")
    print(f"  등급: {vehicle['west_grade']}")

    # 잔존율 조회
    capital_id = "meritz_capital"

    if not residual_rates.validate_vehicle_exists(capital_id, vehicle_id):
        print(f"  ✗ {capital_id}에 해당 차량의 잔존율 데이터가 없습니다")
        return False

    print(f"\n✓ 잔존율 데이터 (36개월):")
    for mileage in [10000, 15000, 20000, 30000]:
        rate = residual_rates.get_residual_rate(capital_id, vehicle_id, 36, mileage)
        residual_value = vehicle['price'] * rate
        print(f"  {mileage:,}km: {rate:.2%} (잔존가치: {residual_value:,.0f}원)")

    return True


def main():
    """메인 테스트 실행"""
    print("\n" + "🔍 데이터 로더 테스트 시작\n")

    try:
        # 테스트 실행
        test1 = test_vehicle_master()
        test2 = test_residual_rates()
        test3 = test_integration()

        # 결과 출력
        print("\n" + "="*80)
        print("테스트 결과")
        print("="*80)
        print(f"  차량 마스터: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"  잔존율 데이터: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"  통합 테스트: {'✅ PASS' if test3 else '❌ FAIL'}")

        if all([test1, test2, test3]):
            print("\n✅ 모든 테스트 통과!")
        else:
            print("\n❌ 일부 테스트 실패")

    except Exception as e:
        print(f"\n❌ 테스트 중 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
