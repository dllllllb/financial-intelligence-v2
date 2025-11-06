"""
data/residual_rates.py
잔존율 데이터 로더 (JSON 기반)
"""

import json
from pathlib import Path
from typing import Dict, Optional, List

# 캐피탈별 잔존율 캐시
_RESIDUAL_CACHE: Dict[str, Dict] = {}


def _load_residual_rates(capital_id: str) -> Dict:
    """
    캐피탈별 잔존율 데이터 로드 (캐싱)

    Args:
        capital_id: 캐피탈 ID (예: "meritz_capital")

    Returns:
        Dict: 전체 차량의 잔존율 데이터

    Raises:
        FileNotFoundError: 잔존율 파일이 없는 경우
    """
    if capital_id not in _RESIDUAL_CACHE:
        json_path = Path(__file__).parent / "residual_rates" / f"{capital_id}.json"

        if not json_path.exists():
            raise FileNotFoundError(f"잔존율 데이터 파일이 없습니다: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            _RESIDUAL_CACHE[capital_id] = json.load(f)

    return _RESIDUAL_CACHE[capital_id]


def get_residual_rate(capital_id: str, vehicle_id: str,
                      contract_months: int, annual_mileage: int,
                      grade_option: str = 'aps_premium') -> float:
    """
    잔존율 조회

    Args:
        capital_id: 캐피탈 ID (예: "meritz_capital")
        vehicle_id: 차량 ID
        contract_months: 계약 기간 (24, 36, 48, 60)
        annual_mileage: 연간 주행거리 (10000, 15000, 20000, 30000)
        grade_option: 잔가 옵션 (west_normal, west_premium, aps_normal, aps_premium, vgs_normal, vgs_premium)
                     기본값: aps_premium (APS 고잔가)

    Returns:
        float: 잔존율 (0~1 사이 값)

    Raises:
        ValueError: 데이터가 없는 경우
    """
    data = _load_residual_rates(capital_id)

    # JSON은 키가 문자열이므로 변환
    months_key = str(contract_months)
    mileage_key = str(annual_mileage)

    try:
        # 새로운 데이터 구조: data[vehicle_id][grade_option][months][mileage]
        return data[vehicle_id][grade_option][months_key][mileage_key]
    except KeyError as e:
        # 폴백: 요청한 옵션이 없으면 다른 옵션 시도
        try:
            vehicle_data = data[vehicle_id]
            # 사용 가능한 옵션 찾기
            available_options = list(vehicle_data.keys())
            if available_options:
                fallback_option = available_options[0]
                return vehicle_data[fallback_option][months_key][mileage_key]
        except:
            pass

        raise ValueError(
            f"잔존율 데이터 없음: {capital_id}/{vehicle_id}/{grade_option}/{contract_months}/{annual_mileage}"
        ) from e


def get_vehicle_residual_table(capital_id: str, vehicle_id: str) -> Dict:
    """
    특정 차량의 전체 잔존율 테이블 조회

    Args:
        capital_id: 캐피탈 ID
        vehicle_id: 차량 ID

    Returns:
        Dict: {24: {10000: 0.65, ...}, 36: {...}, ...}

    Raises:
        ValueError: 차량 데이터가 없는 경우
    """
    data = _load_residual_rates(capital_id)

    if vehicle_id not in data:
        raise ValueError(f"차량 {vehicle_id}의 잔존율 데이터가 없습니다")

    # 문자열 키를 정수로 변환
    result = {}
    for months_str, mileage_dict in data[vehicle_id].items():
        months = int(months_str)
        result[months] = {
            int(mileage_str): rate
            for mileage_str, rate in mileage_dict.items()
        }

    return result


def get_all_vehicle_ids(capital_id: str) -> list:
    """캐피탈의 전체 차량 목록"""
    data = _load_residual_rates(capital_id)
    return list(data.keys())


def validate_vehicle_exists(capital_id: str, vehicle_id: str) -> bool:
    """차량 데이터 존재 여부 확인"""
    try:
        data = _load_residual_rates(capital_id)
        return vehicle_id in data
    except FileNotFoundError:
        return False


def get_available_capitals() -> list:
    """사용 가능한 캐피탈 목록"""
    data_dir = Path(__file__).parent / "residual_rates"

    if not data_dir.exists():
        return []

    capitals = []
    for json_file in data_dir.glob("*.json"):
        capital_id = json_file.stem
        capitals.append(capital_id)

    return capitals


def get_available_periods(capital_id: str, vehicle_id: str) -> List[int]:
    """특정 차량의 사용 가능한 계약 기간 목록"""
    table = get_vehicle_residual_table(capital_id, vehicle_id)
    return sorted(list(table.keys()))


def get_available_mileages(capital_id: str, vehicle_id: str, contract_months: int) -> List[int]:
    """특정 차량/기간의 사용 가능한 주행거리 목록"""
    table = get_vehicle_residual_table(capital_id, vehicle_id)

    if contract_months not in table:
        return []

    return sorted(list(table[contract_months].keys()))
