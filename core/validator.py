"""
core/validator.py
입력 검증 및 유효성 검사
"""

from typing import Dict, Optional, List


class ValidationError(Exception):
    """검증 오류"""
    pass


def validate_lease_input(
    vehicle_price: float,
    contract_months: int,
    down_payment: float = 0,
    residual_rate: Optional[float] = None,
    annual_mileage: Optional[int] = None
) -> Dict:
    """
    리스 입력값 검증

    Args:
        vehicle_price: 차량 가격
        contract_months: 계약 기간
        down_payment: 선납금
        residual_rate: 잔존율
        annual_mileage: 연간 주행거리

    Returns:
        Dict: 검증 결과 및 경고 메시지

    Raises:
        ValidationError: 검증 실패 시
    """
    errors = []
    warnings = []

    # 차량 가격 검증
    if vehicle_price <= 0:
        errors.append("차량 가격은 0보다 커야 합니다")
    elif vehicle_price < 10_000_000:
        warnings.append("차량 가격이 1천만원 미만입니다. 확인해주세요")
    elif vehicle_price > 500_000_000:
        warnings.append("차량 가격이 5억원을 초과합니다. 확인해주세요")

    # 계약 기간 검증
    valid_periods = [24, 36, 48, 60]
    if contract_months not in valid_periods:
        errors.append(f"계약 기간은 {valid_periods} 중 하나여야 합니다")

    # 선납금 검증
    if down_payment < 0:
        errors.append("선납금은 음수일 수 없습니다")
    elif down_payment > vehicle_price:
        errors.append("선납금이 차량 가격을 초과할 수 없습니다")
    elif down_payment > vehicle_price * 0.5:
        warnings.append("선납금이 차량 가격의 50%를 초과합니다")

    # 잔존율 검증
    if residual_rate is not None:
        if residual_rate < 0 or residual_rate > 1:
            errors.append("잔존율은 0~1 사이여야 합니다")
        elif residual_rate < 0.1:
            warnings.append("잔존율이 10% 미만입니다. 확인해주세요")
        elif residual_rate > 0.8:
            warnings.append("잔존율이 80%를 초과합니다. 확인해주세요")

    # 주행거리 검증
    if annual_mileage is not None:
        valid_mileages = [10000, 15000, 20000, 30000]
        if annual_mileage not in valid_mileages:
            warnings.append(f"일반적인 주행거리는 {valid_mileages}km입니다")

    # 오류가 있으면 예외 발생
    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "valid": True,
        "warnings": warnings
    }


def calculate_recommended_down_payment(
    vehicle_price: float,
    monthly_income: Optional[float] = None
) -> Dict:
    """
    권장 선납금 계산

    Args:
        vehicle_price: 차량 가격
        monthly_income: 월 소득 (선택)

    Returns:
        Dict: 권장 선납금 정보
    """
    recommendations = []

    # 기본 권장: 0%, 10%, 20%, 30%
    for percentage in [0, 0.1, 0.2, 0.3]:
        amount = vehicle_price * percentage
        recommendations.append({
            "percentage": percentage,
            "amount": amount,
            "description": f"{int(percentage*100)}% 선납"
        })

    # 월 소득 기반 권장 (있는 경우)
    if monthly_income:
        # 월 소득의 20% 이하를 리스료로 권장
        max_monthly_lease = monthly_income * 0.2
        # 간이 계산으로 필요한 선납금 추정
        # (실제로는 정확한 계산 필요)

    return {
        "recommendations": recommendations,
        "note": "선납금이 많을수록 월 리스료가 낮아집니다"
    }


def validate_comparison_inputs(
    vehicle_ids: List[str],
    capital_ids: List[str],
    contract_months: int,
    annual_mileage: int
) -> Dict:
    """
    비교 입력값 검증

    Args:
        vehicle_ids: 차량 ID 목록
        capital_ids: 캐피탈 ID 목록
        contract_months: 계약 기간
        annual_mileage: 연간 주행거리

    Returns:
        Dict: 검증 결과
    """
    errors = []
    warnings = []

    if len(vehicle_ids) == 0:
        errors.append("최소 1대 이상의 차량을 선택해야 합니다")
    elif len(vehicle_ids) > 5:
        warnings.append("5대 이상의 차량을 비교하면 가독성이 떨어질 수 있습니다")

    if len(capital_ids) == 0:
        errors.append("최소 1개 이상의 캐피탈을 선택해야 합니다")

    if errors:
        raise ValidationError("; ".join(errors))

    return {
        "valid": True,
        "warnings": warnings
    }


def check_data_availability(
    capital_id: str,
    vehicle_id: str,
    contract_months: int,
    annual_mileage: int
) -> Dict:
    """
    데이터 가용성 확인

    Args:
        capital_id: 캐피탈 ID
        vehicle_id: 차량 ID
        contract_months: 계약 기간
        annual_mileage: 연간 주행거리

    Returns:
        Dict: 가용성 정보
    """
    from data import residual_rates

    try:
        rate = residual_rates.get_residual_rate(
            capital_id, vehicle_id, contract_months, annual_mileage
        )
        return {
            "available": True,
            "residual_rate": rate
        }
    except (ValueError, KeyError, FileNotFoundError) as e:
        return {
            "available": False,
            "error": str(e)
        }
