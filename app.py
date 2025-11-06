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

    # 1-1. 브랜드 선택
    brands = vehicle_master.get_brands()
    selected_brand = st.selectbox(
        "브랜드",
        options=brands,
        key="brand"
    )

    # 1-2. 기본 모델 선택
    models = vehicle_master.get_models_by_brand(selected_brand)

    if not models:
        st.warning(f"⚠ {selected_brand}의 모델이 없습니다")
        st.stop()

    selected_model = st.selectbox(
        "기본 모델",
        options=models,
        key="model"
    )

    # 1-3. 세부 트림 선택
    trims = vehicle_master.get_trims_by_brand_model(selected_brand, selected_model)

    if not trims:
        st.warning(f"⚠ {selected_brand} {selected_model}의 트림이 없습니다")
        st.stop()

    # 트림 선택 (가격 정보 포함)
    trim_options = {
        f"{t['trim']} ({t['price']:,}원)": t['id']
        for t in trims
    }

    selected_trim_display = st.selectbox(
        "세부 트림",
        options=list(trim_options.keys()),
        key="trim"
    )

    selected_vehicle_id = trim_options[selected_trim_display]
    vehicle = vehicle_master.get_vehicle(selected_vehicle_id)

    st.info(f"💰 선택한 차량: {vehicle['display_name']}")
    st.caption(f"   차량가: {vehicle['price']:,}원")

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
                is_commercial=False  # 개인
            )

            # 리스료 계산
            # 과세표준 방식 (메리츠 엑셀과 동일)
            taxable_base = vehicle['price'] / 1.1  # VAT 제외
            acquisition_tax_rate = 0.07  # 개인 7%
            acquisition_tax = taxable_base * acquisition_tax_rate
            registration_fee = 100_000  # 등록비
            acquisition_cost_total = vehicle['price'] + acquisition_tax + registration_fee

            result = calculate_operating_lease(
                vehicle_price=vehicle['price'],
                contract_months=contract_months,
                down_payment=down_payment,
                residual_rate=residual_rate,
                annual_rate=annual_rate,
                acquisition_tax_rate=0.0,  # 취득세는 이미 취득원가에 포함됨
                registration_fee=registration_fee,
                annual_car_tax=annual_car_tax,
                method='simple',
                acquisition_cost=acquisition_cost_total  # 하이브리드 방식
            )

        except ValidationError as e:
            st.error(f"❌ 입력 오류: {str(e)}")
            st.stop()
        except Exception as e:
            st.error(f"❌ 계산 오류: {str(e)}")
            st.stop()

    # ========================================
    # 견적서 스타일 결과 표시
    # ========================================

    st.markdown("---")
    st.markdown("### 📋 운용리스 견적서")

    # 1. 차량 및 계약 정보
    st.markdown("#### 1️⃣ 차량 정보")
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown(f"""
        **차량명:** {vehicle['display_name']}
        **차량가격:** {vehicle['price']:,}원
        **배기량:** {vehicle['engine_cc']:,}cc
        **유종:** {vehicle['fuel_type']}
        """)

    with info_col2:
        st.markdown(f"""
        **캐피탈:** {capital_display.get(selected_capital, selected_capital)}
        **계약기간:** {contract_months}개월
        **연간주행거리:** {annual_mileage:,}km
        **잔가옵션:** {grade_option}
        """)

    # 2. 상세 계산 과정
    st.markdown("---")
    st.markdown("#### 2️⃣ 상세 계산 과정")

    calc_col1, calc_col2 = st.columns(2)

    with calc_col1:
        st.markdown("**📌 취득 원가 계산**")
        taxable_base_display = taxable_base
        acquisition_tax_amount = acquisition_tax
        acquisition_cost_display = vehicle['price'] + acquisition_tax_amount + 100_000
        financed_amount = acquisition_cost_display - down_payment

        st.markdown(f"""
        ```
        차량가격:           {vehicle['price']:>15,}원
        과세표준:           {taxable_base_display:>15,.0f}원  (차량가 ÷ 1.1)
        취득세 (7%):        {acquisition_tax_amount:>15,.0f}원  (과세표준 × 0.07)
        등록비:             {100_000:>15,}원
        ───────────────────────────────────
        취득원가:           {acquisition_cost_display:>15,.0f}원
        (-) 선납금:         {down_payment:>15,.0f}원
        ───────────────────────────────────
        금융대상금액:       {financed_amount:>15,.0f}원
        ```
        """)

        st.markdown("**📌 감가상각 계산**")
        total_depreciation = financed_amount - result['residual_value']

        st.markdown(f"""
        ```
        차량가격:           {vehicle['price']:>15,}원
        잔존율 ({residual_rate:.1%}):    {residual_rate:>15.1%}
        ───────────────────────────────────
        잔존가치:           {result['residual_value']:>15,.0f}원

        금융대상:           {financed_amount:>15,.0f}원
        (-) 잔존가치:       {result['residual_value']:>15,.0f}원
        ───────────────────────────────────
        총 감가상각:        {total_depreciation:>15,.0f}원
        ÷ {contract_months}개월
        ───────────────────────────────────
        월 감가상각비:      {result['monthly_depreciation']:>15,.0f}원
        ```
        """)

    with calc_col2:
        st.markdown("**📌 금융비용 계산**")
        monthly_interest_rate = annual_rate / 12
        st.markdown(f"""
        ```
        금융대상금액:       {financed_amount:>15,.0f}원
        연 이자율:          {annual_rate:>15.2%}
        월 이자율:          {monthly_interest_rate:>15.4%}

        평균잔액법 적용
        ───────────────────────────────────
        월 금융비용:        {result['monthly_finance']:>15,.0f}원
        총 금융비용:        {result['total_interest']:>15,.0f}원
        ```
        """)

        st.markdown("**📌 부대비용 계산**")
        st.markdown(f"""
        ```
        등록비 (월할):      {result['monthly_registration']:>15,.0f}원
          = {100_000:,}원 ÷ {contract_months}개월

        자동차세 (월할):    {result['monthly_car_tax']:>15,.0f}원
          = {annual_car_tax:,}원 ÷ 12개월
        ```
        """)

    # 3. 월 납입료 총계
    st.markdown("---")
    st.markdown("#### 3️⃣ 월 납입료")

    st.markdown(f"""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50;'>
        <table style='width: 100%; font-size: 16px;'>
            <tr>
                <td><b>감가상각비</b></td>
                <td style='text-align: right;'>{result['monthly_depreciation']:>15,}원</td>
            </tr>
            <tr>
                <td><b>금융비용</b></td>
                <td style='text-align: right;'>{result['monthly_finance']:>15,}원</td>
            </tr>
            <tr>
                <td><b>취득세 (월할)</b></td>
                <td style='text-align: right;'>{result['monthly_tax']:>15,}원</td>
            </tr>
            <tr>
                <td><b>등록비 (월할)</b></td>
                <td style='text-align: right;'>{result['monthly_registration']:>15,}원</td>
            </tr>
            <tr>
                <td><b>자동차세 (월할)</b></td>
                <td style='text-align: right;'>{result['monthly_car_tax']:>15,}원</td>
            </tr>
            <tr style='border-top: 2px solid #333; font-size: 20px;'>
                <td><b>💰 월 납입료 합계</b></td>
                <td style='text-align: right; color: #4CAF50;'><b>{result['monthly_total']:>15,}원</b></td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # 4. 총 비용 요약
    st.markdown("---")
    st.markdown("#### 4️⃣ 총 비용 요약")

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

    with summary_col1:
        st.metric("📅 총 납부액", f"{result['total_payment']:,}원",
                  help=f"월 {result['monthly_total']:,}원 × {contract_months}개월")

    with summary_col2:
        st.metric("💸 총 이자", f"{result['total_interest']:,}원",
                  help="전체 계약기간 동안 발생하는 금융비용")

    with summary_col3:
        st.metric("🚗 잔존가치", f"{result['residual_value']:,}원",
                  delta=f"{residual_rate:.1%}",
                  help="계약 종료 시 차량 잔존가치")

    with summary_col4:
        st.metric("💵 실차량비용", f"{result['effective_vehicle_cost']:,}원",
                  help="총 납부액 - 잔존가치 = 실제 차량 사용 비용")

    # 5. 조건별 비교 (탭 없이 한번에 표시)
    st.markdown("---")
    st.markdown("#### 5️⃣ 조건별 비교")

    # 5-1. 기간별 비교
    st.markdown("**📊 기간별 비교** (주행거리: {:,}km/년)".format(annual_mileage))

    period_comparison = []
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
                acquisition_tax_rate=0.0,  # 취득세는 이미 취득원가에 포함됨
                registration_fee=100_000,
                annual_car_tax=annual_car_tax,
                method='simple',
                acquisition_cost=acquisition_cost_total
            )

            # 현재 선택된 기간 표시
            period_mark = " ⭐" if period == contract_months else ""

            period_comparison.append({
                "계약기간": f"{period}개월{period_mark}",
                "잔존율": f"{temp_rate:.1%}",
                "월 리스료": f"{temp_result['monthly_total']:,}원",
                "총 납부액": f"{temp_result['total_payment']:,}원",
                "총 이자": f"{temp_result['total_interest']:,}원"
            })
        except:
            pass

    if period_comparison:
        st.table(period_comparison)

    st.markdown("")  # 간격

    # 5-2. 주행거리별 비교
    st.markdown("**🚗 주행거리별 비교** (계약기간: {}개월)".format(contract_months))

    mileage_comparison = []
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
                acquisition_tax_rate=0.0,  # 취득세는 이미 취득원가에 포함됨
                registration_fee=100_000,
                annual_car_tax=annual_car_tax,
                method='simple',
                acquisition_cost=acquisition_cost_total
            )

            # 현재 선택된 주행거리 표시
            mileage_mark = " ⭐" if mileage == annual_mileage else ""

            mileage_comparison.append({
                "연간주행거리": f"{mileage:,}km{mileage_mark}",
                "잔존율": f"{temp_rate:.1%}",
                "월 리스료": f"{temp_result['monthly_total']:,}원",
                "총 납부액": f"{temp_result['total_payment']:,}원",
                "총 이자": f"{temp_result['total_interest']:,}원"
            })
        except:
            pass

    if mileage_comparison:
        st.table(mileage_comparison)

    # 참고사항
    st.markdown("---")
    st.info(f"""
    ℹ️ **참고사항**
    - 캐피탈: {capital_display.get(selected_capital, selected_capital)}
    - 본 계산기는 개인 등록 기준입니다 (취득세 7%, 과세표준 방식)
    - 과세표준 = 차량가 ÷ 1.1 (VAT 제외)
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
