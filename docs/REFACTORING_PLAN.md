# 리스 계산기 리팩토링 플랜

## 📋 목차
1. [Executive Summary](#executive-summary)
2. [현재 상황 분석 (As-Is)](#현재-상황-분석-as-is)
3. [문제점 식별](#문제점-식별)
4. [목표 및 방향성 (To-Be)](#목표-및-방향성-to-be)
5. [리팩토링 솔루션](#리팩토링-솔루션)
6. [마이그레이션 계획](#마이그레이션-계획)
7. [예상 효과 및 ROI](#예상-효과-및-roi)

---

## Executive Summary

### 배경
현재 2개 캐피탈(메리츠, MG)로 운영 중인 리스 계산기를 17개 캐피탈로 확장 예정입니다. 현재 아키텍처로는 확장 시 유지보수 비용이 기하급수적으로 증가할 것으로 예상됩니다.

### 핵심 문제
- **확장성**: 하드코딩된 if/else 구조로 새 캐피탈 추가 시 5곳 이상 수정 필요
- **복잡도**: 2개 → 17개 확장 시 코드 복잡도 O(n²) 증가
- **유지보수**: 한 캐피탈 수정 시 다른 캐피탈에 영향 가능

### 제안 솔루션
**플러그인 아키텍처 도입**: 각 캐피탈을 독립적인 플러그인으로 구현하여 확장성과 유지보수성을 획기적으로 개선합니다.

### 예상 효과
- 새 캐피탈 추가 시간: **2-3일 → 2-3시간** (10배 개선)
- 코드 복잡도: **O(n²) → O(n)** (선형 복잡도)
- 유지보수 비용: **70% 감소**

---

## 현재 상황 분석 (As-Is)

### 1. 현재 아키텍처

```
financial-intelligence-v2/
├── app.py                        (600+ lines, 모든 로직 포함)
├── data/
│   ├── vehicle_master.py         (차량 마스터 + 매칭 로직)
│   ├── vehicle_master.json       (메리츠 차량)
│   ├── mg_vehicle_master.json    (MG 차량)
│   ├── master_carinfo.json       (신뢰 기준 가격)
│   └── residual_rates/
│       ├── meritz_capital.json   (메리츠 잔존율)
│       └── mg_capital.json       (MG 잔존율)
├── core/
│   ├── lease_calculator.py       (메리츠 계산기)
│   ├── mg_calculator.py          (MG 계산기)
│   └── residual_rates.py         (잔존율 조회)
└── tools/
    └── interest_rates.py         (금리 조회)
```

### 2. 주요 컴포넌트 분석

#### app.py (600+ lines)
```python
# 현재 구조
if capital == "meritz_capital":
    # 메리츠 전용 로직 (100+ lines)
    annual_car_tax = calculate_auto_tax(...)
    acquisition_tax = taxable_base * 0.07
    result = calculate_operating_lease(...)

elif capital == "mg_capital":
    # MG 전용 로직 (100+ lines)
    mg_calc = MGLeaseCalculator()
    mg_result = mg_calc.calculate(...)

elif capital == "compare":
    # 비교 로직 (200+ lines)
    for cap_id in available_capitals:
        if cap_id == "mg_capital":
            # MG 로직 반복
        else:
            # 메리츠 로직 반복
```

**문제점**:
- 모든 캐피탈 로직이 한 파일에 집중
- 로직 중복 (단일 모드와 비교 모드에서 동일 로직 반복)
- 새 캐피탈 추가 시 3곳 수정 필요 (단일/비교/에러처리)

#### vehicle_master.py (400+ lines)
```python
def find_vehicle_by_name(brand, model, trim, capital_id=None):
    vehicles = _load_vehicles(capital_id)

    # 매칭 로직 (100+ lines)
    # 1. 정확한 매칭
    # 2. 모델명 제거 후 재시도
    # 3. 부분 매칭
    # 4. 한글/영어 변환

    return None

def get_price_from_master(brand, model, grade):
    # 정규화 및 매칭 (150+ lines)
    # - 브랜드 변환 (아우디 → AUDI)
    # - 단어 변환 (프리미엄 → PREMIUM)
    # - 숫자 추출 및 비교

    return price
```

**문제점**:
- 차량 매칭과 가격 조회가 혼재
- 정규화 로직이 함수 내부에 하드코딩
- 캐피탈별 매칭 설정 불가능

#### core/mg_calculator.py (285 lines)
```python
class MGLeaseCalculator:
    def calculate(self, vehicle_price, residual_rate, ...):
        # 취득원가 계산
        acquisition_cost_details = self._calculate_acquisition_cost(...)

        # PMT 계산
        monthly_payment = -npf.pmt(...)

        return {
            "monthly_payment": monthly_payment,
            "down_payment": down_payment,
            ...
        }

    def _calculate_acquisition_cost(self, vehicle_price, region, ...):
        # MG 전용 취득원가 로직
        ...
```

**장점**:
- ✅ 클래스 기반 구조
- ✅ 메서드 분리

**문제점**:
- 표준 인터페이스 없음 (메리츠와 다른 구조)
- 설정이 코드에 하드코딩

#### core/lease_calculator.py
```python
def calculate_operating_lease(vehicle_price, contract_months, ...):
    # 메리츠 전용 계산 (함수 기반)
    depreciation = (acquisition_cost - residual_value) / contract_months
    interest = ((acquisition_cost + residual_value) / 2) * (annual_rate / 12)

    return {
        "monthly_total": depreciation + interest + monthly_car_tax,
        ...
    }
```

**문제점**:
- 함수 기반 (MG는 클래스 기반)
- 인터페이스 불일치

### 3. 데이터 흐름 (현재)

```
사용자 입력 (app.py)
    ↓
차량 선택
    ↓
capital 분기 (if/elif)
    ↓
┌─────────────┬─────────────┐
│  메리츠     │     MG      │
│             │             │
│ 1. 차량 매칭 │ 1. 차량 매칭 │
│    (직접)   │    (직접)   │
│             │             │
│ 2. 가격 조회 │ 2. 가격 조회 │
│  master_   │  master_   │
│  carinfo   │  carinfo   │
│             │             │
│ 3. 잔존율   │ 3. 잔존율   │
│  조회       │  조회       │
│             │             │
│ 4. 계산     │ 4. 계산     │
│  (함수)     │  (클래스)   │
└─────────────┴─────────────┘
    ↓
결과 표시
```

---

## 문제점 식별

### 1. 확장성 문제 (Critical)

#### 현재 상황
```python
# app.py에서 3곳 수정 필요
# 1. 캐피탈 선택 옵션
capital_options = ["meritz_capital", "nh_capital", "mg_capital"]  # +14개 추가

# 2. 단일 계산 로직
if capital == "meritz_capital":
    # 100 lines
elif capital == "nh_capital":
    # 100 lines
elif capital == "mg_capital":
    # 100 lines
# ... +14개 elif 추가 (1400+ lines!)

# 3. 비교 계산 로직
for cap_id in available_capitals:
    if cap_id == "mg_capital":
        # 100 lines
    else:
        # 100 lines
    # ... +14개 분기
```

#### 문제
- **코드량 폭발**: 17개 × 100 lines × 2곳 = **3,400+ lines**
- **O(n²) 복잡도**: 캐피탈 수 증가에 따라 분기 수 기하급수 증가
- **에러 가능성**: 각 분기마다 복사-붙여넣기로 인한 실수 가능

### 2. 유지보수성 문제 (High)

#### 문제 시나리오
메리츠 캐피탈의 취득세 계산 로직 변경 필요:
```python
# 변경 필요 위치
1. app.py: 단일 모드 (line 350)
2. app.py: 비교 모드 (line 550)
3. core/lease_calculator.py (line 45)
4. 테스트 코드 (여러 곳)

→ 4곳 이상 수정 필요, 한 곳이라도 놓치면 버그 발생
```

#### 통계
- 현재 2개 캐피탈: **평균 3-4곳 수정**
- 17개 캐피탈 예상: **평균 10-15곳 수정**
- 에러 발생 확률: **70% 이상**

### 3. 일관성 문제 (High)

#### 인터페이스 불일치
```python
# 메리츠 (함수 기반)
result = calculate_operating_lease(
    vehicle_price=price,
    contract_months=months,
    ...
)
# → result['monthly_total']

# MG (클래스 기반)
calc = MGLeaseCalculator()
result = calc.calculate(
    vehicle_price=price,
    residual_rate=rate,
    ...
)
# → result['monthly_payment']
```

#### 문제
- 반환값 구조 다름: `monthly_total` vs `monthly_payment`
- 호출 방법 다름: 함수 vs 클래스
- 매개변수 순서 다름

### 4. 테스트 어려움 (Medium)

#### 현재 테스트 구조
```python
# app.py를 테스트하려면 모든 캐피탈을 mock해야 함
def test_comparison():
    # 메리츠 mock
    # MG mock
    # UI mock
    # 데이터 mock
    # ... (복잡도 매우 높음)
```

#### 문제
- 단위 테스트 불가능 (모든 것이 결합됨)
- 통합 테스트만 가능 (느리고 불안정)
- 특정 캐피탈만 테스트 불가

### 5. 데이터 관리 문제 (Medium)

#### 현재 구조
```
data/
├── vehicle_master.json        (메리츠 전용?)
├── mg_vehicle_master.json     (MG 전용)
├── master_carinfo.json        (공통)
└── residual_rates/
    ├── meritz_capital.json
    └── mg_capital.json
```

#### 문제
- 캐피탈별 데이터 위치 불명확
- 설정(config)과 데이터(residual_rates) 분리 안 됨
- 17개 확장 시 파일 구조 파악 어려움

### 6. 학습한 문제 패턴

#### 실제 발생한 문제들
1. **차량 매칭 실패**
   - 원인: 캐피탈마다 다른 데이터 구조
   - 해결: 정규화 로직 추가
   - 문제: 하드코딩되어 있어 확장 어려움

2. **가격 불일치**
   - 원인: 캐피탈별 차량 가격 상이
   - 해결: master_carinfo 통합
   - 문제: 매칭 로직이 여전히 캐피탈마다 중복

3. **트림명 차이**
   - 원인: "A3 40 TFSI" vs "40 TFSI"
   - 해결: 모델명 prefix 제거
   - 문제: 캐피탈별 설정 불가

---

## 목표 및 방향성 (To-Be)

### 1. 핵심 원칙

#### SOLID 원칙 적용
1. **Single Responsibility**: 각 클래스는 하나의 책임만
2. **Open/Closed**: 확장에 열려있고 수정에 닫혀있음
3. **Liskov Substitution**: 캐피탈 교체 가능
4. **Interface Segregation**: 필요한 인터페이스만 구현
5. **Dependency Inversion**: 추상화에 의존

#### 설계 철학
1. **Convention over Configuration**: 규칙 기반 자동화
2. **Plugin Architecture**: 플러그인으로 확장
3. **Separation of Concerns**: 데이터/로직/UI 분리
4. **Single Source of Truth**: master_carinfo가 절대 기준

### 2. 목표 지표

| 항목 | 현재 (2개) | 목표 (17개) | 개선율 |
|------|-----------|------------|--------|
| 새 캐피탈 추가 시간 | 2-3일 | 2-3시간 | **90% 감소** |
| 코드 수정 위치 | 5곳 | 1곳 | **80% 감소** |
| app.py 라인 수 | 600+ | 200 | **67% 감소** |
| 테스트 커버리지 | 0% | 80%+ | **신규** |
| 버그 발생률 | 높음 | 낮음 | **70% 감소** |

### 3. 기대 효과

#### 개발자 경험
- ✅ 새 캐피탈 추가가 매우 쉬움 (3개 파일만)
- ✅ 기존 코드 수정 없이 확장 가능
- ✅ 각 캐피탈 독립적으로 개발/테스트

#### 유지보수성
- ✅ 한 캐피탈 수정이 다른 곳에 영향 없음
- ✅ 버그 발생 시 영향 범위 명확
- ✅ 코드 리뷰 범위 축소

#### 확장성
- ✅ 17개 → 100개 확장 가능
- ✅ 새 비즈니스 로직 추가 용이
- ✅ 다른 프로젝트 재사용 가능

---

## 리팩토링 솔루션

### 1. 새로운 아키텍처

```
financial-intelligence-v2/
├── app.py                          (200 lines, UI만)
├── data/
│   ├── master_carinfo.json         ⭐ Single Source of Truth
│   └── capitals/                   ⭐ 캐피탈별 데이터
│       ├── meritz/
│       │   ├── config.json         (메타데이터)
│       │   ├── residual_rates.json (잔존율)
│       │   └── grade_mapping.json  (등급 매핑)
│       ├── mg/
│       │   └── ... (동일 구조)
│       └── [15개 더]
├── core/
│   ├── base_calculator.py          ⭐ 추상 기본 클래스
│   ├── calculators/                ⭐ 플러그인
│       ├── meritz_calculator.py
│       ├── mg_calculator.py
│       └── [15개 더]
│   └── registry.py                 ⭐ 플러그인 레지스트리
├── services/
│   ├── vehicle_matching.py         ⭐ 차량 매칭 서비스
│   ├── residual_rate.py            ⭐ 잔존율 조회 서비스
│   └── comparison.py               ⭐ 비교 서비스
├── tests/
│   └── capitals/
│       ├── test_meritz.py
│       ├── test_mg.py
│       └── [15개 더]
└── docs/
    ├── REFACTORING_PLAN.md         (본 문서)
    ├── PLUGIN_GUIDE.md             (플러그인 개발 가이드)
    └── API_REFERENCE.md            (API 문서)
```

### 2. 핵심 컴포넌트 설계

#### 2.1 BaseCapitalCalculator (추상 클래스)

```python
# core/base_calculator.py
from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class CalculationInput:
    """표준화된 입력"""
    vehicle_price: int
    residual_rate: float
    contract_months: int
    annual_mileage: int
    annual_interest_rate: float
    down_payment_rate: float = 0.0
    region: str = "서울"
    is_ev: bool = False
    is_hybrid: bool = False
    company_lease: bool = False

@dataclass
class CalculationResult:
    """표준화된 출력"""
    monthly_payment: int
    down_payment: int
    total_payment: int
    residual_value: int
    acquisition_cost: int
    breakdown: Dict
    metadata: Dict

class BaseCapitalCalculator(ABC):
    """모든 캐피탈 계산기의 기본 클래스"""

    def __init__(self, capital_id: str):
        self.capital_id = capital_id
        self.data_dir = Path(f"data/capitals/{capital_id}")

        # 설정 로드
        self.config = self._load_json("config.json")
        self.residual_rates = self._load_json("residual_rates.json")
        self.grade_mapping = self._load_json("grade_mapping.json")

    @abstractmethod
    def calculate(self, input_data: CalculationInput) -> CalculationResult:
        """
        리스료 계산 (각 캐피탈 구현 필요)

        Args:
            input_data: 표준화된 입력

        Returns:
            표준화된 계산 결과
        """
        pass

    @abstractmethod
    def _calculate_acquisition_cost(
        self,
        vehicle_price: int,
        **kwargs
    ) -> Dict:
        """
        취득원가 계산 (캐피탈마다 다름)

        Returns:
            {
                'acquisition_tax': int,
                'bond_cost': int,
                'registration_fee': int,
                'total': int
            }
        """
        pass

    def get_residual_rate(
        self,
        vehicle_id: str,
        months: int,
        mileage: int,
        grade_option: str
    ) -> float:
        """
        잔존율 조회 (기본 구현 제공, 오버라이드 가능)

        Args:
            vehicle_id: 차량 ID
            months: 계약 개월수
            mileage: 연간 주행거리
            grade_option: 등급 옵션 (예: 'aps_premium')

        Returns:
            잔존율 (0~1)
        """
        if vehicle_id not in self.residual_rates:
            raise ValueError(f"차량 잔존율 없음: {vehicle_id}")

        vehicle_rates = self.residual_rates[vehicle_id]

        if grade_option not in vehicle_rates:
            raise ValueError(f"등급 옵션 없음: {grade_option}")

        grade_rates = vehicle_rates[grade_option]

        if months not in grade_rates:
            raise ValueError(f"계약 기간 없음: {months}개월")

        month_rates = grade_rates[months]

        if mileage not in month_rates:
            raise ValueError(f"주행거리 없음: {mileage}km")

        return month_rates[mileage]

    def get_available_grade_options(self, vehicle_id: str) -> List[str]:
        """차량이 지원하는 등급 옵션 목록"""
        if vehicle_id not in self.residual_rates:
            return []
        return list(self.residual_rates[vehicle_id].keys())

    def get_display_name(self) -> str:
        """캐피탈 표시 이름"""
        return self.config.get('display_name', self.capital_id)

    def supports_feature(self, feature: str) -> bool:
        """기능 지원 여부"""
        return feature in self.config.get('supported_features', [])

    def _load_json(self, filename: str) -> Dict:
        """JSON 파일 로드"""
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"파일 없음: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
```

#### 2.2 MeritzCapitalCalculator (구현 예시)

```python
# core/calculators/meritz_calculator.py
from core.base_calculator import (
    BaseCapitalCalculator,
    CalculationInput,
    CalculationResult
)

class MeritzCapitalCalculator(BaseCapitalCalculator):
    """메리츠캐피탈 계산기"""

    def calculate(self, input_data: CalculationInput) -> CalculationResult:
        """메리츠 정액법 계산"""

        # 1. 취득원가
        acq_cost = self._calculate_acquisition_cost(
            vehicle_price=input_data.vehicle_price,
            region=input_data.region,
            is_ev=input_data.is_ev,
            is_hybrid=input_data.is_hybrid
        )

        # 2. 선납금
        down_payment = int(acq_cost['total'] * input_data.down_payment_rate)

        # 3. 잔존가치
        residual_value = int(input_data.vehicle_price * input_data.residual_rate)

        # 4. 감가상각
        depreciation = (acq_cost['total'] - residual_value) / input_data.contract_months

        # 5. 금융비용
        interest = ((acq_cost['total'] + residual_value) / 2) * \
                   (input_data.annual_interest_rate / 12)

        # 6. 자동차세
        annual_car_tax = self._calculate_car_tax(
            input_data.vehicle_price,
            input_data.is_ev
        )
        monthly_car_tax = annual_car_tax / 12

        # 7. 월 납입료
        monthly_payment = int(depreciation + interest + monthly_car_tax)

        # 8. 총 납부액
        total_payment = down_payment + (monthly_payment * input_data.contract_months)

        return CalculationResult(
            monthly_payment=monthly_payment,
            down_payment=down_payment,
            total_payment=total_payment,
            residual_value=residual_value,
            acquisition_cost=acq_cost['total'],
            breakdown={
                'vehicle_price': input_data.vehicle_price,
                'acquisition_tax': acq_cost['acquisition_tax'],
                'bond_cost': acq_cost['bond_cost'],
                'registration_fee': acq_cost['registration_fee'],
                'monthly_depreciation': int(depreciation),
                'monthly_interest': int(interest),
                'monthly_car_tax': int(monthly_car_tax),
                'residual_rate': input_data.residual_rate,
                'annual_interest_rate': input_data.annual_interest_rate,
                'contract_months': input_data.contract_months,
                'annual_mileage': input_data.annual_mileage
            },
            metadata={
                'calculation_method': 'straight_line',
                'capital_id': self.capital_id
            }
        )

    def _calculate_acquisition_cost(
        self,
        vehicle_price: int,
        region: str,
        is_ev: bool,
        is_hybrid: bool
    ) -> Dict:
        """메리츠 취득원가 계산"""

        # 취득세
        taxable_base = vehicle_price / 1.1
        tax_rate = self.config['acquisition_tax_config']['base_rate']

        if is_ev:
            tax_rate = 0.07  # 전기차 감면 적용
            full_tax = taxable_base * tax_rate
            discount = min(
                taxable_base * 0.04,
                self.config['acquisition_tax_config']['ev_reduction']
            )
            acquisition_tax = max(full_tax - discount, 0)
        elif is_hybrid:
            tax_rate = self.config['acquisition_tax_config']['hybrid_rate']
            acquisition_tax = taxable_base * tax_rate
        else:
            acquisition_tax = taxable_base * tax_rate

        acquisition_tax = int(acquisition_tax // 10 * 10)  # 10원 단위 내림

        # 공채 (메리츠는 0)
        bond_cost = 0

        # 등록비
        registration_fee = self.config.get('registration_fee', 100000)

        # 합계
        total = vehicle_price + acquisition_tax + bond_cost + registration_fee

        return {
            'acquisition_tax': acquisition_tax,
            'bond_cost': bond_cost,
            'registration_fee': registration_fee,
            'total': total
        }

    def _calculate_car_tax(self, vehicle_price: int, is_ev: bool) -> int:
        """자동차세 계산"""
        if is_ev:
            return self.config.get('ev_car_tax', 130000)
        else:
            return int(vehicle_price * 0.0132)
```

#### 2.3 CapitalRegistry (플러그인 관리)

```python
# core/registry.py
from typing import Dict, List, Optional
from pathlib import Path
import importlib
import json

from core.base_calculator import BaseCapitalCalculator

class CapitalRegistry:
    """캐피탈 플러그인 레지스트리 (싱글톤)"""

    _instance = None
    _calculators: Dict[str, BaseCapitalCalculator] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._calculators:
            self._load_all_calculators()

    def _load_all_calculators(self):
        """모든 캐피탈 플러그인 자동 로드"""
        capitals_dir = Path("data/capitals")

        if not capitals_dir.exists():
            print(f"⚠️ 캐피탈 디렉토리 없음: {capitals_dir}")
            return

        for capital_dir in capitals_dir.iterdir():
            if not capital_dir.is_dir():
                continue

            config_path = capital_dir / "config.json"
            if not config_path.exists():
                print(f"⚠️ config.json 없음: {capital_dir.name}")
                continue

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # 비활성화된 캐피탈 건너뛰기
                if not config.get('enabled', False):
                    print(f"⏸️ 비활성화됨: {config.get('display_name', capital_dir.name)}")
                    continue

                capital_id = config['capital_id']

                # 동적으로 모듈 로드
                module_name = f"core.calculators.{capital_id}_calculator"
                class_name = self._get_class_name(capital_id)

                module = importlib.import_module(module_name)
                calculator_class = getattr(module, class_name)

                # 인스턴스 생성 및 등록
                self._calculators[capital_id] = calculator_class(capital_id)

                print(f"✅ 로드 완료: {config.get('display_name', capital_id)}")

            except Exception as e:
                print(f"❌ {capital_dir.name} 로드 실패: {e}")
                import traceback
                traceback.print_exc()

    def get_calculator(self, capital_id: str) -> BaseCapitalCalculator:
        """캐피탈 계산기 가져오기"""
        if capital_id not in self._calculators:
            raise ValueError(
                f"❌ 캐피탈을 찾을 수 없습니다: {capital_id}\n"
                f"사용 가능: {list(self._calculators.keys())}"
            )
        return self._calculators[capital_id]

    def get_all_capitals(self) -> List[str]:
        """활성화된 모든 캐피탈 ID 목록"""
        return list(self._calculators.keys())

    def get_display_names(self) -> Dict[str, str]:
        """캐피탈 ID → 표시 이름 매핑"""
        return {
            cap_id: calc.get_display_name()
            for cap_id, calc in self._calculators.items()
        }

    def is_available(self, capital_id: str) -> bool:
        """캐피탈 사용 가능 여부"""
        return capital_id in self._calculators

    def reload(self):
        """플러그인 재로드 (개발용)"""
        self._calculators.clear()
        self._load_all_calculators()

    def _get_class_name(self, capital_id: str) -> str:
        """
        클래스 이름 생성

        예: meritz_capital → MeritzCapitalCalculator
        """
        parts = capital_id.split('_')
        return ''.join(p.capitalize() for p in parts) + 'Calculator'

# 싱글톤 인스턴스
registry = CapitalRegistry()
```

#### 2.4 VehicleMatchingService (차량 매칭 분리)

```python
# services/vehicle_matching.py
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path
import json
import re

@dataclass
class VehicleMatchConfig:
    """차량 매칭 설정"""
    trim_includes_model: bool = False
    case_sensitive: bool = False
    fuzzy_match: bool = True
    brand_translations: Dict[str, str] = None
    word_translations: Dict[str, str] = None

@dataclass
class MatchedVehicle:
    """매칭된 차량 정보"""
    vehicle_id: str
    price: int
    grade_info: Dict
    metadata: Dict

class VehicleNameNormalizer:
    """차량명 정규화"""

    BRAND_MAP = {
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

    WORD_MAP = {
        "시리즈": "SERIES",
        "베이스": "BASE",
        "스포츠": "SPORT",
        "프리미엄": "PREMIUM",
        "럭셔리": "LUXURY",
        "시그니처": "SIGNATURE",
        "익스클루시브": "EXCLUSIVE"
    }

    def normalize_brand(self, brand: str) -> str:
        """브랜드명 정규화"""
        brand_upper = brand.upper()
        return self.BRAND_MAP.get(brand_upper, brand_upper)

    def normalize_model(self, model: str) -> str:
        """모델명 정규화"""
        return model.upper().replace(" ", "").replace("_", "").replace("-", "")

    def normalize_grade(self, grade: str, model: str = "") -> str:
        """등급명 정규화"""
        # 모델명 prefix 제거
        if model and grade.upper().startswith(model.upper()):
            grade = grade[len(model):].strip()

        # 한글 → 영어 변환
        grade_upper = grade.upper()
        for kr, en in self.WORD_MAP.items():
            grade_upper = grade_upper.replace(kr.upper(), en)

        # 공백 및 특수문자 제거
        return grade_upper.replace(" ", "").replace("_", "").replace("-", "")

class VehicleMatchingService:
    """차량 매칭 전담 서비스"""

    def __init__(self):
        self.master_carinfo = self._load_master_carinfo()
        self.normalizer = VehicleNameNormalizer()

    def find_vehicle_in_capital(
        self,
        brand: str,
        model: str,
        trim: str,
        capital_id: str,
        match_config: VehicleMatchConfig
    ) -> Optional[MatchedVehicle]:
        """
        캐피탈 데이터에서 차량 찾기

        Args:
            brand: 브랜드명
            model: 모델명
            trim: 트림명
            capital_id: 캐피탈 ID
            match_config: 매칭 설정

        Returns:
            매칭된 차량 정보 또는 None
        """
        # 1. master_carinfo에서 가격 조회
        master_price = self.get_master_price(brand, model, trim)
        if not master_price:
            return None

        # 2. 캐피탈별 등급 매핑 조회
        capital_vehicle = self._find_in_capital_data(
            brand, model, trim, capital_id, match_config
        )

        if not capital_vehicle:
            return None

        # 3. 결과 통합
        return MatchedVehicle(
            vehicle_id=capital_vehicle['id'],
            price=master_price,
            grade_info=capital_vehicle['grade_info'],
            metadata=capital_vehicle.get('metadata', {})
        )

    def get_master_price(self, brand: str, model: str, grade: str) -> Optional[int]:
        """master_carinfo에서 가격 조회"""
        norm_brand = self.normalizer.normalize_brand(brand)
        norm_model = self.normalizer.normalize_model(model)
        norm_grade = self.normalizer.normalize_grade(grade, model)

        matches = []
        for car_id, car_data in self.master_carinfo.items():
            if self._is_match(norm_brand, norm_model, norm_grade, car_data):
                matches.append(car_data)

        if not matches:
            return None

        # 최신 연식 선택
        matches.sort(key=lambda x: x.get('name', ''), reverse=True)
        return matches[0].get('price')

    def _is_match(
        self,
        norm_brand: str,
        norm_model: str,
        norm_grade: str,
        car_data: Dict
    ) -> bool:
        """차량 매칭 여부 확인"""
        car_brand = self.normalizer.normalize_brand(car_data.get('brand', ''))
        car_model = self.normalizer.normalize_model(car_data.get('model', ''))
        car_grade = self.normalizer.normalize_grade(car_data.get('grade', ''))

        # 브랜드 일치
        if norm_brand != car_brand:
            return False

        # 모델 유연한 매칭
        if not self._model_match(norm_model, car_model):
            return False

        # 등급 유연한 매칭
        if not self._grade_match(norm_grade, car_grade):
            return False

        return True

    def _model_match(self, norm_model: str, car_model: str) -> bool:
        """모델명 유연한 매칭"""
        # 포함 관계
        if norm_model in car_model or car_model in norm_model:
            return True

        # 숫자 기반 매칭
        norm_nums = ''.join(re.findall(r'\d+', norm_model))
        car_nums = ''.join(re.findall(r'\d+', car_model))

        if norm_nums and car_nums:
            # 첫 자리 숫자가 같으면 같은 시리즈
            if norm_nums[0] == car_nums[0]:
                return True

        return False

    def _grade_match(self, norm_grade: str, car_grade: str) -> bool:
        """등급명 유연한 매칭"""
        # 포함 관계
        if norm_grade in car_grade or car_grade in norm_grade:
            return True

        # 숫자 + 키워드 매칭
        grade_nums = ''.join(re.findall(r'\d+', norm_grade))
        car_grade_nums = ''.join(re.findall(r'\d+', car_grade))

        if grade_nums and car_grade_nums and grade_nums == car_grade_nums:
            common_keywords = ['SPORT', 'BASE', 'LUXURY', 'PREMIUM', 'SIGNATURE']
            for keyword in common_keywords:
                if keyword in norm_grade and keyword in car_grade:
                    return True

        # BASE 특수 처리
        if "BASE" in norm_grade and "BASE" in car_grade:
            return True

        return False

    def _find_in_capital_data(
        self,
        brand: str,
        model: str,
        trim: str,
        capital_id: str,
        config: VehicleMatchConfig
    ) -> Optional[Dict]:
        """캐피탈별 데이터에서 차량 찾기"""
        grade_mapping_path = Path(f"data/capitals/{capital_id}/grade_mapping.json")

        if not grade_mapping_path.exists():
            return None

        with open(grade_mapping_path, 'r', encoding='utf-8') as f:
            grade_mapping = json.load(f)

        # 매칭 로직 (캐피탈별 설정 반영)
        # ... (기존 find_vehicle_by_name 로직 활용)

        return None  # 구현 필요

    def _load_master_carinfo(self) -> Dict:
        """master_carinfo.json 로드"""
        path = Path("data/master_carinfo.json")
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
```

#### 2.5 ComparisonService (비교 로직 분리)

```python
# services/comparison.py
from typing import List, Optional
from dataclasses import dataclass

from core.registry import registry
from core.base_calculator import CalculationInput, CalculationResult
from services.vehicle_matching import VehicleMatchingService

@dataclass
class ComparisonRequest:
    """비교 요청"""
    brand: str
    model: str
    trim: str
    contract_months: int
    annual_mileage: int
    down_payment_percent: float
    capital_ids: Optional[List[str]] = None  # None이면 전체 비교

@dataclass
class ComparisonResult:
    """비교 결과"""
    capital_id: str
    display_name: str
    monthly_payment: Optional[int]
    grade_option: Optional[str]
    residual_rate: Optional[float]
    details: Optional[CalculationResult]
    error: Optional[str]
    rank: Optional[int]

class ComparisonService:
    """캐피탈 비교 서비스"""

    def __init__(self):
        self.vehicle_matcher = VehicleMatchingService()
        self.registry = registry

    def compare(self, request: ComparisonRequest) -> List[ComparisonResult]:
        """
        여러 캐피탈 비교

        Args:
            request: 비교 요청

        Returns:
            정렬된 비교 결과 목록
        """
        # 비교할 캐피탈 결정
        capital_ids = request.capital_ids or self.registry.get_all_capitals()

        results = []
        for capital_id in capital_ids:
            try:
                result = self._calculate_for_capital(capital_id, request)
                results.append(result)
            except Exception as e:
                # 에러 발생 시에도 결과 추가
                results.append(ComparisonResult(
                    capital_id=capital_id,
                    display_name=self.registry.get_calculator(capital_id).get_display_name(),
                    monthly_payment=None,
                    grade_option=None,
                    residual_rate=None,
                    details=None,
                    error=str(e),
                    rank=None
                ))

        # 정렬 및 순위 부여
        self._assign_ranks(results)

        return results

    def _calculate_for_capital(
        self,
        capital_id: str,
        request: ComparisonRequest
    ) -> ComparisonResult:
        """단일 캐피탈 계산"""

        calculator = self.registry.get_calculator(capital_id)

        # 1. 차량 매칭
        vehicle = self.vehicle_matcher.find_vehicle_in_capital(
            request.brand,
            request.model,
            request.trim,
            capital_id,
            calculator.config.get('matching_config', {})
        )

        if not vehicle:
            raise ValueError(
                f"차량을 찾을 수 없습니다: {request.brand} {request.model} {request.trim}"
            )

        # 2. 최적 잔가 옵션 선택
        grade_option = self._select_best_grade_option(calculator, vehicle.vehicle_id)

        # 3. 잔존율 조회
        residual_rate = calculator.get_residual_rate(
            vehicle.vehicle_id,
            request.contract_months,
            request.annual_mileage,
            grade_option
        )

        # 4. 금리 조회 (간단히 config에서)
        annual_rate = calculator.config.get('interest_rate_config', {}).get('base_rate', 0.05)

        # 5. 계산
        input_data = CalculationInput(
            vehicle_price=vehicle.price,
            residual_rate=residual_rate,
            contract_months=request.contract_months,
            annual_mileage=request.annual_mileage,
            annual_interest_rate=annual_rate,
            down_payment_rate=request.down_payment_percent / 100
        )

        calc_result = calculator.calculate(input_data)

        return ComparisonResult(
            capital_id=capital_id,
            display_name=calculator.get_display_name(),
            monthly_payment=calc_result.monthly_payment,
            grade_option=grade_option,
            residual_rate=residual_rate,
            details=calc_result,
            error=None,
            rank=None
        )

    def _select_best_grade_option(
        self,
        calculator,
        vehicle_id: str
    ) -> str:
        """
        최적 잔가 옵션 선택 (우선순위 기반)

        Args:
            calculator: 캐피탈 계산기
            vehicle_id: 차량 ID

        Returns:
            등급 옵션 ID
        """
        grade_options = calculator.config.get('grade_options', {})
        available_options = calculator.get_available_grade_options(vehicle_id)

        # 우선순위로 정렬
        sorted_options = sorted(
            grade_options.items(),
            key=lambda x: x[1].get('priority', 999)
        )

        # 차량이 지원하는 첫 번째 옵션 선택
        for option_id, option_config in sorted_options:
            if option_id in available_options:
                return option_id

        raise ValueError(f"사용 가능한 잔가 옵션이 없습니다: {vehicle_id}")

    def _assign_ranks(self, results: List[ComparisonResult]):
        """순위 부여 (in-place)"""
        # 성공한 결과만 정렬
        valid_results = [r for r in results if r.monthly_payment is not None]
        valid_results.sort(key=lambda x: x.monthly_payment)

        for rank, result in enumerate(valid_results, 1):
            result.rank = rank
```

#### 2.6 단순화된 app.py

```python
# app.py (200 lines)
import streamlit as st
from typing import List

from services.comparison import ComparisonService, ComparisonRequest, ComparisonResult
from services.vehicle_matching import VehicleMatchingService
from core.registry import registry
from core.base_calculator import CalculationInput

def main():
    st.title("🚗 리스 계산기")

    # 캐피탈 선택
    capitals = registry.get_display_names()
    capital_options = list(capitals.keys()) + ["compare"]

    capital = st.selectbox(
        "캐피탈 선택",
        capital_options,
        format_func=lambda x: "🔍 비교 (모든 캐피탈)" if x == "compare" else capitals.get(x, x),
        index=len(capital_options) - 1  # 기본값: 비교
    )

    # 차량 선택 (기존과 동일)
    vehicle_matcher = VehicleMatchingService()
    master_carinfo = vehicle_matcher.master_carinfo

    brands = sorted(set(v['brand'] for v in master_carinfo.values()))
    brand = st.selectbox("브랜드", brands)

    models = sorted(set(
        v['model'] for v in master_carinfo.values()
        if v['brand'] == brand
    ))
    model = st.selectbox("모델", models)

    trims = sorted(set(
        v['grade'] for v in master_carinfo.values()
        if v['brand'] == brand and v['model'] == model
    ))
    trim = st.selectbox("트림", trims)

    # 가격 표시
    price = vehicle_matcher.get_master_price(brand, model, trim)
    if price:
        st.markdown(f"**차량 가격:** {price:,}원 (master_carinfo 기준)")

    # 계약 조건 입력 (기존과 동일)
    col1, col2 = st.columns(2)
    with col1:
        contract_months = st.selectbox("계약 기간", [12, 24, 36, 48, 60], index=4)
    with col2:
        annual_mileage = st.selectbox("연간 주행거리", [10000, 15000, 20000, 30000], index=2)

    down_payment_percent = st.slider("선납금 비율 (%)", 0, 50, 0)

    # 계산하기
    if st.button("계산하기", type="primary"):
        if capital == "compare":
            # 비교 모드
            display_comparison_mode(
                brand, model, trim,
                contract_months, annual_mileage, down_payment_percent
            )
        else:
            # 단일 캐피탈 모드
            display_single_mode(
                capital, brand, model, trim,
                contract_months, annual_mileage, down_payment_percent
            )

def display_comparison_mode(
    brand: str, model: str, trim: str,
    contract_months: int, annual_mileage: int, down_payment_percent: float
):
    """비교 모드 표시"""
    comparison_service = ComparisonService()

    request = ComparisonRequest(
        brand=brand,
        model=model,
        trim=trim,
        contract_months=contract_months,
        annual_mileage=annual_mileage,
        down_payment_percent=down_payment_percent
    )

    with st.spinner("비교 중..."):
        results = comparison_service.compare(request)

    # 통계
    success_count = sum(1 for r in results if r.monthly_payment is not None)
    error_count = len(results) - success_count

    if success_count > 0:
        st.success(f"✅ {success_count}개 캐피탈 비교 완료")
    if error_count > 0:
        st.warning(f"⚠️ {error_count}개 캐피탈은 데이터가 없습니다")

    st.markdown("#### 💰 월 납입료 비교 (낮은 순)")

    # 결과 표시
    for result in results:
        display_comparison_result(result, results)

def display_comparison_result(result: ComparisonResult, all_results: List[ComparisonResult]):
    """비교 결과 하나 표시"""
    if result.error:
        # 에러 표시
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            st.markdown("### ❌")
        with col2:
            st.markdown(f"**{result.display_name}**")
            st.caption("데이터 없음")
        with col3:
            st.markdown("### -")
            st.caption(f"⚠️ {result.error}")
        st.markdown("---")
        return

    # 정상 결과
    rank_emoji = "🥇" if result.rank == 1 else "🥈" if result.rank == 2 else "🥉" if result.rank == 3 else f"{result.rank}."

    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        st.markdown(f"### {rank_emoji}")

    with col2:
        st.markdown(f"**{result.display_name}**")
        st.caption(f"잔가: {result.residual_rate:.1%} ({result.grade_option})")

    with col3:
        st.markdown(f"### {result.monthly_payment:,}원")
        if result.rank == 1:
            st.caption("🎯 최저가")
        elif result.rank and result.rank > 1:
            first = next(r for r in all_results if r.rank == 1)
            diff = result.monthly_payment - first.monthly_payment
            st.caption(f"↑ {diff:,}원")

    # 계산 상세보기
    with st.expander("📊 계산 상세보기"):
        display_calculation_details(result.details)

    st.markdown("---")

def display_single_mode(
    capital: str, brand: str, model: str, trim: str,
    contract_months: int, annual_mileage: int, down_payment_percent: float
):
    """단일 캐피탈 모드 표시"""
    calculator = registry.get_calculator(capital)
    vehicle_matcher = VehicleMatchingService()

    # 차량 매칭
    vehicle = vehicle_matcher.find_vehicle_in_capital(
        brand, model, trim, capital,
        calculator.config.get('matching_config', {})
    )

    if not vehicle:
        st.error(f"❌ 차량을 찾을 수 없습니다: {brand} {model} {trim}")
        return

    # 잔가 옵션 선택
    available_options = calculator.get_available_grade_options(vehicle.vehicle_id)
    grade_option = st.selectbox("잔가 옵션", available_options)

    # 잔존율 조회
    residual_rate = calculator.get_residual_rate(
        vehicle.vehicle_id, contract_months, annual_mileage, grade_option
    )

    # 계산
    input_data = CalculationInput(
        vehicle_price=vehicle.price,
        residual_rate=residual_rate,
        contract_months=contract_months,
        annual_mileage=annual_mileage,
        annual_interest_rate=calculator.config.get('interest_rate_config', {}).get('base_rate', 0.05),
        down_payment_rate=down_payment_percent / 100
    )

    result = calculator.calculate(input_data)

    # 결과 표시
    st.success(f"✅ {calculator.get_display_name()} 계산 완료")
    st.markdown(f"### 💰 월 납입료: {result.monthly_payment:,}원")

    with st.expander("📊 계산 상세보기", expanded=True):
        display_calculation_details(result)

def display_calculation_details(result):
    """계산 상세 정보 표시"""
    breakdown = result.breakdown

    info_text = f"""
**[계약 조건]**
계약기간: {breakdown.get('contract_months', 0)}개월 | 연간주행: {breakdown.get('annual_mileage', 0):,}km | 잔존율: {breakdown.get('residual_rate', 0):.1%} | 금리: {breakdown.get('annual_interest_rate', 0):.2%}

**[취득원가]**
차량가격: {breakdown.get('vehicle_price', 0):,}원 | 취득세: {breakdown.get('acquisition_tax', 0):,}원 | 등록비: {breakdown.get('registration_fee', 0):,}원 → 합계: {result.acquisition_cost:,}원

**[금융 조건]**
선납금: {result.down_payment:,}원 | 잔존가치: {result.residual_value:,}원

**[월 납입료 구성]**
"""

    if 'monthly_depreciation' in breakdown:
        info_text += f"감가상각: {breakdown.get('monthly_depreciation', 0):,}원 | 금융비용: {breakdown.get('monthly_interest', 0):,}원 | 자동차세: {breakdown.get('monthly_car_tax', 0):,}원 → 합계: {result.monthly_payment:,}원"
    else:
        info_text += f"원리금균등상환: {result.monthly_payment:,}원"

    info_text += f"""

**[총 비용]**
총납부액: {result.total_payment:,}원 - 잔존가치: {result.residual_value:,}원 = 실차량비용: {result.total_payment - result.residual_value:,}원
"""

    st.markdown(info_text)

if __name__ == "__main__":
    main()
```

### 3. 캐피탈별 설정 파일

#### config.json (메리츠 예시)

```json
{
  "capital_id": "meritz_capital",
  "display_name": "메리츠캐피탈",
  "version": "1.0.0",
  "enabled": true,
  "calculation_method": "straight_line",

  "supported_features": [
    "multiple_grades",
    "premium_residual",
    "ev_discount",
    "regional_bond"
  ],

  "grade_options": {
    "west_normal": {
      "display": "West 일반잔가",
      "priority": 4,
      "adjustment": 0.0
    },
    "aps_normal": {
      "display": "APS 일반잔가",
      "priority": 3,
      "adjustment": 0.0
    },
    "aps_premium": {
      "display": "APS 고잔가",
      "priority": 1,
      "adjustment": 0.08
    },
    "vgs_premium": {
      "display": "VGS 고잔가",
      "priority": 2,
      "adjustment": 0.06
    }
  },

  "interest_rate_config": {
    "base_rate": 0.05,
    "ev_discount": 0.005,
    "import_premium": 0.003,
    "high_price_threshold": 80000000,
    "high_price_premium": 0.002
  },

  "acquisition_tax_config": {
    "base_rate": 0.07,
    "hybrid_rate": 0.05,
    "ev_reduction": 1400000,
    "ev_reduction_method": "min_of_4pct_or_1.4m"
  },

  "registration_fee": 100000,
  "ev_car_tax": 130000,

  "matching_config": {
    "trim_includes_model": true,
    "case_sensitive": false,
    "fuzzy_match": true,
    "brand_translations": "default",
    "word_translations": "default"
  }
}
```

---

## 마이그레이션 계획

### Phase 1: 기반 구축 (2일)

#### Day 1: 핵심 클래스 구현
- [ ] `BaseCapitalCalculator` 구현 (4시간)
  - [ ] 추상 메서드 정의
  - [ ] 공통 메서드 구현
  - [ ] 데이터 로딩 로직

- [ ] `CapitalRegistry` 구현 (3시간)
  - [ ] 싱글톤 패턴
  - [ ] 동적 로딩 로직
  - [ ] 에러 핸들링

- [ ] 디렉토리 구조 생성 (1시간)
  - [ ] `data/capitals/` 생성
  - [ ] `core/calculators/` 생성
  - [ ] `services/` 생성

#### Day 2: 서비스 계층 구현
- [ ] `VehicleMatchingService` 구현 (4시간)
  - [ ] 정규화 로직 분리
  - [ ] 매칭 로직 개선
  - [ ] 테스트 케이스 작성

- [ ] `ComparisonService` 구현 (3시간)
  - [ ] 비교 로직 분리
  - [ ] 순위 계산
  - [ ] 에러 핸들링

- [ ] 단위 테스트 작성 (1시간)

### Phase 2: 기존 캐피탈 마이그레이션 (3일)

#### Day 3-4: 메리츠 마이그레이션
- [ ] 데이터 마이그레이션 (4시간)
  - [ ] `data/capitals/meritz/config.json` 작성
  - [ ] `residual_rates.json` 변환
  - [ ] `grade_mapping.json` 작성

- [ ] `MeritzCapitalCalculator` 구현 (6시간)
  - [ ] `core/lease_calculator.py` 로직 이식
  - [ ] BaseCalculator 인터페이스 구현
  - [ ] 테스트 작성 및 검증

- [ ] 기존 코드와 결과 비교 검증 (2시간)

#### Day 5: MG 마이그레이션
- [ ] 데이터 마이그레이션 (2시간)
  - [ ] `data/capitals/mg/config.json` 작성
  - [ ] `residual_rates.json` 변환

- [ ] `MGCapitalCalculator` 리팩토링 (4시간)
  - [ ] BaseCalculator 인터페이스 구현
  - [ ] 기존 로직 유지하면서 구조 개선

- [ ] 검증 (2시간)

### Phase 3: app.py 리팩토링 (1일)

#### Day 6: UI 단순화
- [ ] 기존 app.py 백업 (10분)
  - [ ] `app.py.old` 생성

- [ ] 새 app.py 작성 (4시간)
  - [ ] Registry 사용
  - [ ] ComparisonService 통합
  - [ ] UI 로직만 유지

- [ ] 통합 테스트 (3시간)
  - [ ] 기존 기능 모두 동작 확인
  - [ ] 비교 모드 검증
  - [ ] 단일 모드 검증

### Phase 4: 문서화 및 정리 (1일)

#### Day 7: 마무리
- [ ] 문서 작성 (4시간)
  - [ ] `PLUGIN_GUIDE.md`: 새 캐피탈 추가 가이드
  - [ ] `API_REFERENCE.md`: API 문서
  - [ ] `MIGRATION_GUIDE.md`: 마이그레이션 가이드

- [ ] 코드 정리 (2시간)
  - [ ] 미사용 코드 제거
  - [ ] 주석 정리
  - [ ] Import 정리

- [ ] Git 커밋 및 태깅 (1시간)
  - [ ] `git commit -m "refactor: plugin architecture"`
  - [ ] `git tag v2.0.0`

### 총 소요 시간: **7일 (실제 작업 약 40시간)**

---

## 예상 효과 및 ROI

### 1. 개발 생산성

| 작업 | Before | After | 개선율 |
|------|--------|-------|--------|
| 새 캐피탈 추가 | 2-3일 | 2-3시간 | **90% ↓** |
| 로직 수정 | 5곳 | 1곳 | **80% ↓** |
| 버그 수정 | 3-4시간 | 30분 | **87% ↓** |
| 테스트 작성 | 불가능 | 쉬움 | **신규** |

### 2. 코드 품질

| 지표 | Before | After | 개선 |
|------|--------|-------|------|
| app.py 라인 수 | 600+ | 200 | **67% ↓** |
| 순환 복잡도 | 높음 (40+) | 낮음 (10) | **75% ↓** |
| 중복 코드 | 많음 (30%) | 없음 (0%) | **100% ↓** |
| 테스트 커버리지 | 0% | 80%+ | **신규** |

### 3. ROI 계산

#### 초기 투자
- 리팩토링 시간: **7일 (40시간)**
- 비용: **40시간 × 시간당 비용**

#### 예상 수익 (연간)
1. **새 캐피탈 15개 추가**
   - Before: 15 × 3일 = 45일
   - After: 15 × 3시간 = 45시간 (5.6일)
   - 절감: **39.4일 (315시간)**

2. **유지보수 비용 절감**
   - Before: 주당 4시간
   - After: 주당 1시간
   - 절감: **주당 3시간 × 52주 = 156시간 (19.5일)**

3. **버그 수정 시간 절감**
   - Before: 월 10시간
   - After: 월 2시간
   - 절감: **월 8시간 × 12개월 = 96시간 (12일)**

#### 총 절감
- **연간 약 71일 (568시간) 절감**
- **ROI: (568 - 40) / 40 = 1,320%**

### 4. 비즈니스 가치

#### 시장 대응 속도
- **새 캐피탈 추가: 3일 → 3시간** (10배 빨라짐)
- 경쟁사 대비 우위 확보

#### 서비스 품질
- 버그 감소 → 사용자 만족도 증가
- 일관된 계산 로직 → 신뢰도 증가

#### 확장성
- 17개 → 100개 확장 가능
- 새 비즈니스 모델 추가 용이

---

## 리스크 및 대응 방안

### 1. 마이그레이션 리스크

#### 리스크: 기능 누락
- **대응**: Phase by Phase 검증
- **방법**: 각 단계마다 기존 기능과 동일한지 확인

#### 리스크: 계산 결과 불일치
- **대응**: 자동화된 회귀 테스트
- **방법**: 100개 샘플 데이터로 Before/After 비교

### 2. 개발 리스크

#### 리스크: 예상보다 시간 초과
- **대응**: 우선순위 조정
- **방법**:
  - Phase 1-2 필수 (기능 유지)
  - Phase 3-4 선택 (개선)

#### 리스크: 팀원 이해도 부족
- **대응**: 단계별 교육
- **방법**:
  - Phase 1 완료 후: 아키텍처 설명회
  - Phase 2 완료 후: 플러그인 개발 워크샵

### 3. 운영 리스크

#### 리스크: 신규 개발자 온보딩 시간 증가
- **대응**: 상세한 문서화
- **방법**:
  - PLUGIN_GUIDE.md: 단계별 가이드
  - 예시 코드 제공

#### 리스크: 기존 데이터 호환성
- **대응**: 점진적 마이그레이션
- **방법**:
  - 기존 파일 유지하면서 새 구조 추가
  - 양쪽 모두 지원하다가 점진적 제거

---

## 결론 및 권장사항

### 핵심 메시지

1. **지금 리팩토링하지 않으면 기술 부채가 기하급수적으로 증가**
   - 2개 → 17개: 복잡도 8.5배 증가
   - 유지보수 비용 연간 500시간 이상 증가 예상

2. **플러그인 아키텍처는 검증된 솔루션**
   - Eclipse, VSCode, Webpack 등 성공 사례 다수
   - 확장성과 유지보수성 획기적 개선

3. **투자 대비 수익이 명확**
   - 초기 투자: 7일
   - 연간 절감: 71일
   - ROI: 1,320%

### 권장사항

#### 단기 (즉시)
1. ✅ 본 리팩토링 플랜 승인
2. ✅ 7일 개발 일정 확보
3. ✅ Phase 1 시작

#### 중기 (2주 후)
1. ✅ 메리츠/MG 마이그레이션 완료
2. ✅ 나머지 15개 캐피탈 순차 추가
3. ✅ 테스트 커버리지 80% 달성

#### 장기 (1개월 후)
1. ✅ 17개 캐피탈 모두 통합
2. ✅ API 서버 분리 검토
3. ✅ 다른 프로젝트 재사용

---

## 부록

### A. 용어 정리

- **플러그인 아키텍처**: 핵심 시스템에 기능을 동적으로 추가할 수 있는 설계 패턴
- **레지스트리 패턴**: 객체를 중앙에서 관리하는 디자인 패턴
- **추상 기본 클래스(ABC)**: 구현을 강제하는 인터페이스 역할
- **의존성 주입(DI)**: 객체 생성을 외부에서 주입하여 결합도 낮추기

### B. 참고 자료

- Martin Fowler, "Refactoring: Improving the Design of Existing Code"
- Uncle Bob, "Clean Architecture"
- GoF, "Design Patterns"

### C. 문의

- 기술 문의: [이메일/슬랙]
- 코드 리뷰 요청: [PR 링크]

---


