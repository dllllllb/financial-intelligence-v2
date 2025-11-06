# 메리츠캐피탈 엑셀 추출기 구현 가이드

## 📋 목차
1. [개요](#개요)
2. [메리츠 엑셀 구조 분석](#메리츠-엑셀-구조-분석)
3. [구현 과정에서 발생한 문제와 해결](#구현-과정에서-발생한-문제와-해결)
4. [최종 구현 내용](#최종-구현-내용)
5. [실행 방법](#실행-방법)
6. [검증 방법](#검증-방법)
7. [향후 업데이트 시 체크리스트](#향후-업데이트-시-체크리스트)

---

## 개요

**파일**: `excel_reverse_engineering/meritz_extractor.py`

**목적**: 메리츠캐피탈 엑셀 견적서에서 차량 정보와 잔존율 데이터를 추출하여 JSON 파일로 변환

**출력**:
- `data/vehicle_master.json`: 차량 마스터 데이터 (1,041대)
- `data/residual_rates/meritz_capital.json`: 잔존율 데이터 (1,010대)

---

## 메리츠 엑셀 구조 분석

### 1. 시트 구조

메리츠 엑셀 견적서는 2개의 주요 시트로 구성:

#### 1.1 **"차종" 시트**
- **위치**: 차량 목록 및 등급 정보
- **데이터 시작**: Row 7부터
- **주요 컬럼**:
  ```
  A (1)  : 순번
  B (2)  : Maker (제조사)
  C (3)  : Model1 (모델명)
  D (4)  : Model2
  E (5)  : Model3 (세부 트림명)
  F (6)  : 차량가격
  G (7)  : 배기량 (cc)
  H (8)  : 유종
  I (9)  : 차종구분
  J (10) : West 등급 ⚠️
  K (11) : AJ 등급 ⚠️
  L (12) : APS 등급 ⚠️
  M (13) : VGS 등급 ⚠️
  P (16) : 고잔가추가 15,000 (장기 계약 프리미엄) ⭐
  Q (17) : 고잔가추가1 10,000 (장기 계약 프리미엄) ⭐
  ```

**⚠️ 중요**: openpyxl의 `cell(row, col)`은 1-based 인덱싱이지만, `iter_rows(values_only=True)[0]`의 배열 인덱스는 0-based입니다!

**올바른 인덱싱**:
```python
row_data = list(sheet.iter_rows(min_row=7, max_row=7, values_only=True))[0]

maker = row_data[1]        # 컬럼 B = 배열 인덱스 1
model1 = row_data[2]       # 컬럼 C = 배열 인덱스 2
model3 = row_data[4]       # 컬럼 E = 배열 인덱스 4
price = row_data[5]        # 컬럼 F = 배열 인덱스 5
west_grade = row_data[9]   # 컬럼 J = 배열 인덱스 9  ✅
aj_grade = row_data[10]    # 컬럼 K = 배열 인덱스 10 ✅
aps_grade = row_data[11]   # 컬럼 L = 배열 인덱스 11 ✅
vgs_grade = row_data[12]   # 컬럼 M = 배열 인덱스 12 ✅
premium_add_15k = row_data[15]  # 컬럼 P = 배열 인덱스 15 ✅
premium_add_10k = row_data[16]  # 컬럼 Q = 배열 인덱스 16 ✅
```

**❌ 흔한 실수**:
```python
# WRONG! 컬럼 번호를 그대로 사용하면 1칸씩 밀림
west_grade = row_data[10]  # 실제로는 K 컬럼을 읽음
aps_grade = row_data[12]   # 실제로는 M 컬럼을 읽음
```

#### 1.2 **"잔가" 시트**
- **위치**: 캐피탈사별 잔가 마스터 테이블
- **구조**: 4개 캐피탈사의 등급별 잔가 테이블

**주행거리 조정값**:
```
Row 36-39, 컬럼 9-10 (I-J)
- 10,000km: 조정값
- 15,000km: 조정값
- 20,000km: 조정값 (기준: 0.0)
- 30,000km: 조정값
```

**West 캐피탈 테이블**:
```
Row 48: 헤더 (등급명)
  컬럼 C-M: SA1, SA, A1, A, B, C, D, E, F, G, P
Row 49-54: 기간별 잔가율
  컬럼 B: 기간 (12, 24, 36, 48, 60, 72)
  컬럼 C-M: 각 등급의 잔가율 (0.0 ~ 1.0)
```

**AJ 캐피탈 테이블**:
```
Row 57: 헤더
  컬럼 C-W: SA1, SA, A1, A, B, C, D, E, F, G, H, I, J, K, L, M, P, S, T, X
Row 58-63: 기간별 잔가율
  컬럼 B: 기간 (12, 24, 36, 48, 60, 72)
```

**APS 캐피탈 테이블**:
```
Row 65: 헤더
  컬럼 C-X: SA1, SA, A1, A, B, C, D, E, F, G, H, I, J, K, L, M, P, S, T, U, X
Row 66-71: 기간별 잔가율
```

**VGS 캐피탈 테이블**:
```
Row 73: 헤더
  컬럼 C-L: SA1, SA, A, B, C, D, E, F, G, H
Row 74-78: 기간별 잔가율
```

**⚠️ 중요 발견**:
- 12개월, 72개월은 사용하지 않음 → 24, 36, 48, 60개월만 추출
- 등급 헤더의 첫 번째 셀은 "기간"이므로 스킵해야 함

---

## 구현 과정에서 발생한 문제와 해결

### 문제 1: West 등급만 추출 (초기 버전)

**증상**:
- BMW X2가 엑셀에서 63% 잔존율인데, 우리 시스템에서 52%로 표시됨
- 추출된 차량 962대 중 잔존율 데이터가 있는 차량이 145대뿐

**원인**:
- 초기 구현에서 West 등급 테이블만 추출
- BMW X2는 West: A (52%), APS: H (55% → 고잔가 63%)
- 메리츠 엑셀은 4개 등급 시스템을 모두 제공하며, 사용자가 선택 가능

**해결**:
```python
# BEFORE: West만 추출
def _extract_residual_tables(self):
    tables = {}
    tables['west'] = self._parse_residual_table(...)
    return tables

# AFTER: 4개 시스템 모두 추출
def _extract_residual_tables(self):
    tables = {}
    tables['west'] = self._parse_residual_table(
        start_row=49, end_row=54, grade_row=48,
        grade_col_start=2, grade_col_end=13
    )
    tables['aj'] = self._parse_residual_table(
        start_row=58, end_row=63, grade_row=57,
        grade_col_start=2, grade_col_end=23
    )
    tables['aps'] = self._parse_residual_table(
        start_row=66, end_row=71, grade_row=65,
        grade_col_start=2, grade_col_end=24
    )
    tables['vgs'] = self._parse_residual_table(
        start_row=74, end_row=78, grade_row=73,
        grade_col_start=2, grade_col_end=12
    )
    return tables
```

**결과**:
- 추출 차량: 962대 → 1,041대
- 잔존율 데이터: 145대 → 1,010대

---

### 문제 2: 컬럼 인덱스 오류

**증상**:
- 엑셀에서 BMW X2의 등급이 "West: A, APS: H"로 표시됨
- 추출 결과에서 "West: None, APS: RV(5인이하)"로 나옴
- 컬럼이 1칸씩 밀려서 읽힘

**원인**:
- openpyxl의 `cell(row, col)` 메서드는 1-based 인덱싱 사용
- `iter_rows(values_only=True)[0]`의 배열 접근은 0-based 인덱싱
- 컬럼 J(10번째)를 읽으려면 배열 인덱스는 9를 사용해야 함

**잘못된 코드**:
```python
# ❌ WRONG
row_data = list(sheet.iter_rows(min_row=7, max_row=7, values_only=True))[0]
west_grade = row_data[10]  # 컬럼 K를 읽게 됨
aj_grade = row_data[11]    # 컬럼 L을 읽게 됨
aps_grade = row_data[12]   # 컬럼 M을 읽게 됨
vgs_grade = row_data[13]   # 컬럼 N을 읽게 됨 (존재하지 않음)
```

**올바른 코드**:
```python
# ✅ CORRECT
row_data = list(sheet.iter_rows(min_row=7, max_row=7, values_only=True))[0]
west_grade = row_data[9]   # 컬럼 J (10번째) = 배열 인덱스 9
aj_grade = row_data[10]    # 컬럼 K (11번째) = 배열 인덱스 10
aps_grade = row_data[11]   # 컬럼 L (12번째) = 배열 인덱스 11
vgs_grade = row_data[12]   # 컬럼 M (13번째) = 배열 인덱스 12
```

**검증 방법**:
```python
# 엑셀에서 특정 차량의 등급을 육안으로 확인한 후
# 출력된 vehicle_master.json에서 해당 차량의 등급 확인
{
  "BMW_X2_X2_XDRIVE_20I_M_MESH": {
    "west_grade": "A",     # 엑셀과 일치 ✅
    "aps_grade": "H"       # 엑셀과 일치 ✅
  }
}
```

---

### 문제 3: 고잔가 옵션 누락

**증상**:
- BMW X2의 APS H 등급이 55%로 추출됨
- 엑셀에서는 "최대잔가" 옵션 선택 시 63%로 표시됨
- 차이: 8%p

**원인**:
- 메리츠 엑셀은 "일반잔가"와 "고잔가(최대잔가)" 2가지 옵션 제공
- 고잔가 = 일반잔가 + 보정율
  - APS/AJ: +8%p (36개월 기준)
  - VGS: +6%p
- 초기 구현에서 일반잔가만 추출

**해결**:
```python
def _apply_premium_adjustment(self, normal_data: Dict, premium_rate: float,
                             long_term_premium: float = 0.0) -> Dict:
    """
    일반잔가에 고잔가 보정 적용

    Args:
        normal_data: 일반잔가 데이터
        premium_rate: 기본 보정율 (0.08 = +8%p, 0.06 = +6%p)
        long_term_premium: 장기 계약 추가 프리미엄 (48/60개월에만 적용)

    Returns:
        Dict: 고잔가 데이터
    """
    premium_data = {}

    for period, mileages in normal_data.items():
        premium_data[period] = {}

        # 48/60개월에는 장기 계약 추가 프리미엄 적용
        total_premium = premium_rate
        if period in [48, 60] and long_term_premium > 0:
            total_premium += long_term_premium

        for mileage, rate in mileages.items():
            # 최대 95%로 제한
            premium_data[period][mileage] = round(min(0.95, rate + total_premium), 4)

    return premium_data

# 차량별 6개 옵션 생성
residual_data = {}

# 장기 계약 추가 프리미엄 계산 (48/60개월용)
# P열: 고잔가추가 15,000, Q열: 고잔가추가1 10,000
long_term_premium = 0.0
if premium_add_15k and isinstance(premium_add_15k, (int, float)):
    long_term_premium += float(premium_add_15k)
if premium_add_10k and isinstance(premium_add_10k, (int, float)):
    long_term_premium += float(premium_add_10k)

# APS 등급
if aps_grade:
    aps_normal = self._calculate_residual_for_vehicle(
        str(aps_grade), residual_tables.get('aps', {}), mileage_adjustments
    )
    if aps_normal:
        residual_data['aps_normal'] = aps_normal
        residual_data['aps_premium'] = self._apply_premium_adjustment(
            aps_normal, 0.08, long_term_premium
        )

# VGS 등급
if vgs_grade:
    vgs_normal = self._calculate_residual_for_vehicle(
        str(vgs_grade), residual_tables.get('vgs', {}), mileage_adjustments
    )
    if vgs_normal:
        residual_data['vgs_normal'] = vgs_normal
        residual_data['vgs_premium'] = self._apply_premium_adjustment(
            vgs_normal, 0.06, long_term_premium
        )
```

**차량별 프리미엄 적용 예시**:
```python
# BMW 520i: P=0.01, Q=0.01 → long_term_premium = 0.02
# → 36개월: 일반잔가 + 8%p
# → 48/60개월: 일반잔가 + 10%p (8% + 2%)

# GLB 250: P=None, Q=None → long_term_premium = 0.0
# → 모든 기간: 일반잔가 + 8%p
```

**검증**:
```python
# BMW X2 xDrive 20i M Mesh의 잔존율 (36개월)
{
  "aps_normal": {
    "36": {"20000": 0.55}   # 일반잔가
  },
  "aps_premium": {
    "36": {"20000": 0.63}   # 고잔가 = 0.55 + 0.08 ✅
  }
}

# BMW 520i의 잔존율 (장기 계약 프리미엄 포함)
{
  "aps_premium": {
    "36": {"20000": 0.715},  # 0.635 + 0.08 = 0.715 (36개월: 기본 프리미엄만)
    "48": {"20000": 0.655},  # 0.555 + 0.08 + 0.02 = 0.655 (48개월: 기본+장기)
    "60": {"20000": 0.595}   # 0.495 + 0.08 + 0.02 = 0.595 (60개월: 기본+장기) ✅
  }
}
```

---

### 문제 4: 데이터 구조 설계

**초기 설계**:
```json
{
  "BMW_X2_...": {
    "24": {"10000": 0.65, "15000": 0.63, ...},
    "36": {"10000": 0.55, "15000": 0.53, ...}
  }
}
```

**문제점**:
- 어떤 등급(West/APS/VGS)의 데이터인지 알 수 없음
- 고잔가/일반잔가 구분 불가능
- 사용자 선택 옵션 제공 불가

**최종 설계**:
```json
{
  "BMW_X2_...": {
    "west_normal": {
      "24": {"10000": 0.65, "15000": 0.63, ...},
      "36": {"10000": 0.52, ...}
    },
    "west_premium": {
      "24": {"10000": 0.73, ...},
      "36": {"10000": 0.60, ...}
    },
    "aps_normal": {
      "36": {"20000": 0.55}
    },
    "aps_premium": {
      "36": {"20000": 0.63}
    },
    "vgs_normal": {...},
    "vgs_premium": {...}
  }
}
```

**장점**:
- 명확한 옵션 구분
- UI에서 6가지 옵션 선택 가능
- Fallback 로직 구현 용이 (없는 옵션은 다른 옵션으로 대체)

---

## 최종 구현 내용

### 1. 클래스 구조

```python
class MeritzResidualExtractor:
    """메리츠캐피탈 엑셀에서 잔존율 데이터 추출"""

    def __init__(self, excel_path: str):
        """엑셀 파일 로드 및 시트 찾기"""

    def extract_all_vehicles(self) -> Tuple[Dict, Dict]:
        """메인 추출 함수"""
        # 1. 잔가 테이블 추출 (4개 시스템)
        # 2. 주행거리 조정값 추출
        # 3. 차량 정보 및 잔존율 계산

    def _extract_residual_tables(self) -> Dict[str, Dict]:
        """4개 캐피탈사의 잔가 테이블 추출"""

    def _parse_residual_table(self, ...) -> Dict:
        """특정 영역의 잔가 테이블 파싱"""

    def _extract_mileage_adjustments(self) -> Dict[int, float]:
        """주행거리별 조정값 추출"""

    def _extract_vehicles_with_residuals(self, ...) -> Tuple[Dict, Dict]:
        """차량 정보 및 잔존율 계산"""

    def _calculate_residual_for_vehicle(self, ...) -> Optional[Dict]:
        """특정 차량의 잔존율 계산"""

    def _apply_premium_adjustment(self, normal_data: Dict,
                                  premium_rate: float) -> Dict:
        """일반잔가에 고잔가 보정 적용"""

    def _normalize_vehicle_id(self, maker: str, model: str,
                              trim: str) -> str:
        """차량 ID 생성"""
```

### 2. 핵심 로직

#### 2.1 잔가 테이블 추출
```python
def _parse_residual_table(self, start_row: int, end_row: int,
                         grade_row: int, grade_col_start: int,
                         grade_col_end: int) -> Dict:
    table = {}

    # 1. 등급 헤더 읽기
    grade_header_cells = list(self.residual_sheet.iter_rows(
        min_row=grade_row, max_row=grade_row,
        min_col=grade_col_start, max_col=grade_col_end,
        values_only=True
    ))[0]

    # 첫 컬럼(기간) 제외하고 등급만 추출
    grades = [cell for cell in grade_header_cells[1:]
              if cell and isinstance(cell, str)]

    # 2. 기간별 데이터 읽기
    for row_idx in range(start_row, end_row):
        row_data = list(self.residual_sheet.iter_rows(
            min_row=row_idx, max_row=row_idx,
            min_col=grade_col_start, max_col=grade_col_end,
            values_only=True
        ))[0]

        period = row_data[0]  # 기간

        # 24, 36, 48, 60개월만 사용
        if period not in [24, 36, 48, 60]:
            continue

        table[period] = {}

        # 3. 등급별 잔존율 읽기
        for grade_idx, grade in enumerate(grades):
            rate_value = row_data[grade_idx + 1]
            if isinstance(rate_value, (int, float)) and 0 < rate_value <= 1:
                table[period][grade] = float(rate_value)

    return table
```

#### 2.2 차량별 잔존율 계산
```python
def _calculate_residual_for_vehicle(self, grade: str,
                                    residual_table: Dict,
                                    mileage_adjustments: Dict) -> Optional[Dict]:
    result = {}

    for period in [24, 36, 48, 60]:
        if period not in residual_table:
            continue

        if grade not in residual_table[period]:
            continue

        base_rate = residual_table[period][grade]
        result[period] = {}

        # 주행거리별 조정
        for mileage in [10000, 15000, 20000, 30000]:
            adjustment = mileage_adjustments.get(mileage, 0.0)
            adjusted_rate = base_rate + adjustment

            # 10% ~ 95% 범위로 제한
            result[period][mileage] = round(
                max(0.1, min(0.95, adjusted_rate)), 4
            )

    return result if result else None
```

#### 2.3 6개 옵션 생성
```python
residual_data = {}

# West 등급
if west_grade:
    west_normal = self._calculate_residual_for_vehicle(
        str(west_grade), residual_tables.get('west', {}), mileage_adjustments
    )
    if west_normal:
        residual_data['west_normal'] = west_normal
        residual_data['west_premium'] = self._apply_premium_adjustment(
            west_normal, 0.08
        )

# APS 등급
if aps_grade:
    aps_normal = self._calculate_residual_for_vehicle(
        str(aps_grade), residual_tables.get('aps', {}), mileage_adjustments
    )
    if aps_normal:
        residual_data['aps_normal'] = aps_normal
        residual_data['aps_premium'] = self._apply_premium_adjustment(
            aps_normal, 0.08
        )

# VGS 등급
if vgs_grade:
    vgs_normal = self._calculate_residual_for_vehicle(
        str(vgs_grade), residual_tables.get('vgs', {}), mileage_adjustments
    )
    if vgs_normal:
        residual_data['vgs_normal'] = vgs_normal
        residual_data['vgs_premium'] = self._apply_premium_adjustment(
            vgs_normal, 0.06
        )
```

### 3. 출력 데이터 구조

#### 3.1 vehicle_master.json
```json
{
  "BMW_X2_X2_XDRIVE_20I_M_MESH": {
    "brand": "BMW",
    "model": "X2",
    "trim": "X2 xDrive 20i M Mesh",
    "display_name": "BMW X2 xDrive 20i M Mesh",
    "price": 55900000,
    "engine_cc": 1998,
    "fuel_type": "가솔린",
    "is_import": true,
    "west_grade": "A",
    "aj_grade": null,
    "aps_grade": "H",
    "vgs_grade": null
  }
}
```

#### 3.2 residual_rates/meritz_capital.json
```json
{
  "BMW_X2_X2_XDRIVE_20I_M_MESH": {
    "west_normal": {
      "24": {"10000": 0.65, "15000": 0.63, "20000": 0.60, "30000": 0.55},
      "36": {"10000": 0.58, "15000": 0.55, "20000": 0.52, "30000": 0.47},
      "48": {"10000": 0.52, "15000": 0.49, "20000": 0.46, "30000": 0.41},
      "60": {"10000": 0.46, "15000": 0.43, "20000": 0.40, "30000": 0.35}
    },
    "west_premium": {
      "24": {"10000": 0.73, "15000": 0.71, "20000": 0.68, "30000": 0.63},
      "36": {"10000": 0.66, "15000": 0.63, "20000": 0.60, "30000": 0.55},
      "48": {"10000": 0.60, "15000": 0.57, "20000": 0.54, "30000": 0.49},
      "60": {"10000": 0.54, "15000": 0.51, "20000": 0.48, "30000": 0.43}
    },
    "aps_normal": {
      "24": {"10000": 0.68, "15000": 0.66, "20000": 0.63, "30000": 0.58},
      "36": {"10000": 0.61, "15000": 0.58, "20000": 0.55, "30000": 0.50},
      "48": {"10000": 0.55, "15000": 0.52, "20000": 0.49, "30000": 0.44},
      "60": {"10000": 0.49, "15000": 0.46, "20000": 0.43, "30000": 0.38}
    },
    "aps_premium": {
      "24": {"10000": 0.76, "15000": 0.74, "20000": 0.71, "30000": 0.66},
      "36": {"10000": 0.69, "15000": 0.66, "20000": 0.63, "30000": 0.58},
      "48": {"10000": 0.63, "15000": 0.60, "20000": 0.57, "30000": 0.52},
      "60": {"10000": 0.57, "15000": 0.54, "20000": 0.51, "30000": 0.46}
    }
  }
}
```

---

## 실행 방법

### 1. 명령행 실행
```bash
cd "/Users/dongyonglee/Desktop/financial intelligence v2"

python excel_reverse_engineering/meritz_extractor.py "xlsx/meritz_capital_2509_V1.xlsx"
```

### 2. 출력 예시
```
================================================================================
메리츠캐피탈 데이터 추출 시작
================================================================================

[1/3] 잔가 테이블 추출 중...
  ✓ 4개 캐피탈사 테이블 추출 완료

[2/3] 주행거리 조정값 추출 중...
  ✓ 주행거리 조정값: {10000: 0.03, 15000: 0.01, 20000: 0.0, 30000: -0.05}

[3/3] 차량 데이터 추출 중...
  ✓ 1041대 차량 처리 완료

✓ 저장: data/vehicle_master.json (1041대)
✓ 저장: data/residual_rates/meritz_capital.json (1010대)

================================================================================
추출 완료!
================================================================================
총 차량 수: 1041대
잔존율 데이터: 1010대
완전한 데이터 (4개 기간): 908대

샘플 데이터 (첫 3대):

  [1] BMW X2 xDrive 20i M Mesh
      가격: 55,900,000원
      등급: A (West), H (APS)
      잔존율: 4개월
      36개월/20,000km: 52.00% (West normal)
                        63.00% (APS premium) ⭐
```

---

## 검증 방법

### 1. BMW X2 검증 스크립트
```python
from data import vehicle_master, residual_rates

# 1. 차량 검색
vehicles = vehicle_master.search_vehicles('X2 xDrive 20i M Mesh')
vehicle_id = vehicles[0]['id']

print(f"차량 ID: {vehicle_id}")
print(f"가격: {vehicles[0]['price']:,}원")

# 2. 등급 확인
vehicle = vehicle_master.get_vehicle(vehicle_id)
print(f"West 등급: {vehicle['west_grade']}")
print(f"APS 등급: {vehicle['aps_grade']}")

# 3. 잔존율 확인
rate_aps_premium = residual_rates.get_residual_rate(
    'meritz_capital', vehicle_id, 36, 20000,
    grade_option='aps_premium'
)

rate_west_normal = residual_rates.get_residual_rate(
    'meritz_capital', vehicle_id, 36, 20000,
    grade_option='west_normal'
)

print(f"\n36개월 / 20,000km:")
print(f"  APS 고잔가: {rate_aps_premium:.1%}")  # 63.0% ✅
print(f"  West 일반: {rate_west_normal:.1%}")   # 52.0%

# 4. 엑셀과 비교
print(f"\n엑셀 최대잔가: 63.0%")
print(f"추출 APS 고잔가: {rate_aps_premium:.1%}")
print(f"일치 여부: {'✅ 일치' if abs(rate_aps_premium - 0.63) < 0.001 else '❌ 불일치'}")
```

### 2. 전체 데이터 통계
```python
import json
from pathlib import Path

# 차량 마스터 로드
with open('data/vehicle_master.json', 'r', encoding='utf-8') as f:
    vehicles = json.load(f)

# 잔존율 데이터 로드
with open('data/residual_rates/meritz_capital.json', 'r', encoding='utf-8') as f:
    residuals = json.load(f)

print(f"총 차량 수: {len(vehicles)}대")
print(f"잔존율 보유 차량: {len(residuals)}대")

# 등급 분포 확인
grade_counts = {
    'west': 0, 'aj': 0, 'aps': 0, 'vgs': 0
}

for vehicle_id, data in vehicles.items():
    if data.get('west_grade'):
        grade_counts['west'] += 1
    if data.get('aj_grade'):
        grade_counts['aj'] += 1
    if data.get('aps_grade'):
        grade_counts['aps'] += 1
    if data.get('vgs_grade'):
        grade_counts['vgs'] += 1

print(f"\n등급 분포:")
for grade, count in grade_counts.items():
    print(f"  {grade}: {count}대")

# 옵션별 차량 수
option_counts = {}
for vehicle_id, options in residuals.items():
    for option in options.keys():
        option_counts[option] = option_counts.get(option, 0) + 1

print(f"\n옵션별 차량 수:")
for option, count in sorted(option_counts.items()):
    print(f"  {option}: {count}대")
```

### 3. 특정 차량 상세 검증
```python
import json

vehicle_id = 'BMW_X2_X2_XDRIVE_20I_M_MESH'

# 엑셀에서 수동으로 확인한 값
EXPECTED = {
    'west_grade': 'A',
    'aps_grade': 'H',
    'aps_premium_36_20000': 0.63,
    'west_normal_36_20000': 0.52
}

# 추출된 데이터 로드
with open('data/vehicle_master.json', 'r') as f:
    vehicles = json.load(f)

with open('data/residual_rates/meritz_capital.json', 'r') as f:
    residuals = json.load(f)

# 검증
vehicle = vehicles[vehicle_id]
residual = residuals[vehicle_id]

print("=== BMW X2 xDrive 20i M Mesh 검증 ===\n")

# 등급 검증
assert vehicle['west_grade'] == EXPECTED['west_grade'], \
    f"West 등급 불일치: {vehicle['west_grade']} != {EXPECTED['west_grade']}"
print(f"✅ West 등급: {vehicle['west_grade']}")

assert vehicle['aps_grade'] == EXPECTED['aps_grade'], \
    f"APS 등급 불일치: {vehicle['aps_grade']} != {EXPECTED['aps_grade']}"
print(f"✅ APS 등급: {vehicle['aps_grade']}")

# 잔존율 검증
aps_premium_rate = residual['aps_premium']['36']['20000']
assert abs(aps_premium_rate - EXPECTED['aps_premium_36_20000']) < 0.001, \
    f"APS 고잔가 불일치: {aps_premium_rate} != {EXPECTED['aps_premium_36_20000']}"
print(f"✅ APS 고잔가 (36/20k): {aps_premium_rate:.1%}")

west_normal_rate = residual['west_normal']['36']['20000']
assert abs(west_normal_rate - EXPECTED['west_normal_36_20000']) < 0.001, \
    f"West 일반 불일치: {west_normal_rate} != {EXPECTED['west_normal_36_20000']}"
print(f"✅ West 일반 (36/20k): {west_normal_rate:.1%}")

print("\n🎉 모든 검증 통과!")
```

---

## 향후 업데이트 시 체크리스트

메리츠에서 업데이트된 엑셀 견적기를 받았을 때 다음 순서로 확인:

### 1. 엑셀 구조 변경 확인

#### ✅ "차종" 시트
- [ ] 시트 이름 동일 여부 확인
- [ ] 데이터 시작 Row (현재: Row 7)
- [ ] 컬럼 위치 변경 여부:
  ```
  - [ ] B(2): Maker
  - [ ] C(3): Model1
  - [ ] E(5): Model3
  - [ ] F(6): 차량가격
  - [ ] G(7): 배기량
  - [ ] H(8): 유종
  - [ ] J(10): West 등급
  - [ ] K(11): AJ 등급
  - [ ] L(12): APS 등급
  - [ ] M(13): VGS 등급
  - [ ] P(16): 고잔가추가 15,000 (장기 프리미엄) ⭐
  - [ ] Q(17): 고잔가추가1 10,000 (장기 프리미엄) ⭐
  ```
- [ ] 새로운 컬럼 추가 여부 확인

#### ✅ "잔가" 시트
- [ ] 시트 이름 동일 여부 확인
- [ ] 주행거리 조정값 위치 (현재: Row 36-39, Col I-J)
- [ ] 캐피탈사 테이블 위치:
  ```
  - [ ] West: Row 48-54, Col B-M
  - [ ] AJ: Row 57-63, Col B-W
  - [ ] APS: Row 65-71, Col B-X
  - [ ] VGS: Row 73-78, Col B-L
  ```
- [ ] 새로운 캐피탈사 추가 여부
- [ ] 기간 변경 (현재: 24, 36, 48, 60개월)

### 2. 샘플 차량으로 수동 검증

BMW X2 또는 다른 대표 차량 1대 선정:

- [ ] 엑셀에서 육안으로 확인:
  - 제조사, 모델명, 가격
  - West, AJ, APS, VGS 등급
  - 36개월/20,000km 조건의 일반잔가/고잔가
- [ ] 추출 후 JSON 파일에서 동일 차량 확인
- [ ] 모든 값이 일치하는지 검증

### 3. 코드 수정 필요 여부 판단

#### 컬럼 위치 변경 시
```python
# meritz_extractor.py:_extract_vehicles_with_residuals()
maker = row_data[1]        # 변경 필요 시 인덱스 수정
model1 = row_data[2]
model3 = row_data[4]
# ...
west_grade = row_data[9]   # 위치 변경 확인
aps_grade = row_data[11]   # 위치 변경 확인
```

#### 테이블 위치 변경 시
```python
# meritz_extractor.py:_extract_residual_tables()
tables['west'] = self._parse_residual_table(
    start_row=49,    # 변경 필요 시 수정
    end_row=54,
    grade_row=48,
    grade_col_start=2,
    grade_col_end=13
)
```

#### 새로운 캐피탈사 추가 시
```python
# 새 캐피탈 추가 (예: "KB")
tables['kb'] = self._parse_residual_table(
    start_row=81,  # 새 테이블 위치
    end_row=86,
    grade_row=80,
    grade_col_start=2,
    grade_col_end=15
)

# 차량 데이터 추출에서 KB 등급 추가
kb_grade = row_data[14]  # 새 컬럼 인덱스

# KB 옵션 생성
if kb_grade:
    kb_normal = self._calculate_residual_for_vehicle(...)
    residual_data['kb_normal'] = kb_normal
    residual_data['kb_premium'] = self._apply_premium_adjustment(kb_normal, 0.08)
```

### 4. 고잔가 보정율 및 장기 프리미엄 확인

엑셀에서 일반잔가와 고잔가를 비교하여 보정율 확인:

**기본 보정율 (36개월 기준):**
- [ ] APS 고잔가 = 일반잔가 + ? %p (현재: +8%p)
- [ ] VGS 고잔가 = 일반잔가 + ? %p (현재: +6%p)
- [ ] West 고잔가 = 일반잔가 + ? %p (현재: +8%p)

**장기 계약 추가 프리미엄 (48/60개월):**
- [ ] P열(고잔가추가 15,000) 확인 → 값이 있으면 해당 비율 추가
- [ ] Q열(고잔가추가1 10,000) 확인 → 값이 있으면 해당 비율 추가
- [ ] 특정 차량에만 장기 프리미엄 적용 여부 확인

보정율 변경 시:
```python
# meritz_extractor.py:_extract_vehicles_with_residuals()
# P/Q열에서 장기 프리미엄 추출
long_term_premium = 0.0
if premium_add_15k:
    long_term_premium += float(premium_add_15k)
if premium_add_10k:
    long_term_premium += float(premium_add_10k)

# 기본 보정율 + 장기 프리미엄 적용
residual_data['aps_premium'] = self._apply_premium_adjustment(
    aps_normal, 0.08, long_term_premium
)
```

### 5. 추출 및 검증

```bash
# 1. 추출 실행
python excel_reverse_engineering/meritz_extractor.py "xlsx/NEW_FILE.xlsx"

# 2. 통계 확인
# - 총 차량 수가 합리적인가?
# - 잔존율 보유 차량이 충분한가? (목표: 90% 이상)
# - 완전한 데이터(4개 기간)가 충분한가?

# 3. BMW X2 검증
python -c "
from data import vehicle_master, residual_rates

vehicles = vehicle_master.search_vehicles('X2 20i M Mesh')
if vehicles:
    vid = vehicles[0]['id']
    rate = residual_rates.get_residual_rate(
        'meritz_capital', vid, 36, 20000,
        grade_option='aps_premium'
    )
    print(f'APS 고잔가: {rate:.1%}')
    print(f'엑셀과 일치: {abs(rate - 0.63) < 0.001}')
"

# 4. 전체 앱 테스트
streamlit run app.py
# - BMW X2 선택
# - 잔가 옵션: APS 고잔가 (최대)
# - 36개월 / 20,000km
# - 63% 표시 확인
```

### 6. Git 커밋

```bash
git add data/vehicle_master.json
git add data/residual_rates/meritz_capital.json
git add excel_reverse_engineering/meritz_extractor.py  # 수정한 경우

git commit -m "chore: 메리츠 엑셀 데이터 업데이트 (YYYY-MM)

- 차량 데이터: X대
- 잔존율 보유: X대
- 엑셀 버전: meritz_capital_YYMM_VX.xlsx
- 검증: BMW X2 63% 일치 ✅
"

git push
```

---

## 🚨 주의사항

### 1. 절대 하지 말아야 할 것

**❌ 컬럼 번호를 그대로 사용하지 말 것**
```python
# WRONG!
west_grade = row_data[10]  # J 컬럼이 아니라 K 컬럼을 읽음
```

**올바른 방법**:
```python
# CORRECT
west_grade = row_data[9]   # J 컬럼 = 10번째 = 배열 인덱스 9
```

**❌ 고잔가 보정을 곱셈으로 하지 말 것**
```python
# WRONG! (8% 증가가 아니라 8%p 증가임)
premium_rate = normal_rate * 1.08
```

**올바른 방법**:
```python
# CORRECT
premium_rate = normal_rate + 0.08  # +8%p (percentage point)
```

### 2. 반드시 확인할 것

- ✅ BMW X2 같은 대표 차량으로 엑셀과 비교 검증
- ✅ 추출된 차량 수가 엑셀의 차량 수와 비슷한지 확인
- ✅ 잔존율 데이터가 90% 이상 차량에 존재하는지 확인
- ✅ 등급 컬럼 인덱스를 절대 추측하지 말고, 실제 엑셀로 확인

### 3. 트러블슈팅

**증상**: 추출된 등급이 엑셀과 다름
→ 컬럼 인덱스 오류. 엑셀 컬럼 위치 재확인 필요

**증상**: 잔존율이 너무 낮거나 높음
→ 고잔가/일반잔가 혼동 또는 보정율 오류

**증상**: 잔존율 데이터가 거의 없음 (10% 미만)
→ 테이블 위치 오류. "잔가" 시트의 Row/Col 재확인

**증상**: 특정 등급만 누락됨
→ 해당 등급 테이블의 위치 확인 필요

---

## 📚 참고 자료

### 관련 파일
- `excel_reverse_engineering/meritz_extractor.py`: 추출기 소스
- `data/residual_rates.py`: 잔존율 로더 (grade_option 지원)
- `app.py`: Streamlit UI (잔가 옵션 선택)
- `tools/excel_validator.py`: 엑셀 검증 도구

### 검증 스크립트
- `tests/test_data_loaders.py`: 데이터 로더 테스트
- `tests/test_calculator_integration.py`: 계산 통합 테스트

### 문서
- `docs/IMPLEMENTATION_SUMMARY.md`: 전체 프로젝트 요약
- `QUICK_START.md`: 빠른 시작 가이드
- `README.md`: 프로젝트 개요

---

**작성일**: 2025-11-06
**최종 업데이트**: 2025-11-06 (장기 계약 프리미엄 추가)
**최종 검증**:
- BMW X2 xDrive 20i M Mesh: 36개월 63% ✅
- BMW 520i: 48개월 65.5%, 60개월 59.5% ✅
- GLB 250 4MATIC: 48개월 59.0%, 60개월 53.0% ✅

**데이터 버전**: meritz_capital_2509_V1.xlsx
