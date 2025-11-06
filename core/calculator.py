"""
core/calculator.py
운용리스 계산 엔진
"""

from typing import Dict, Optional


def calculate_operating_lease(
    vehicle_price: float,
    contract_months: int,
    down_payment: float,
    residual_rate: float,
    annual_rate: float,
    acquisition_tax_rate: float = 0.0,
    registration_fee: float = 200_000,
    annual_car_tax: float = 0.0,
    method: str = 'simple',
    acquisition_cost: Optional[float] = None
) -> Dict:
    """
    운용리스 월 리스료 계산

    Args:
        vehicle_price: 차량가 (원)
        contract_months: 계약기간 (개월)
        down_payment: 선납금 (보증금)
        residual_rate: 잔존율 (0~1)
        annual_rate: 연이율 (0~1)
        acquisition_tax_rate: 취득세율 (0~1, 영업용은 보통 0)
        registration_fee: 등록비 (원)
        annual_car_tax: 연간 자동차세 (원)
        method: 'simple' (정액법) or 'annuity' (원리금균등)
        acquisition_cost: 취득원가 (차량가+취득세+등록비 등).
                         제공시 금융은 취득원가 기준, 잔존가치는 차량가 기준으로 계산

    Returns:
        Dict: 계산 결과
            - monthly_total: 월 총 리스료
            - monthly_base: 월 기본 리스료 (감가+금융비)
            - monthly_depreciation: 월 감가상각비
            - monthly_finance: 월 금융비용
            - monthly_tax: 월 취득세
            - monthly_registration: 월 등록비
            - monthly_car_tax: 월 자동차세
            - applied_rate: 적용 금리
            - residual_value: 잔존가치
            - residual_rate: 잔존율
            - total_payment: 총 납부액
            - total_interest: 총 이자
            - effective_vehicle_cost: 실차량비용
    """
    # 금융 대상액 계산
    # acquisition_cost가 제공되면 하이브리드 방식 사용:
    #  - 금융 대상액은 취득원가 기준
    #  - 잔존가치는 차량가 기준 (세금/수수료는 잔존가치에 포함되지 않음)
    if acquisition_cost:
        financed = acquisition_cost - down_payment
        residual_value = vehicle_price * residual_rate  # 차량가 기준!
    else:
        financed = vehicle_price - down_payment
        residual_value = financed * residual_rate

    depreciation = financed - residual_value

    r = annual_rate / 12  # 월 금리
    n = contract_months

    # 계산 방식 선택
    if method == 'annuity':
        # 원리금균등상환
        if r == 0:
            monthly_depreciation_payment = depreciation / n
        else:
            monthly_depreciation_payment = depreciation * (r / (1 - (1 + r)**-n))

        monthly_rv_interest = residual_value * r
        monthly_base = monthly_depreciation_payment + monthly_rv_interest
        monthly_finance = monthly_base - (depreciation / n)

    else:  # 'simple' (기본값 - 정액법)
        # 월 감가상각
        monthly_depreciation = depreciation / n

        # 평균 잔액
        average_balance = (financed + residual_value) / 2

        # 월 금융비용
        monthly_finance = average_balance * r

        # 월 기본 리스료
        monthly_base = monthly_depreciation + monthly_finance

    # 세금/비용
    monthly_tax = (vehicle_price * acquisition_tax_rate) / n
    monthly_registration = registration_fee / n
    monthly_car_tax = annual_car_tax / 12

    # 월 총 리스료
    monthly_total = monthly_base + monthly_tax + monthly_registration + monthly_car_tax

    # 총 납부액 계산
    total_payment = monthly_total * n + down_payment
    total_interest = monthly_finance * n

    return {
        'monthly_total': round(monthly_total, -3),  # 천원 단위 반올림
        'monthly_base': round(monthly_base, -3),
        'monthly_depreciation': round(depreciation / n, -3),
        'monthly_finance': round(monthly_finance, -3),
        'monthly_tax': round(monthly_tax, -3),
        'monthly_registration': round(monthly_registration, -3),
        'monthly_car_tax': round(monthly_car_tax, -3),
        'applied_rate': annual_rate,
        'residual_value': round(residual_value, -3),
        'residual_rate': residual_rate,
        'total_payment': round(total_payment, -3),
        'total_interest': round(total_interest, -3),
        'effective_vehicle_cost': round(total_payment - residual_value, -3),
    }


def calculate_auto_tax(engine_cc: int, is_commercial: bool = True) -> float:
    """
    자동차세 계산 (승용차 기준)

    Args:
        engine_cc: 배기량 (cc)
        is_commercial: 영업용 여부 (True: 영업용 50% 감면)

    Returns:
        float: 연간 자동차세 (원)
    """
    # 전기차 (배기량 0)
    if engine_cc == 0:
        base_tax = 100_000  # 전기차 기본세

    # 비영업용 기준 세액
    elif engine_cc <= 1000:
        base_tax = engine_cc * 80

    elif engine_cc <= 1600:
        base_tax = 80_000 + (engine_cc - 1000) * 140 / 600

    elif engine_cc <= 2000:
        base_tax = 164_000 + (engine_cc - 1600) * 200 / 400

    else:  # 2000cc 초과
        base_tax = 364_000 + (engine_cc - 2000) * 220 / 1000

    # 영업용은 50% 감면
    if is_commercial:
        return base_tax * 0.5

    return base_tax


def calculate_acquisition_tax(vehicle_price: float, vehicle_type: str = 'passenger') -> float:
    """
    취득세 계산

    Args:
        vehicle_price: 차량 가격 (원)
        vehicle_type: 차량 종류
            - 'passenger': 승용차 (7%)
            - 'passenger_rv': 승용RV (7%)
            - 'commercial': 영업용 (면제)
            - 'electric': 전기차 (감면 적용)

    Returns:
        float: 취득세 (원)
    """
    # 공급가액 (부가세 제외)
    supply_price = vehicle_price / 1.1

    if vehicle_type == 'commercial':
        # 영업용 등록 시 면제
        return 0

    elif vehicle_type == 'electric':
        # 전기차 감면 (2024년 기준 140만원 한도)
        tax = supply_price * 0.07
        reduction = min(tax, 1_400_000)  # 최대 140만원 감면
        return max(0, tax - reduction)

    else:
        # 일반 승용차/RV: 7%
        return supply_price * 0.07


def calculate_total_acquisition_cost(
    vehicle_price: float,
    vehicle_type: str = 'passenger',
    registration_fee: float = 200_000,
    public_bond: float = 0,
    delivery_fee: float = 0,
    other_fees: float = 0
) -> Dict:
    """
    총 취득원가 계산

    Args:
        vehicle_price: 차량 가격
        vehicle_type: 차량 종류
        registration_fee: 등록비
        public_bond: 공채 매입액
        delivery_fee: 탁송료
        other_fees: 기타 부대비용

    Returns:
        Dict: 취득원가 상세
    """
    acquisition_tax = calculate_acquisition_tax(vehicle_price, vehicle_type)

    total_cost = (
        vehicle_price +
        acquisition_tax +
        registration_fee +
        public_bond +
        delivery_fee +
        other_fees
    )

    return {
        'vehicle_price': vehicle_price,
        'acquisition_tax': round(acquisition_tax, -3),
        'registration_fee': registration_fee,
        'public_bond': public_bond,
        'delivery_fee': delivery_fee,
        'other_fees': other_fees,
        'total_acquisition_cost': round(total_cost, -3)
    }


def calculate_irr(
    vehicle_price: float,
    contract_months: int,
    monthly_lease: float,
    down_payment: float,
    residual_value: float
) -> float:
    """
    내부수익률(IRR) 계산 (간이 계산)

    Args:
        vehicle_price: 차량 가격
        contract_months: 계약 기간
        monthly_lease: 월 리스료
        down_payment: 선납금
        residual_value: 잔존가치

    Returns:
        float: 연간 IRR (0~1)
    """
    # 간이 IRR 계산 (Newton-Raphson 방법 간소화)
    # 실제로는 scipy.optimize를 사용하는 것이 정확함

    # 초기 추정값
    rate = 0.05  # 5%

    for _ in range(100):  # 최대 100번 반복
        # NPV 계산
        npv = -vehicle_price + down_payment

        for month in range(1, contract_months + 1):
            npv += monthly_lease / ((1 + rate/12) ** month)

        npv += residual_value / ((1 + rate/12) ** contract_months)

        # NPV의 미분값
        d_npv = 0
        for month in range(1, contract_months + 1):
            d_npv -= month * monthly_lease / (12 * ((1 + rate/12) ** (month + 1)))

        d_npv -= contract_months * residual_value / (12 * ((1 + rate/12) ** (contract_months + 1)))

        # Newton-Raphson 업데이트
        if abs(d_npv) < 1e-10:
            break

        rate = rate - npv / d_npv

        # 수렴 확인
        if abs(npv) < 1:
            break

    return max(0, min(1, rate))  # 0~100% 범위로 제한
