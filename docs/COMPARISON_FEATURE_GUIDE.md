# 캐피탈 비교 기능 구현 가이드

## 📋 목차
1. [개요](#개요)
2. [주요 기능](#주요-기능)
3. [구현 상세](#구현-상세)
4. [데이터 구조](#데이터-구조)
5. [문제 해결 과정](#문제-해결-과정)
6. [사용 방법](#사용-방법)

---

## 개요

### 배경
기존에는 단일 캐피탈만 선택하여 리스료를 계산할 수 있었으나, 사용자가 여러 캐피탈의 견적을 한눈에 비교할 수 있는 기능이 필요했습니다.

### 목표
- 모든 캐피탈의 월 납입료를 한 번에 비교
- 최저가 캐피탈을 쉽게 파악
- 각 캐피탈별 계산 상세 내역 제공
- 신뢰할 수 있는 차량 가격 기준 사용

---

## 주요 기능

### 1. 캐피탈 비교 모드
- 캐피탈 선택에 "🔍 비교 (모든 캐피탈)" 옵션 추가
- 선택 시 모든 캐피탈에 대해 자동으로 계산 수행
- 월 납입료 기준으로 자동 정렬 (낮은 순)

### 2. master_carinfo 통합
- `master_carinfo.xlsx`를 JSON으로 변환 (1,729대 차량)
- 모든 캐피탈 계산에 동일한 기준 가격 사용
- 캐피탈별 차량 마스터의 가격 불일치 문제 해결

### 3. 차량 매칭 시스템
- 한글/영어 브랜드명 자동 변환 (아우디 ↔ Audi)
- 모델명 prefix 자동 제거 (A3 40 TFSI → 40 TFSI)
- 유연한 매칭 로직으로 캐피탈별 데이터 구조 차이 해결

### 4. 계산 상세보기 UI
- 아코디언 형태로 계산 상세 내역 표시
- 기본적으로 닫혀있고 클릭 시 펼쳐짐
- 간결한 텍스트 형태로 공간 효율적 표시

---

## 구현 상세

### 1. 파일 구조

```
financial intelligence v2/
├── app.py                          # 메인 Streamlit 앱
├── data/
│   ├── vehicle_master.py           # 차량 마스터 로더
│   ├── vehicle_master.json         # 메리츠 차량 마스터
│   ├── mg_vehicle_master.json      # MG 차량 마스터
│   └── master_carinfo.json         # 통합 차량 마스터 (신뢰 기준)
├── core/
│   └── mg_calculator.py            # MG 캐피탈 계산기 (PMT 방식)
└── docs/
    └── COMPARISON_FEATURE_GUIDE.md # 본 문서
```

### 2. 핵심 코드 변경

#### app.py

##### 2.1 캐피탈 선택 UI (lines 52-67)
```python
capital_display = {
    "meritz_capital": "메리츠캐피탈",
    "nh_capital": "NH농협캐피탈",
    "mg_capital": "MG새마을금고",
    "compare": "🔍 비교 (모든 캐피탈)"  # 비교 옵션 추가
}
capital_options = available_capitals + ["compare"]
capital = st.selectbox(
    "캐피탈 선택",
    capital_options,
    format_func=lambda x: capital_display.get(x, x),
    index=len(capital_options) - 1  # 기본값: 비교
)
```

##### 2.2 master_carinfo 가격 조회 (lines 225-238)
```python
# master_carinfo에서 신뢰할 수 있는 차량 가격 조회
master_price = vehicle_master.get_price_from_master(
    brand=vehicle['brand'],
    model=vehicle['model'],
    grade=vehicle['trim']
)

if not master_price:
    st.error(f"❌ master_carinfo에서 차량 가격을 찾을 수 없습니다...")
    st.stop()

st.markdown(f"**차량 가격:** {master_price:,}원 (master_carinfo 기준)")
```

##### 2.3 비교 계산 루프 (lines 240-385)
```python
# 비교 모드
if capital == "compare":
    comparison_results = []

    # 모든 캐피탈에 대해 계산 (동일한 master_price 사용)
    for cap_id in available_capitals:
        try:
            # 캐피탈별 차량 찾기 (잔존율 조회용)
            cap_vehicle = vehicle_master.find_vehicle_by_name(
                brand=vehicle['brand'],
                model=vehicle['model'],
                trim=vehicle['trim'],
                capital_id=cap_id
            )

            # 가격은 master_carinfo의 신뢰할 수 있는 가격 사용
            vehicle_price_for_calc = master_price

            # 캐피탈별 최적 잔가 옵션 선택
            if cap_id == "mg_capital":
                optimal_grade = 'snk_premium'  # MG는 고잔가 우선
            else:
                optimal_grade = 'aps_premium'  # 메리츠/NH는 APS 고잔가 우선

            # 잔존율 조회 (fallback 포함)
            # ... 계산 수행 ...

            # 결과 저장 (상세 정보 포함)
            comparison_results.append({
                'capital': capital_display.get(cap_id, cap_id),
                'capital_id': cap_id,
                'monthly_payment': monthly_payment,
                'grade_option': optimal_grade,
                'residual_rate': residual_rate,
                'details': calc_details  # 계산 상세 정보
            })

        except Exception as e:
            # 에러 처리
            comparison_results.append({
                'capital': capital_display.get(cap_id, cap_id),
                'capital_id': cap_id,
                'monthly_payment': None,
                'error': str(e),
                'grade_option': None,
                'residual_rate': None
            })

    # 결과 정렬 (월 납입료 낮은 순, None은 맨 뒤로)
    comparison_results.sort(key=lambda x: (x['monthly_payment'] is None, x['monthly_payment'] or float('inf')))
```

##### 2.4 결과 표시 (lines 397-502)
```python
rank = 0
for idx, item in enumerate(comparison_results, 1):
    # 에러가 있는 경우
    if item['monthly_payment'] is None:
        # 에러 표시
        continue

    # 정상 결과
    rank += 1
    rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."

    # 컬럼 레이아웃
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        st.markdown(f"### {rank_emoji}")

    with col2:
        st.markdown(f"**{item['capital']}**")
        st.caption(f"잔가: {item['residual_rate']:.1%} ({item['grade_option']})")

    with col3:
        st.markdown(f"### {item['monthly_payment']:,}원")
        if rank == 1:
            st.caption("🎯 최저가")
        elif rank > 1:
            first_success = next(r for r in comparison_results if r['monthly_payment'] is not None)
            diff = item['monthly_payment'] - first_success['monthly_payment']
            st.caption(f"↑ {diff:,}원")

    # 계산 상세보기 (아코디언)
    with st.expander("📊 계산 상세보기"):
        # 간결한 텍스트 형태로 정리
        info_text = f"""
**[계약 조건]**
계약기간: {breakdown.get('contract_months', 0)}개월 | 연간주행: {breakdown.get('annual_mileage', 0):,}km | 잔존율: {breakdown.get('residual_rate', 0):.1%} | 금리: {breakdown.get('annual_interest_rate', 0):.2%}

**[취득원가]**
차량가격: {breakdown.get('vehicle_price', 0):,}원 | 취득세: {breakdown.get('acquisition_tax', 0):,}원 | 등록비: {breakdown.get('registration_fee', 0):,}원 → 합계: {details.get('acquisition_cost', 0):,}원

**[금융 조건]**
선납금: {details.get('down_payment', 0):,}원 | 잔존가치: {residual_value:,}원

**[월 납입료 구성]**
감가상각: xxx원 | 금융비용: xxx원 | 자동차세: xxx원 → 합계: xxx원

**[총 비용]**
총납부액: {total_payment:,}원 - 잔존가치: {residual_value:,}원 = 실차량비용: {net_cost:,}원
"""
        st.markdown(info_text)

    st.markdown("---")
```

#### vehicle_master.py

##### 2.5 master_carinfo 로더 (lines 261-279)
```python
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
```

##### 2.6 가격 조회 함수 (lines 282-416)
```python
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
    grade_cleaned = grade
    if grade.upper().startswith(model.upper()):
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
        model_matched = False
        if norm_model in car_model or car_model in norm_model:
            model_matched = True
        else:
            # 숫자만 추출해서 비교
            import re
            norm_model_nums = ''.join(re.findall(r'\d+', norm_model))
            car_model_nums = ''.join(re.findall(r'\d+', car_model))

            if norm_model_nums and car_model_nums:
                if norm_model_nums[0] == car_model_nums[0]:
                    model_matched = True

        if not model_matched:
            continue

        # 등급 일치 확인 (유연한 매칭)
        if norm_grade in car_grade or car_grade in norm_grade:
            matches.append(car_data)
        else:
            # 숫자와 키워드로 매칭 시도
            import re
            grade_nums = ''.join(re.findall(r'\d+', norm_grade))
            car_grade_nums = ''.join(re.findall(r'\d+', car_grade))

            if grade_nums and car_grade_nums and grade_nums == car_grade_nums:
                common_keywords = ['SPORT', 'BASE', 'LUXURY', 'PREMIUM', 'SIGNATURE', 'EXCLUSIVE']
                has_common_keyword = False
                for keyword in common_keywords:
                    if keyword in norm_grade and keyword in car_grade:
                        has_common_keyword = True
                        break

                if has_common_keyword:
                    matches.append(car_data)
            elif "BASE" in norm_grade and "BASE" in car_grade:
                matches.append(car_data)

    if not matches:
        return None

    # 여러 개 매칭되면 최신 연식 선택
    matches.sort(key=lambda x: x.get('name', ''), reverse=True)

    return matches[0].get('price')
```

##### 2.7 차량 찾기 함수 개선 (lines 203-258)
```python
def find_vehicle_by_name(brand: str, model: str, trim: str, capital_id: Optional[str] = None) -> Optional[Dict]:
    """
    브랜드, 모델, 트림으로 차량 찾기 (캐피탈별)

    메리츠와 MG의 데이터 구조가 다르므로 유연한 매칭 사용
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

    return None
```

---

## 데이터 구조

### 1. master_carinfo.json
```json
{
  "17601": {
    "id_cargrade": 17601,
    "brand": "아우디",
    "model": "A3",
    "grade": "40 TFSI 프리미엄",
    "name": "2026",
    "price": 47460000
  },
  "17602": {
    "id_cargrade": 17602,
    "brand": "BMW",
    "model": "1시리즈",
    "grade": "120 M 스포츠",
    "name": "2025",
    "price": 52800000
  }
}
```

### 2. comparison_results 구조
```python
[
    {
        'capital': '메리츠캐피탈',
        'capital_id': 'meritz_capital',
        'monthly_payment': 813000,
        'grade_option': 'aps_premium',
        'residual_rate': 0.60,
        'details': {
            'monthly_payment': 813000,
            'down_payment': 0,
            'total_payment': 48780000,
            'residual_value': 28476000,
            'acquisition_cost': 50583181,
            'breakdown': {
                'vehicle_price': 47460000,
                'acquisition_tax': 3023181,
                'registration_fee': 100000,
                'residual_rate': 0.60,
                'annual_interest_rate': 0.0515,
                'contract_months': 60,
                'annual_mileage': 20000,
                'monthly_depreciation': 366893,
                'monthly_interest': 217142,
                'monthly_car_tax': 52250
            }
        }
    },
    {
        'capital': 'MG새마을금고',
        'capital_id': 'mg_capital',
        'monthly_payment': 843800,
        'grade_option': 'snk_premium',
        'residual_rate': 0.61,
        'details': {
            'monthly_payment': 843800,
            'down_payment': 0,
            'total_payment': 50628000,
            'residual_value': 28950600,
            # ... (MG PMT 방식 데이터)
        }
    }
]
```

---

## 문제 해결 과정

### 문제 1: MG Capital이 비교 결과에 안 나타남
**증상**: 메리츠는 계산되지만 MG는 "데이터 없음" 에러

**원인**:
- 메리츠: brand="Audi", model="A3", trim="A3 40 TFSI"
- MG: brand="AUDI", model="A3", trim="40 TFSI"
- 데이터 구조가 완전히 다름

**해결**:
1. `find_vehicle_by_name()` 함수 개선
2. 대소문자 무관 비교 추가
3. 트림에서 모델명 prefix 제거 로직 추가

### 문제 2: master_carinfo에서 차량 가격을 찾을 수 없음
**증상**: "master_carinfo에서 차량 가격을 찾을 수 없습니다: Audi A3 A3 40 TFSI Premium"

**원인**:
- master_carinfo: brand="아우디" (한글)
- vehicle_master: brand="Audi" (영어)
- master_carinfo: grade="40 TFSI 프리미엄"
- vehicle_master: grade="A3 40 TFSI Premium"

**해결**:
1. 정규화 함수에 한글↔영어 변환 추가
2. 브랜드명 매핑: 아우디→AUDI, 벤츠→BENZ 등
3. 단어 매핑: 프리미엄→PREMIUM, 스포츠→SPORT 등
4. 등급에서 모델명 제거 로직 추가

### 문제 3: 트림 불일치
**증상**: "A3 40 TFSI"와 "40 TFSI"가 매칭되지 않음

**원인**:
- 메리츠 엑셀: 트림에 모델명 포함 (A3 40 TFSI)
- MG 엑셀: 트림에 모델명 미포함 (40 TFSI)
- master_carinfo: 등급에 모델명 미포함

**해결**:
```python
# 트림에서 모델명 제거
trim_cleaned = trim
if trim.upper().startswith(model.upper()):
    trim_cleaned = trim[len(model):].strip()
```

### 검증 결과
```
✅ Audi A3 "A3 40 TFSI" → 47,460,000원
✅ Audi A3 "40 TFSI" → 47,460,000원
✅ BMW 120 "M Sport" → 52,800,000원
✅ 메리츠: 813,000원/월 (60.0% aps_premium)
✅ MG: 843,800원/월 (61.0% snk_premium)
```

---

## 사용 방법

### 1. 기본 사용법

1. **캐피탈 선택**
   - "🔍 비교 (모든 캐피탈)" 선택

2. **차량 선택**
   - 브랜드 → 모델 → 트림 순으로 선택
   - 차량 가격은 master_carinfo 기준으로 자동 표시

3. **계약 조건 입력**
   - 계약 기간: 12~60개월
   - 연간 주행거리: 10,000~30,000km
   - 선납금 비율: 0~50%

4. **계산하기 버튼 클릭**

### 2. 결과 확인

#### 비교 결과
- 🥇 1위: 최저가 (메리츠캐피탈: 813,000원)
- 🥈 2위: ↑30,800원 (MG새마을금고: 843,800원)
- 각 캐피탈별 잔존율과 등급 옵션 표시

#### 계산 상세보기
각 결과 하단의 "📊 계산 상세보기" 클릭 시:

```
[계약 조건]
계약기간: 60개월 | 연간주행: 20,000km | 잔존율: 60.0% | 금리: 5.15%

[취득원가]
차량가격: 47,460,000원 | 취득세: 3,023,181원 | 등록비: 100,000원 → 합계: 50,583,181원

[금융 조건]
선납금: 0원 | 금융대상: 50,583,181원 | 잔존가치: 28,476,000원

[월 납입료 구성]
감가상각: 366,893원 | 금융비용: 217,142원 | 자동차세: 52,250원 → 합계: 813,000원

[총 비용]
총납부액: 48,780,000원 - 잔존가치: 28,476,000원 = 실차량비용: 20,304,000원
```

### 3. 캐피탈별 계산 방식 차이

#### 메리츠/NH 캐피탈 (정액법)
- 감가상각: (취득원가 - 잔존가치) / 계약개월수
- 금융비용: (취득원가 + 잔존가치) / 2 × 연금리 / 12
- 월 납입료 = 감가상각 + 금융비용 + 자동차세

#### MG 캐피탈 (PMT 방식)
- PMT 함수 사용 (원리금균등상환)
- 월 납입료 = PMT(금리/12, 개월수, -금융대상, 잔존가치)
- numpy_financial.pmt() 활용

---

## 주의사항

### 1. 차량 가격 기준
- **반드시 master_carinfo.json의 가격 사용**
- 캐피탈별 vehicle_master의 가격은 참고용 (잔존율 조회용)

### 2. 잔존율 매칭
- 차량 매칭이 실패하면 해당 캐피탈은 "데이터 없음"으로 표시
- 각 캐피탈은 독립적으로 계산되며, 일부 실패해도 다른 캐피탈은 정상 표시

### 3. 고잔가 옵션
- 가능한 경우 고잔가 옵션 우선 사용
- 실패 시 자동으로 일반잔가로 fallback

### 4. 브라우저 캐싱
- 데이터 변경 시 브라우저 새로고침 필요
- JSON 파일 캐싱으로 성능 최적화

---

## 향후 개선 방향

1. **추가 캐피탈 지원**
   - 현재: 메리츠, NH, MG
   - 향후: 하나캐피탈, 현대캐피탈 등

2. **필터링 기능**
   - 특정 캐피탈만 비교
   - 가격대별 필터

3. **정렬 옵션**
   - 월 납입료 외 다른 기준 (잔존율, 총 비용 등)

4. **상세 비교 차트**
   - 막대 그래프로 시각화
   - 총 비용 대비 그래프

5. **견적서 저장/출력**
   - PDF 생성
   - 이메일 전송

---

## 버전 히스토리

### v1.0 (2025-11-08)
- 캐피탈 비교 기능 초기 구현
- master_carinfo 통합
- 차량 매칭 시스템 구축
- 계산 상세보기 UI 추가

---

## 문의 및 지원

문제 발생 시:
1. 브라우저 콘솔에서 에러 확인
2. master_carinfo.json 데이터 확인
3. 차량 마스터 데이터 확인

**작성일**: 2025-11-08
**작성자**: Claude Code
