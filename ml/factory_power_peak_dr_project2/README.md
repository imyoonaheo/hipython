# ⚡ 공장 전력 피크 경보 & DR 수익 플랫폼

> AI 기반 제조 전력 비용 절감 및 수익 창출 플랫폼
> **올라운더팀** | 허유나 · 이형주 · 강창희 · 박순선 | 2026

![표지](assets/slide_01_cover.png)

---

## 📌 한 줄 소개

> XGBoost 기반 **15분 단위 전력 피크 예측** + **DR 수익 자동 계산** 플랫폼
> 중소 제조 공장의 전기요금 절감과 수요반응(DR) 수익 창출을 동시에 지원합니다.

---

## 🔴 문제 정의

![문제정의](assets/slide_03_problem.png)

전기요금은 총 사용량이 아닌 **한 순간의 최대 피크(Peak)** 로 결정됩니다.
직전 12개월 중 가장 높은 피크가 향후 1년간의 기본요금 기준이 되는 구조로,
**"한 번의 실수 = 1년 비용"** 이라는 문제가 발생합니다.

현재 중소 공장의 운영 방식은 전기 담당자가 하루 3~4회 계기판을 수동 확인하는 수준으로,
실시간 대응이 불가능하고 DR 제도 참여도 어려운 상황입니다.

---

## ✅ 핵심 기능

![핵심기능](assets/slide_12_features.png)

| 탭 | 기능 | 주요 내용 |
|----|------|---------|
| Tab 1 📊 | **전력 피크 예측** | XGBoost로 15/30/45/60분 단위 피크 예측 + 경보 알림 |
| Tab 2 ⚡ | **전력 실적 조회** | 월별/기간별 전력 사용 패턴 분석 및 시각화 |
| Tab 3 ⚙️ | **운영 최적화** | TOU 기반 비용 최소화 생산 스케줄 도출 |
| Tab 4 💰 | **DR 수익 시뮬레이션** | CBL 기반 감축량 산정 + 예상 정산금 자동 계산 |
| Tab 5 🌿 | **ESG 리포트** | Scope 2 탄소배출량 자동 계산 + GRI 302 리포트 생성 |

---

## 🛠 기술 스택

![기술스택](assets/slide_13_techstack.png)

| 영역 | 기술 |
|------|------|
| ML 예측 모델 | XGBoost (R²=0.9663, RMSE=9.43kW) |
| 웹 프레임워크 | Streamlit |
| 데이터 처리 | Pandas / NumPy |
| 시각화 | Plotly |
| 데이터베이스 | SQLite (PowerMgt.db) |
| 날씨 API | 기상청 단기예보 API (울산 ASOS #152) |
| 개발 언어 | Python 3.8+ |

---

## 📊 데이터 설계

![데이터설계](assets/slide_18_data.png)

- **데이터 소스**: KAMP + 기상청 ASOS + KEPCO + 한국전력거래소
- **최종 데이터셋**: `okm_enriched_final.csv`
  - 8,760행 (1시간 단위, Full Year) / 37개 피처 / 결측치 0
- **증강 전략**: KAMP 원본 1~9월(6,120행) + 10~12월 증강(2,640행) = 8,760행
- **GMM 클러스터링**으로 생산 패턴 4단계 자동 분류
- **파생변수 14개** 생성: furnace_on(열처리로 역추론), TOU 구간, 주간여부 등

---

## 🤖 모델 설계

![모델비교](assets/slide_21_model.png)

6개 모델 비교 실험 (LinearRegression / Ridge / DecisionTree / RandomForest / XGBoost / DNN) 후
**XGBoost 최종 채택** — furnace_on 등 이진/범주형 변수가 지배적인 데이터 특성상 트리 기반 모델이 압도적으로 유리했습니다.

![모델구조](assets/slide_22_model_matrix.png)

**3 Sets × 4 Time Steps = 12개 독립 모델** 병렬 구조로 구성했습니다.

| Set | 피처 수 | 설명 |
|-----|--------|------|
| Set_A | 8개 | 날짜·시간·달력 기본 정보 |
| Set_B | 12개 | Set_A + 기상 데이터 |
| **Set_C ★** | **22개** | Set_B + 생산량·GMM·furnace_on·TOU 등 (최고 정확도) |

---

## 💰 비즈니스 가치

![비즈니스가치](assets/slide_14_value.png)

| 가치 | 내용 |
|------|------|
| 💰 비용 절감 | 피크 감축을 통한 기본요금 최소화 → 전력 비용 10~20% 절감 |
| 📈 수익 창출 | DR 참여로 추가 정산금 확보 (CBL × MGP 93.41원/kWh) |
| 🌿 ESG 성과 | Scope 2 자동 계산 + GRI 302 리포트 자동 생성 |

---

## 🚀 실행 방법

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. 앱 실행
streamlit run streamlit_app.py
```

> **필수 파일 확인**
> - `models/energy_pipeline_v4.pkl` — XGBoost 모델
> - `db/PowerMgt.db` — SQLite DB
> - `data/okm_enriched_final.csv` — 학습 데이터
> - `data/power_estimate_full_2021.csv` — 전력 실적 (Tab2용)

---

## 📁 프로젝트 구조

```
factory_power_peak_dr_project2/
├── streamlit_app.py              # 메인 진입점
├── predictor1.py                 # XGBoost 예측 모듈
├── power_db_operations.py        # DB + 기상청 API 연동
├── weather_api.py                # 날씨 데이터 수집
├── requirements.txt
├── pages/
│   ├── tab1_dashboard.py         # 피크 예측
│   ├── tab2_power_query.py       # 전력 조회
│   ├── tab3_dr_sim.py            # DR 시뮬레이션
│   ├── tab3_optimization.py      # 운영 최적화
│   ├── tab4_dr_sim.py            # DR 연결 wrapper
│   └── tab5_esg.py               # ESG 리포트
├── dashboard/                    # HTML 확정본 5개
├── data/                         # CSV 데이터
├── db/                           # SQLite DB
├── models/                       # XGBoost 모델
└── notebook/                     # 모델 개발 Jupyter
```

---

> 본 프로젝트는 KAMP 소성가공 자원 최적화 AI 데이터셋을 활용하였습니다.
