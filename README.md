# 운용리스 계산기 v2

금융사 엑셀 견적기를 역공학하여 동일한 계산 결과를 도출하는 웹 기반 운용리스 계산기

## 프로젝트 개요

- **목적**: 특정 금융사의 엑셀 견적기를 역공학하여 동일한 계산 결과 도출
- **목표**: 엑셀 견적서와 오차 ±2,000원 이내 정확도 달성
- **기술 스택**: Python 3.10+, Streamlit, JSON 데이터

## 프로젝트 구조

```
lease-calculator-v2/
├── app.py                          # Streamlit 메인 앱
├── requirements.txt                # 패키지 의존성
├── README.md
│
├── core/                           # 계산 엔진
│   ├── __init__.py
│   ├── calculator.py
│   └── validator.py
│
├── data/                           # 데이터 레이어
│   ├── __init__.py
│   ├── residual_rates/            # 캐피탈별 잔존율 JSON
│   ├── vehicle_master.py
│   ├── residual_rates.py
│   ├── interest_rates.py
│   └── tax_policies.py
│
├── utils/                          # 유틸리티
│   ├── __init__.py
│   ├── data_loader.py
│   └── formatters.py
│
├── tests/                          # 테스트
│   ├── __init__.py
│   ├── test_calculator.py
│   └── test_integration.py
│
├── tools/                          # 변환 도구
│   ├── excel_to_json.py
│   └── validate_json.py
│
└── excel_reverse_engineering/      # 엑셀 역공학
    ├── excel_parser.py
    ├── residual_extractor.py
    └── formula_extractor.py
```

## 설치 방법

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

## 사용 방법

### 1. 엑셀 파일을 JSON으로 변환

```bash
python tools/excel_to_json.py "엑셀파일경로.xlsx" capital_id
```

### 2. Streamlit 앱 실행

```bash
streamlit run app.py
```

## 개발 단계

- [x] Phase 1: 프로젝트 구조 생성
- [ ] Phase 2: 엑셀 역공학 도구 개발
- [ ] Phase 3: JSON 데이터 구축
- [ ] Phase 4: 계산 엔진 개발
- [ ] Phase 5: Streamlit UI 개발
- [ ] Phase 6: 테스트 및 검증

## 라이센스

Private Project
