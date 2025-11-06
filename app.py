"""
app.py
Streamlit 기반 운용리스 계산기 UI
"""

import streamlit as st
from core.calculator import calculate_operating_lease, calculate_auto_tax
from data import vehicle_master, residual_rates, interest_rates
from core.validator import validate_lease_input, ValidationError

# 페이지 설정
st.set_page_config(
    page_title="운용리스 계산기 v2",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일
st.markdown("""
<style>
.big-font {
    font-size:20px !important;
    font-weight: bold;
}
.metric-box {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# 제목
st.title("🚗 운용리스 계산기 v2")
st.markdown("---")

# 사이드바: 입력 영역
with st.sidebar:
    st.header("💼 계산 조건 입력")

    # 0. 캐피탈 선택
    st.subheader("0️⃣ 캐피탈 선택")
    available_capitals = residual_rates.get_available_capitals()

    if not available_capitals:
        st.error("❌ 캐피탈 데이터가 없습니다!")
        st.stop()

    capital_display = {
        "meritz_capital": "메리츠캐피탈",
        "nh_capital": "NH농협캐피탈",
        "mg_capital": "MG새마을금고"
    }

    selected_capital = st.selectbox(
        "캐피탈을 선택하세요",
        options=available_capitals,
        format_func=lambda x: capital_display.get(x, x),
        key="capital"
    )

    # 잔가 옵션 선택
    grade_option = st.selectbox(
        "잔가 옵션",
        options=['aps_premium', 'aps_normal', 'west_premium', 'west_normal', 'vgs_premium', 'vgs_normal'],
        index=0,
        format_func=lambda x: {
            'aps_premium': 'APS 고잔가 (최대)',
            'aps_normal': 'APS 일반잔가',
            'west_premium': 'West 고잔가',
            'west_normal': 'West 일반잔가',
            'vgs_premium': 'VGS 고잔가',
            'vgs_normal': 'VGS 일반잔가'
        }.get(x, x),
        key="grade_option"
    )

    # 1. 차량 선택
    st.subheader("1️⃣ 차량 선택")

    # 브랜드 필터
    brands = vehicle_master.get_brands()
    selected_brand = st.selectbox(
        "브랜드",
        options=["전체"] + brands,
        key="brand"
    )

    # 차량 목록
    if selected_brand == "전체":
        vehicle_list = vehicle_master.get_vehicle_list()
    else:
        vehicle_list = vehicle_master.get_vehicle_list(brand=selected_brand)

    # 가격 범위 필터
    if vehicle_list:
        min_price = min(v["price"] for v in vehicle_list)
        max_price = max(v["price"] for v in vehicle_list)

        price_range = st.slider(
            "가격 범위 (만원)",
            min_value=int(min_price/10000),
            max_value=int(max_price/10000),
            value=(int(min_price/10000), int(max_price/10000)),
            key="price_range"
        )

        # 가격 필터 적용
        vehicle_list = [
            v for v in vehicle_list
            if price_range[0] * 10000 <= v["price"] <= price_range[1] * 10000
        ]

    # 차량 선택
    if vehicle_list:
        vehicle_options = {v["display"]: v["id"] for v in vehicle_list}
        selected_vehicle_name = st.selectbox(
            "차량을 선택하세요",
            options=list(vehicle_options.keys()),
            key="vehicle"
        )
        selected_vehicle_id = vehicle_options[selected_vehicle_name]
        vehicle = vehicle_master.get_vehicle(selected_vehicle_id)

        st.info(f"💰 차량가: {vehicle['price']:,}원")
    else:
        st.warning("⚠ 선택 가능한 차량이 없습니다")
        st.stop()

    # 2. 계약 조건
    st.subheader("2️⃣ 계약 조건")

    col1, col2 = st.columns(2)

    with col1:
        contract_months = st.selectbox(
            "계약 기간",
            options=[24, 36, 48, 60],
            index=1,
            format_func=lambda x: f"{x}개월",
            key="period"
        )

    with col2:
        annual_mileage = st.selectbox(
            "연간 주행거리",
            options=[10000, 15000, 20000, 30000],
            index=2,
            format_func=lambda x: f"{x:,}km",
            key="mileage"
        )

    # 3. 선납금
    st.subheader("3️⃣ 선납금 (보증금)")

    max_down = vehicle['price'] * 0.5
    down_payment_percent = st.slider(
        "차량가 대비 비율",
        min_value=0,
        max_value=50,
        value=0,
        step=5,
        format="%d%%",
        key="down_percent"
    )

    down_payment = vehicle['price'] * (down_payment_percent / 100)
    st.caption(f"💵 선납금: {down_payment:,.0f}원")

    st.markdown("---")
    calculate_button = st.button("💡 계산하기", type="primary", use_container_width=True)

# 메인 영역: 결과 표시
if calculate_button:
    with st.spinner("계산 중..."):
        try:
            # 입력 검증
            validation = validate_lease_input(
                vehicle_price=vehicle['price'],
                contract_months=contract_months,
                down_payment=down_payment,
                annual_mileage=annual_mileage
            )

            # 경고 표시
            if validation.get('warnings'):
                for warning in validation['warnings']:
                    st.warning(f"⚠ {warning}")

            # 잔존율 조회
            try:
                residual_rate = residual_rates.get_residual_rate(
                    selected_capital, selected_vehicle_id,
                    contract_months, annual_mileage,
                    grade_option=grade_option
                )
            except ValueError as e:
                st.error(f"❌ 잔존율 데이터 없음: {e}")
                st.info("💡 다른 계약 기간이나 주행거리를 선택해주세요")
                st.stop()

            # 금리 조회
            annual_rate = interest_rates.get_interest_rate(
                capital_id=selected_capital,
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

        except ValidationError as e:
            st.error(f"❌ 입력 오류: {str(e)}")
            st.stop()
        except Exception as e:
            st.error(f"❌ 계산 오류: {str(e)}")
            st.stop()

    # 결과 표시
    st.success("✅ 계산 완료!")

    # 주요 결과
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 월 리스료",
            value=f"{result['monthly_total']:,.0f}원"
        )

    with col2:
        st.metric(
            label="📊 잔존가치",
            value=f"{result['residual_value']:,.0f}원",
            delta=f"{residual_rate:.1%}"
        )

    with col3:
        st.metric(
            label="📈 적용 금리",
            value=f"{result['applied_rate']:.2%}"
        )

    with col4:
        st.metric(
            label="💵 총 납부액",
            value=f"{result['total_payment']:,.0f}원"
        )

    st.markdown("---")

    # 상세 내역
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 월 리스료 상세")

        breakdown = [
            ("감가상각비", result['monthly_depreciation']),
            ("금융비용", result['monthly_finance']),
            ("등록비", result['monthly_registration']),
            ("자동차세", result['monthly_car_tax']),
        ]

        for label, value in breakdown:
            st.write(f"**{label}:** {value:,.0f}원")

        st.write("---")
        st.write(f"**합계:** {result['monthly_total']:,.0f}원")

    with col2:
        st.subheader("📊 총 비용 분석")

        summary = [
            ("총 납부액", result['total_payment']),
            ("총 이자", result['total_interest']),
            ("잔존가치", result['residual_value']),
            ("실차량비용", result['effective_vehicle_cost']),
        ]

        for label, value in summary:
            st.write(f"**{label}:** {value:,.0f}원")

    # 조건별 비교
    st.markdown("---")
    st.subheader("🔍 조건별 비교")

    tab1, tab2 = st.tabs(["기간별 비교", "주행거리별 비교"])

    with tab1:
        st.write(f"**주행거리:** {annual_mileage:,}km/년")

        comparison_data = []
        for period in [24, 36, 48, 60]:
            try:
                temp_rate = residual_rates.get_residual_rate(
                    selected_capital, selected_vehicle_id, period, annual_mileage,
                    grade_option=grade_option
                )
                temp_annual_rate = interest_rates.get_interest_rate(
                    capital_id=selected_capital,
                    vehicle_price=vehicle['price'],
                    brand=vehicle['brand'],
                    is_import=vehicle['is_import'],
                    is_ev=(vehicle['engine_cc'] == 0),
                    contract_months=period
                )
                temp_result = calculate_operating_lease(
                    vehicle_price=vehicle['price'],
                    contract_months=period,
                    down_payment=down_payment,
                    residual_rate=temp_rate,
                    annual_rate=temp_annual_rate,
                    acquisition_tax_rate=0.0,
                    registration_fee=200_000,
                    annual_car_tax=annual_car_tax,
                    method='simple'
                )
                comparison_data.append({
                    "기간": f"{period}개월",
                    "월 리스료": f"{temp_result['monthly_total']:,.0f}원",
                    "잔존율": f"{temp_rate:.1%}",
                    "총 납부액": f"{temp_result['total_payment']:,.0f}원"
                })
            except:
                pass

        if comparison_data:
            st.table(comparison_data)

    with tab2:
        st.write(f"**계약 기간:** {contract_months}개월")

        comparison_data = []
        for mileage in [10000, 15000, 20000, 30000]:
            try:
                temp_rate = residual_rates.get_residual_rate(
                    selected_capital, selected_vehicle_id, contract_months, mileage,
                    grade_option=grade_option
                )
                temp_result = calculate_operating_lease(
                    vehicle_price=vehicle['price'],
                    contract_months=contract_months,
                    down_payment=down_payment,
                    residual_rate=temp_rate,
                    annual_rate=annual_rate,
                    acquisition_tax_rate=0.0,
                    registration_fee=200_000,
                    annual_car_tax=annual_car_tax,
                    method='simple'
                )
                comparison_data.append({
                    "주행거리": f"{mileage:,}km",
                    "월 리스료": f"{temp_result['monthly_total']:,.0f}원",
                    "잔존율": f"{temp_rate:.1%}",
                    "총 납부액": f"{temp_result['total_payment']:,.0f}원"
                })
            except:
                pass

        if comparison_data:
            st.table(comparison_data)

    # 참고사항
    st.markdown("---")
    st.info(f"""
    ℹ️ **참고사항**
    - 캐피탈: {capital_display.get(selected_capital, selected_capital)}
    - 본 계산기는 영업용 등록 기준입니다 (취득세 면제)
    - 보험료는 별도이며, 고객님께서 직접 가입하셔야 합니다
    - 실제 리스료는 신용도, 프로모션 등에 따라 달라질 수 있습니다
    - 계산 방식: 정액법 (감가상각 균등 분할)
    """)

else:
    # 초기 화면
    st.info("👈 왼쪽에서 조건을 입력하고 '계산하기' 버튼을 눌러주세요")

    # 데이터 통계
    st.markdown("---")
    st.subheader("📊 데이터 현황")

    col1, col2, col3 = st.columns(3)

    with col1:
        vehicle_count = len(vehicle_master.get_all_vehicle_ids())
        st.metric("등록된 차량 수", f"{vehicle_count:,}대")

    with col2:
        capital_count = len(residual_rates.get_available_capitals())
        st.metric("등록된 캐피탈 수", f"{capital_count}개")

    with col3:
        brand_count = len(vehicle_master.get_brands())
        st.metric("등록된 브랜드 수", f"{brand_count}개")

    # 브랜드별 통계
    st.markdown("---")
    st.subheader("🏢 브랜드별 차량 수")

    brands = vehicle_master.get_brands()
    brand_stats = []
    for brand in brands[:10]:  # 상위 10개
        count = len(vehicle_master.get_vehicle_list(brand=brand))
        brand_stats.append({"브랜드": brand, "차량 수": f"{count}대"})

    if brand_stats:
        st.table(brand_stats)
