"""
tools/excel_to_json.py
캐피탈사 엑셀 파일을 JSON으로 일괄 변환
"""

import json
from pathlib import Path
import sys

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from excel_reverse_engineering.residual_extractor import ResidualRateExtractor


def convert_excel_to_json(excel_path: str, capital_id: str,
                          output_dir: str = "data/residual_rates"):
    """
    엑셀 파일을 JSON으로 변환

    Parameters:
        excel_path: 엑셀 파일 경로
        capital_id: 캐피탈 ID (예: "meritz_capital")
        output_dir: JSON 저장 디렉토리
    """
    print("="*60)
    print(f"엑셀 → JSON 변환 시작")
    print(f"파일: {excel_path}")
    print(f"캐피탈: {capital_id}")
    print("="*60)

    # 1. 엑셀에서 잔존율 추출
    extractor = ResidualRateExtractor(excel_path)
    all_vehicles = extractor.extract_all_vehicles()

    print(f"\n총 {len(all_vehicles)}대 차량 추출 완료")

    # 2. JSON 형식으로 변환 (키를 문자열로)
    json_data = {}
    for vehicle_id, residual_table in all_vehicles.items():
        json_data[vehicle_id] = {
            str(months): {
                str(mileage): rate
                for mileage, rate in mileage_dict.items()
            }
            for months, mileage_dict in residual_table.items()
        }

    # 3. JSON 파일 저장
    output_path = Path(output_dir) / f"{capital_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    print(f"\n저장 완료: {output_path}")
    print(f"파일 크기: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

    # 4. 검증
    print("\n데이터 검증 중...")
    validate_json_data(output_path)

    return output_path


def validate_json_data(json_path: Path):
    """JSON 데이터 검증"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_vehicles = len(data)
    complete_vehicles = 0
    incomplete_vehicles = []

    expected_periods = ["24", "36", "48", "60"]
    expected_mileages = ["10000", "15000", "20000", "30000"]

    for vehicle_id, residual_table in data.items():
        # 모든 기간과 주행거리가 있는지 확인
        is_complete = True

        for period in expected_periods:
            if period not in residual_table:
                is_complete = False
                break

            for mileage in expected_mileages:
                if mileage not in residual_table[period]:
                    is_complete = False
                    break

        if is_complete:
            complete_vehicles += 1
        else:
            incomplete_vehicles.append(vehicle_id)

    print(f"  ✓ 전체 차량: {total_vehicles}대")
    print(f"  ✓ 완전한 데이터: {complete_vehicles}대")

    if incomplete_vehicles:
        print(f"  ⚠ 불완전한 데이터: {len(incomplete_vehicles)}대")
        print(f"     {incomplete_vehicles[:5]}..." if len(incomplete_vehicles) > 5 else f"     {incomplete_vehicles}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="엑셀 견적기를 JSON으로 변환")
    parser.add_argument("excel_path", help="엑셀 파일 경로")
    parser.add_argument("capital_id", help="캐피탈 ID (예: meritz_capital)")
    parser.add_argument("--output-dir", default="data/residual_rates",
                       help="JSON 저장 디렉토리")

    args = parser.parse_args()

    convert_excel_to_json(
        excel_path=args.excel_path,
        capital_id=args.capital_id,
        output_dir=args.output_dir
    )

    print("\n✅ 변환 완료!")
