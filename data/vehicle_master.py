"""
data/vehicle_master.py
차량 마스터 데이터 로더
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

# 싱글톤 캐시 (capital별)
_VEHICLE_CACHE: Dict[str, Dict] = {}
_MASTER_CARINFO_CACHE: Optional[Dict] = None


def _load_vehicles(capital_id: Optional[str] = None) -> Dict:
    """
    차량 데이터 로드 (캐싱)

    Args:
        capital_id: 캐피탈 ID (예: "mg_capital")
                   None이면 기본 vehicle_master.json 로드
    """
    cache_key = capital_id or "default"

    if cache_key not in _VEHICLE_CACHE:
        if capital_id and capital_id.startswith("mg_"):
            # MG Capital: mg_vehicle_master.json 사용
            json_path = Path(__file__).parent / "mg_vehicle_master.json"
        else:
            # Default: vehicle_master.json 사용 (메리츠 등)
            json_path = Path(__file__).parent / "vehicle_master.json"

        if not json_path.exists():
            raise FileNotFoundError(f"차량 마스터 파일이 없습니다: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            _VEHICLE_CACHE[cache_key] = json.load(f)

    return _VEHICLE_CACHE[cache_key]


def get_vehicle(vehicle_id: str, capital_id: Optional[str] = None) -> Dict:
    """
    차량 상세 정보 조회

    Args:
        vehicle_id: 차량 ID (예: "AUDI_A3_A3_40_TFSI")
        capital_id: 캐피탈 ID (None이면 기본)

    Returns:
        Dict: 차량 정보

    Raises:
        ValueError: 차량 ID를 찾을 수 없는 경우
    """
    vehicles = _load_vehicles(capital_id)

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

    # 가격 순으로 정렬 (None은 맨 뒤로)
    result.sort(key=lambda x: (x["price"] is None, x["price"] or float('inf')))

    return result


def get_all_vehicle_ids(capital_id: Optional[str] = None) -> List[str]:
    """전체 차량 ID 목록"""
    vehicles = _load_vehicles(capital_id)
    return list(vehicles.keys())


def validate_vehicle_exists(vehicle_id: str, capital_id: Optional[str] = None) -> bool:
    """차량 존재 여부 확인"""
    vehicles = _load_vehicles(capital_id)
    return vehicle_id in vehicles


def get_brands(capital_id: Optional[str] = None) -> List[str]:
    """전체 브랜드 목록"""
    vehicles = _load_vehicles(capital_id)
    brands = set(v["brand"] for v in vehicles.values())
    return sorted(list(brands))


def get_models_by_brand(brand: str, capital_id: Optional[str] = None) -> List[str]:
    """
    브랜드별 기본 모델 목록 조회

    Args:
        brand: 브랜드명 (예: "BMW", "Audi")
        capital_id: 캐피탈 ID

    Returns:
        List[str]: 모델 목록 (중복 제거, 정렬)
    """
    vehicles = _load_vehicles(capital_id)
    models = set()

    for vehicle_data in vehicles.values():
        if vehicle_data["brand"] == brand:
            models.add(vehicle_data["model"])

    return sorted(list(models))


def get_trims_by_brand_model(brand: str, model: str, capital_id: Optional[str] = None) -> List[Dict]:
    """
    브랜드와 모델로 세부 트림 목록 조회

    Args:
        brand: 브랜드명
        model: 모델명
        capital_id: 캐피탈 ID

    Returns:
        List[Dict]: 트림 목록 [{"id": ..., "trim": ..., "price": ...}, ...]
    """
    vehicles = _load_vehicles(capital_id)
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

    # 가격 순으로 정렬 (None은 맨 뒤로)
    result.sort(key=lambda x: (x["price"] is None, x["price"] or float('inf')))

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


def find_vehicle_by_name(brand: str, model: str, trim: str, capital_id: Optional[str] = None) -> Optional[Dict]:
    """
    브랜드, 모델, 트림으로 차량 찾기 (캐피탈별)

    메리츠와 MG의 데이터 구조가 다르므로 유연한 매칭 사용

    Args:
        brand: 브랜드명
        model: 모델명
        trim: 트림명
        capital_id: 캐피탈 ID

    Returns:
        Dict: 차량 정보 (id 포함) 또는 None
    """
    vehicles = _load_vehicles(capital_id)

    # 트림에서 모델명 제거 (예: "A3 40 TFSI" → "40 TFSI")
    trim_cleaned = trim
    if trim.upper().startswith(model.upper()):
        trim_cleaned = trim[len(model):].strip()

    # 정확히 일치하는 차량 먼저 찾기
    for vehicle_id, vehicle_data in vehicles.items():
        if (vehicle_data["brand"].upper() == brand.upper() and
            vehicle_data["model"].upper() == model.upper() and
            vehicle_data["trim"].upper() == trim.upper()):
            return {
                "id": vehicle_id,
                **vehicle_data
            }

    # 트림에서 모델명 제거한 버전으로 재시도
    for vehicle_id, vehicle_data in vehicles.items():
        if (vehicle_data["brand"].upper() == brand.upper() and
            vehicle_data["model"].upper() == model.upper() and
            vehicle_data["trim"].upper() == trim_cleaned.upper()):
            return {
                "id": vehicle_id,
                **vehicle_data
            }

    # 정확히 일치하지 않으면 브랜드+모델만 일치하는 것 중 트림이 포함된 것 찾기
    for vehicle_id, vehicle_data in vehicles.items():
        if (vehicle_data["brand"].upper() == brand.upper() and
            vehicle_data["model"].upper() == model.upper() and
            (trim.upper() in vehicle_data["trim"].upper() or
             trim_cleaned.upper() in vehicle_data["trim"].upper())):
            return {
                "id": vehicle_id,
                **vehicle_data
            }

    # 모델명도 다를 수 있으므로 브랜드만 일치하면서 가격이 비슷한 차량 찾기
    # (메리츠와 MG의 데이터 구조가 완전히 다르기 때문)
    return None  # 일단 None 반환


def _load_master_carinfo() -> Dict:
    """
    master_carinfo.json 로드 (캐싱)

    Returns:
        Dict: {id_cargrade: {차량정보}}
    """
    global _MASTER_CARINFO_CACHE

    if _MASTER_CARINFO_CACHE is None:
        json_path = Path(__file__).parent / "master_carinfo.json"

        if not json_path.exists():
            raise FileNotFoundError(f"master_carinfo 파일이 없습니다: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            _MASTER_CARINFO_CACHE = json.load(f)

    return _MASTER_CARINFO_CACHE


def get_price_from_master(brand: str, model: str, grade: str) -> Optional[int]:
    """
    master_carinfo에서 차량 가격 조회

    브랜드+모델+등급으로 매칭, 여러 연식이 있으면 최신 것 선택

    Args:
        brand: 브랜드명 (예: "BMW")
        model: 모델명 (예: "1시리즈" 또는 "1_series" 또는 "120")
        grade: 등급/트림 (예: "120i Sport" 또는 "120 M 스포츠" 또는 "M Sport")

    Returns:
        int: 차량 가격 또는 None
    """
    master_carinfo = _load_master_carinfo()

    # 정규화 함수 (비교를 위해)
    def normalize(s: str) -> str:
        if not s:
            return ""
        # 대문자 변환
        s = s.upper()

        # 브랜드명 한글 -> 영어 변환
        brand_map = {
            "아우디": "AUDI",
            "벤츠": "BENZ",
            "메르세데스벤츠": "BENZ",
            "비엠더블유": "BMW",
            "폭스바겐": "VOLKSWAGEN",
            "포르쉐": "PORSCHE",
            "포르셰": "PORSCHE",
            "렉서스": "LEXUS",
            "토요타": "TOYOTA",
            "혼다": "HONDA",
            "닛산": "NISSAN",
            "현대": "HYUNDAI",
            "기아": "KIA",
            "제네시스": "GENESIS"
        }
        for kr, en in brand_map.items():
            s = s.replace(kr, en)

        # 일반 단어 한글 -> 영어 변환
        s = s.replace("시리즈", "SERIES")
        s = s.replace("베이스", "BASE")
        s = s.replace("스포츠", "SPORT")
        s = s.replace("프리미엄", "PREMIUM")
        s = s.replace("럭셔리", "LUXURY")
        s = s.replace("시그니처", "SIGNATURE")
        s = s.replace("익스클루시브", "EXCLUSIVE")

        # 공백, 특수문자 제거
        s = s.replace(" ", "").replace("_", "").replace("-", "")

        return s

    norm_brand = normalize(brand)
    norm_model = normalize(model)

    # 등급에서 모델명 제거 (예: "A3 40 TFSI" → "40 TFSI")
    # 일부 vehicle_master에서 trim에 모델명이 포함되어 있는 경우 대응
    grade_cleaned = grade
    if grade.upper().startswith(model.upper()):
        # 모델명으로 시작하면 제거
        grade_cleaned = grade[len(model):].strip()

    norm_grade = normalize(grade_cleaned)

    # 매칭되는 차량 찾기
    matches = []
    for id_cargrade, car_data in master_carinfo.items():
        car_brand = normalize(car_data.get('brand', ''))
        car_model = normalize(car_data.get('model', ''))
        car_grade = normalize(car_data.get('grade', ''))

        # 브랜드 일치 확인
        if norm_brand != car_brand:
            continue

        # 모델 일치 확인 (유연한 매칭)
        # 예: "1SERIES" ↔ "120", "X5" ↔ "X530D"
        model_matched = False
        if norm_model in car_model or car_model in norm_model:
            model_matched = True
        else:
            # 숫자만 추출해서 비교 (예: "1SERIES" → "1", "120" → "120")
            import re
            norm_model_nums = ''.join(re.findall(r'\d+', norm_model))
            car_model_nums = ''.join(re.findall(r'\d+', car_model))

            # 앞자리 숫자가 일치하면 같은 시리즈로 간주
            if norm_model_nums and car_model_nums:
                if norm_model_nums[0] == car_model_nums[0]:
                    model_matched = True

        if not model_matched:
            continue

        # 등급 일치 확인 (유연한 매칭)
        # 예: "120ISPORT" ↔ "120MSPORT", "BASE" ↔ "120BASE"
        if norm_grade in car_grade or car_grade in norm_grade:
            matches.append(car_data)
        else:
            # 숫자와 키워드로 매칭 시도
            import re
            grade_nums = ''.join(re.findall(r'\d+', norm_grade))
            car_grade_nums = ''.join(re.findall(r'\d+', car_grade))

            # 등급에 숫자가 있고 일치하면 매칭
            if grade_nums and car_grade_nums and grade_nums == car_grade_nums:
                # 키워드 추출 및 매칭 (SPORT, BASE 등)
                # "120ISPORT" → ['SPORT'], "120MSPORT" → ['SPORT']
                common_keywords = ['SPORT', 'BASE', 'LUXURY', 'PREMIUM', 'SIGNATURE', 'EXCLUSIVE']

                # 공통 키워드가 둘 다에 포함되어 있는지 확인
                has_common_keyword = False
                for keyword in common_keywords:
                    if keyword in norm_grade and keyword in car_grade:
                        has_common_keyword = True
                        break

                if has_common_keyword:
                    matches.append(car_data)
            # "BASE"와 같이 숫자 없는 경우
            elif "BASE" in norm_grade and "BASE" in car_grade:
                matches.append(car_data)

    if not matches:
        return None

    # 여러 개 매칭되면 최신 연식 선택 (name 필드)
    matches.sort(key=lambda x: x.get('name', ''), reverse=True)

    return matches[0].get('price')
