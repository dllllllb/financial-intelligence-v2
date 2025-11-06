"""
data/vehicle_master.py
차량 마스터 데이터 로더
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

# 싱글톤 캐시
_VEHICLE_CACHE: Optional[Dict] = None


def _load_vehicles() -> Dict:
    """차량 데이터 로드 (캐싱)"""
    global _VEHICLE_CACHE

    if _VEHICLE_CACHE is None:
        json_path = Path(__file__).parent / "vehicle_master.json"
        if not json_path.exists():
            raise FileNotFoundError(f"차량 마스터 파일이 없습니다: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            _VEHICLE_CACHE = json.load(f)

    return _VEHICLE_CACHE


def get_vehicle(vehicle_id: str) -> Dict:
    """
    차량 상세 정보 조회

    Args:
        vehicle_id: 차량 ID (예: "AUDI_A3_A3_40_TFSI")

    Returns:
        Dict: 차량 정보

    Raises:
        ValueError: 차량 ID를 찾을 수 없는 경우
    """
    vehicles = _load_vehicles()

    if vehicle_id not in vehicles:
        raise ValueError(f"차량 ID를 찾을 수 없습니다: {vehicle_id}")

    return vehicles[vehicle_id]


def get_vehicle_list(brand: Optional[str] = None,
                     vehicle_type: Optional[str] = None,
                     is_import: Optional[bool] = None) -> List[Dict]:
    """
    차량 목록 조회 (필터링 가능)

    Args:
        brand: 브랜드 필터 (예: "Audi", "BMW")
        vehicle_type: 차종 필터 (예: "sedan", "suv")
        is_import: 수입차 여부 필터

    Returns:
        List[Dict]: 차량 목록 [{"id": ..., "display": ..., "price": ...}, ...]
    """
    vehicles = _load_vehicles()

    result = []
    for vehicle_id, vehicle_data in vehicles.items():
        # 필터 적용
        if brand and vehicle_data["brand"] != brand:
            continue
        if is_import is not None and vehicle_data["is_import"] != is_import:
            continue

        result.append({
            "id": vehicle_id,
            "display": vehicle_data["display_name"],
            "brand": vehicle_data["brand"],
            "price": vehicle_data["price"],
            "is_import": vehicle_data["is_import"]
        })

    # 가격 순으로 정렬
    result.sort(key=lambda x: x["price"])

    return result


def get_all_vehicle_ids() -> List[str]:
    """전체 차량 ID 목록"""
    vehicles = _load_vehicles()
    return list(vehicles.keys())


def validate_vehicle_exists(vehicle_id: str) -> bool:
    """차량 존재 여부 확인"""
    vehicles = _load_vehicles()
    return vehicle_id in vehicles


def get_brands() -> List[str]:
    """전체 브랜드 목록"""
    vehicles = _load_vehicles()
    brands = set(v["brand"] for v in vehicles.values())
    return sorted(list(brands))


def get_models_by_brand(brand: str) -> List[str]:
    """
    브랜드별 기본 모델 목록 조회

    Args:
        brand: 브랜드명 (예: "BMW", "Audi")

    Returns:
        List[str]: 모델 목록 (중복 제거, 정렬)
    """
    vehicles = _load_vehicles()
    models = set()

    for vehicle_data in vehicles.values():
        if vehicle_data["brand"] == brand:
            models.add(vehicle_data["model"])

    return sorted(list(models))


def get_trims_by_brand_model(brand: str, model: str) -> List[Dict]:
    """
    브랜드와 모델로 세부 트림 목록 조회

    Args:
        brand: 브랜드명
        model: 모델명

    Returns:
        List[Dict]: 트림 목록 [{"id": ..., "trim": ..., "price": ...}, ...]
    """
    vehicles = _load_vehicles()
    result = []

    for vehicle_id, vehicle_data in vehicles.items():
        if (vehicle_data["brand"] == brand and
            vehicle_data["model"] == model):
            result.append({
                "id": vehicle_id,
                "trim": vehicle_data["trim"],
                "display": vehicle_data["display_name"],
                "price": vehicle_data["price"]
            })

    # 가격 순으로 정렬
    result.sort(key=lambda x: x["price"])

    return result


def search_vehicles(keyword: str, limit: int = 20) -> List[Dict]:
    """
    키워드로 차량 검색

    Args:
        keyword: 검색 키워드
        limit: 최대 결과 수

    Returns:
        List[Dict]: 검색 결과
    """
    vehicles = _load_vehicles()
    keyword_lower = keyword.lower()

    result = []
    for vehicle_id, vehicle_data in vehicles.items():
        # 브랜드, 모델, 트림에서 검색
        if (keyword_lower in vehicle_data["brand"].lower() or
            keyword_lower in vehicle_data["model"].lower() or
            keyword_lower in vehicle_data["trim"].lower()):
            result.append({
                "id": vehicle_id,
                "display": vehicle_data["display_name"],
                "brand": vehicle_data["brand"],
                "price": vehicle_data["price"]
            })

    return result[:limit]
