# 🚀 운용리스 계산기 v2 - 빠른 시작 가이드

## 즉시 실행

### 1. Streamlit 웹앱 실행
```bash
streamlit run app.py
```
→ 브라우저에서 http://localhost:8501 자동 오픈

### 2. 엑셀 견적서 검증
```bash
python tools/excel_validator.py "xlsx/meritz_capital_2509_V1.xlsx" 2000
```

### 3. 통합 테스트
```bash
python tests/test_calculator_integration.py
```

## ✅ 검증 결과

**메리츠 엑셀 견적서 대비:**
- 엑셀: 1,079,400원
- 계산: 1,079,000원
- **오차: 400원 (0.04%)** ✅

목표 ±2,000원 달성!

## 📊 데이터 현황

- 차량: 962대
- 캐피탈: 메리츠
- 잔존율: 15,392개 데이터 포인트

## 🔍 핵심 발견

메리츠 엑셀의 **하이브리드 계산 방식** 규명:
- 잔존가치 = 차량가 × 잔존율 (세금 제외)
- 금융대상 = 취득원가 (세금 포함)

## 📖 상세 문서

→ `docs/IMPLEMENTATION_SUMMARY.md` 참고

---

**생성일:** 2025-11-05 | **상태:** ✅ Production Ready
