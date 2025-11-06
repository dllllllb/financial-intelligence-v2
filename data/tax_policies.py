"""
data/tax_policies.py
세금 및 수수료 정책
"""

from typing import Dict


# 지역별 공채 매입 정책 (차량가 대비 비율)
PUBLIC_BOND_RATES = {
    "서울": {
        "승용": 0.05,
        "승용RV": 0.0,
        "화물": 0.0
    },
    "부산": {
        "승용": 0.05,
        "승용RV": 0.0,
        "화물": 0.0
    },
    "대구": {
        "승용": 0.05,
        "승용RV": 0.0,
        "화물": 0.0
    },
    "인천": {
        "승용": 0.09,
        "승용RV": 0.0,
        "화물": 0.0
    },
    "광주": {
        "승용": 0.0,
        "승용RV": 0.0,
        "화물": 0.0
    },
    "대전": {
        "승용": 0.05,
        "승용RV": 0.0,
        "화물": 0.0
    },
    "울산": {
        "승용": 0.0,
        "승용RV": 0.0,
        "화물": 0.0
    },
    "경기": {
        "승용": 0.0,
        "승용RV": 0.0,
        "화물": 0.0
    }
}

# 공채 할인율 (지역별)
PUBLIC_BOND_DISCOUNT = {
    "서울": 0.08,
    "부산": 0.08,
    "대구": 0.08,
    "인천": 0.09,
    "광주": 0.0,
    "대전": 0.08,
    "울산": 0.0,
    "경기": 0.0
}


def get_public_bond_cost(
    vehicle_price: float,
    region: str,
    vehicle_type: str = "승용"
) -> Dict:
    """
    공채 매입 비용 계산

    Args:
        vehicle_price: 차량 가격
        region: 등록 지역
        vehicle_type: 차량 종류 ("승용", "승용RV", "화물")

    Returns:
        Dict: 공채 관련 비용
            - bond_amount: 공채 매입액
            - discount_rate: 할인율
            - discount_amount: 할인액
            - actual_cost: 실제 부담액
    """
    # 공채 매입 비율
    bond_rate = PUBLIC_BOND_RATES.get(region, {}).get(vehicle_type, 0.0)
    bond_amount = vehicle_price * bond_rate

    # 할인율
    discount_rate = PUBLIC_BOND_DISCOUNT.get(region, 0.0)
    discount_amount = bond_amount * discount_rate

    # 실제 부담액
    actual_cost = bond_amount - discount_amount

    return {
        "bond_amount": round(bond_amount, -3),
        "discount_rate": discount_rate,
        "discount_amount": round(discount_amount, -3),
        "actual_cost": round(actual_cost, -3)
    }


def get_registration_fee(
    vehicle_type: str = "승용",
    registration_method: str = "대행"
) -> float:
    """
    등록비 조회

    Args:
        vehicle_type: 차량 종류
        registration_method: 등록 방법 ("대행", "직접")

    Returns:
        float: 등록비 (원)
    """
    if registration_method == "직접":
        # 직접 등록 시 기본 비용만
        return 50_000

    # 대행 등록 기본 비용
    base_fees = {
        "승용": 200_000,
        "승용RV": 200_000,
        "화물": 150_000,
        "전기": 200_000
    }

    return base_fees.get(vehicle_type, 200_000)


def get_delivery_fee(
    distance: str = "전국",
    vehicle_size: str = "일반"
) -> float:
    """
    탁송료 조회

    Args:
        distance: 거리 ("서울", "수도권", "전국")
        vehicle_size: 차량 크기 ("일반", "대형")

    Returns:
        float: 탁송료 (원)
    """
    fees = {
        "서울": {"일반": 100_000, "대형": 150_000},
        "수도권": {"일반": 150_000, "대형": 200_000},
        "전국": {"일반": 188_000, "대형": 250_000}
    }

    return fees.get(distance, {}).get(vehicle_size, 188_000)


def calculate_total_fees(
    vehicle_price: float,
    region: str = "서울",
    vehicle_type: str = "승용",
    registration_method: str = "대행",
    delivery_distance: str = "전국",
    vehicle_size: str = "일반",
    other_fees: float = 0
) -> Dict:
    """
    총 부대비용 계산

    Args:
        vehicle_price: 차량 가격
        region: 등록 지역
        vehicle_type: 차량 종류
        registration_method: 등록 방법
        delivery_distance: 탁송 거리
        vehicle_size: 차량 크기
        other_fees: 기타 비용

    Returns:
        Dict: 부대비용 상세
    """
    # 공채 비용
    bond_costs = get_public_bond_cost(vehicle_price, region, vehicle_type)

    # 등록비
    registration_fee = get_registration_fee(vehicle_type, registration_method)

    # 탁송료
    delivery_fee = get_delivery_fee(delivery_distance, vehicle_size)

    # 총 비용
    total = (
        bond_costs["actual_cost"] +
        registration_fee +
        delivery_fee +
        other_fees
    )

    return {
        "public_bond": bond_costs,
        "registration_fee": registration_fee,
        "delivery_fee": delivery_fee,
        "other_fees": other_fees,
        "total_fees": round(total, -3)
    }


def get_available_regions() -> list:
    """등록 가능한 지역 목록"""
    return list(PUBLIC_BOND_RATES.keys())
