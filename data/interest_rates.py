"""
data/interest_rates.py
금리 테이블 및 정책
"""

from typing import Dict, Optional


# 캐피탈별 금리 구조
INTEREST_RATES = {
    "meritz_capital": {
        # 차량가 구간별 기본 금리
        "price_tiers": [
            {"max_price": 30_000_000, "rate": 0.065},  # 3천만원 이하: 6.5%
            {"max_price": 50_000_000, "rate": 0.060},  # 5천만원 이하: 6.0%
            {"max_price": 80_000_000, "rate": 0.055},  # 8천만원 이하: 5.5%
            {"max_price": float('inf'), "rate": 0.050}  # 8천만원 초과: 5.0%
        ],

        # 금리 조정 요소
        "adjustments": {
            "domestic_brand": -0.005,   # 현대/기아 우대 -0.5%p
            "import_brand": 0.005,      # 수입차 할증 +0.5%p
            "ev_vehicle": -0.003,       # 전기차 우대 -0.3%p
            "long_term_48m": -0.002,    # 48개월 이상 우대 -0.2%p
            "high_credit": -0.003,      # 우량고객 우대 -0.3%p
        },

        # 브랜드별 특별 금리 (개발명세서의 "브랜드" 시트 참고)
        "brand_rates": {
            "Audi": 0.0505,
            "Benz": 0.0505,
            "BMW": 0.0505,
            "Cadillac": 0.054,
            "Citroen": 0.058,
            "Ford": 0.058,
            "Honda": 0.058,
            "Jaguar": 0.058,
            "Jeep": 0.058,
            "Lamborghini": 0.058,
            "Landrover": 0.058,
            "Lexus": 0.058,
            "Porsche": 0.0505,
            "Tesla": 0.058,
            "Volvo": 0.058,
            # 국산차
            "현대": 0.048,
            "기아": 0.048,
            "제네시스": 0.048,
        }
    },

    "nh_capital": {
        "price_tiers": [
            {"max_price": 30_000_000, "rate": 0.068},
            {"max_price": 50_000_000, "rate": 0.063},
            {"max_price": 80_000_000, "rate": 0.058},
            {"max_price": float('inf'), "rate": 0.053}
        ],

        "adjustments": {
            "domestic_brand": -0.003,
            "import_brand": 0.006,
            "ev_vehicle": -0.004,
            "long_term_48m": -0.002,
            "high_credit": -0.003,
        },

        "brand_rates": {}
    },

    "mg_capital": {
        "price_tiers": [
            {"max_price": 30_000_000, "rate": 0.070},
            {"max_price": 50_000_000, "rate": 0.065},
            {"max_price": 80_000_000, "rate": 0.060},
            {"max_price": float('inf'), "rate": 0.055}
        ],

        "adjustments": {
            "domestic_brand": 0.000,
            "import_brand": 0.008,
            "ev_vehicle": -0.005,
            "long_term_48m": -0.002,
            "high_credit": -0.003,
        },

        "brand_rates": {}
    }
}


def get_interest_rate(
    capital_id: str,
    vehicle_price: float,
    brand: Optional[str] = None,
    is_import: bool = False,
    is_ev: bool = False,
    contract_months: int = 36,
    high_credit: bool = False
) -> float:
    """
    금리 조회 및 조정

    Args:
        capital_id: 캐피탈 ID (예: "meritz_capital")
        vehicle_price: 차량 가격
        brand: 브랜드명 (예: "BMW", "현대")
        is_import: 수입차 여부
        is_ev: 전기차 여부
        contract_months: 계약 기간
        high_credit: 우량고객 여부

    Returns:
        float: 최종 적용 금리 (연율, 0~1)
    """
    if capital_id not in INTEREST_RATES:
        raise ValueError(f"캐피탈 {capital_id}의 금리 데이터가 없습니다")

    capital_data = INTEREST_RATES[capital_id]

    # 1. 브랜드별 특별 금리 확인 (최우선)
    if brand and brand in capital_data.get("brand_rates", {}):
        base_rate = capital_data["brand_rates"][brand]

    # 2. 차량가 기준 기본 금리
    else:
        base_rate = None
        for tier in capital_data["price_tiers"]:
            if vehicle_price <= tier["max_price"]:
                base_rate = tier["rate"]
                break

        if base_rate is None:
            base_rate = capital_data["price_tiers"][-1]["rate"]

    # 3. 조정 적용
    adjustments = capital_data["adjustments"]
    adjusted_rate = base_rate

    # 국산/수입 조정
    if is_import:
        adjusted_rate += adjustments.get("import_brand", 0)
    else:
        adjusted_rate += adjustments.get("domestic_brand", 0)

    # 전기차 조정
    if is_ev:
        adjusted_rate += adjustments.get("ev_vehicle", 0)

    # 장기 계약 조정
    if contract_months >= 48:
        adjusted_rate += adjustments.get("long_term_48m", 0)

    # 우량고객 조정
    if high_credit:
        adjusted_rate += adjustments.get("high_credit", 0)

    return max(0.0, adjusted_rate)  # 음수 방지


def get_base_rate(capital_id: str, vehicle_price: float) -> float:
    """
    기본 금리 조회 (조정 없이)

    Args:
        capital_id: 캐피탈 ID
        vehicle_price: 차량 가격

    Returns:
        float: 기본 금리
    """
    if capital_id not in INTEREST_RATES:
        raise ValueError(f"캐피탈 {capital_id}의 금리 데이터가 없습니다")

    capital_data = INTEREST_RATES[capital_id]

    for tier in capital_data["price_tiers"]:
        if vehicle_price <= tier["max_price"]:
            return tier["rate"]

    return capital_data["price_tiers"][-1]["rate"]


def get_brand_rate(capital_id: str, brand: str) -> Optional[float]:
    """
    브랜드별 특별 금리 조회

    Args:
        capital_id: 캐피탈 ID
        brand: 브랜드명

    Returns:
        Optional[float]: 특별 금리 (없으면 None)
    """
    if capital_id not in INTEREST_RATES:
        return None

    capital_data = INTEREST_RATES[capital_id]
    return capital_data.get("brand_rates", {}).get(brand)


def get_available_capitals() -> list:
    """사용 가능한 캐피탈 목록"""
    return list(INTEREST_RATES.keys())


def get_rate_adjustments(capital_id: str) -> Dict:
    """
    캐피탈의 금리 조정 정책 조회

    Args:
        capital_id: 캐피탈 ID

    Returns:
        Dict: 금리 조정 정책
    """
    if capital_id not in INTEREST_RATES:
        raise ValueError(f"캐피탈 {capital_id}의 금리 데이터가 없습니다")

    return INTEREST_RATES[capital_id]["adjustments"]
