"""
app1.py — 신용카드 연체확률 예측 Streamlit 웹 서비스 (UI 개선)
실행 : conda activate ml_edu  →  streamlit run app1.py
"""

import streamlit as st
import pandas as pd
from predict import load_pipeline, get_risk, FEATURE_COLS

# ── 페이지 설정 ───────────────────────────────────────────────────
st.set_page_config(
    page_title="신용카드 연체확률 예측",
    page_icon="💳",
    layout="wide",
)

# ── 커스텀 CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
/* 사이드바 배경 */
[data-testid="stSidebar"] {
    background-color: #1b2838;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    color: #dce8f5 !important;
}
[data-testid="stSidebar"] .stCaption p {
    color: #8bafc9 !important;
}

/* 섹션 타이틀 배지 */
.badge {
    display: inline-block;
    background: #2d5a8e;
    color: white !important;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 10px;
}

/* 결과 등급 박스 */
.grade-box {
    text-align: center;
    padding: 18px;
    border-radius: 12px;
    font-size: 22px;
    font-weight: 800;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── EX-01 : 모델 로드 ─────────────────────────────────────────────
@st.cache_resource
def get_pipeline():
    try:
        return load_pipeline()
    except FileNotFoundError:
        return None

pipeline = get_pipeline()
if pipeline is None:
    st.error("⛔ 모델 파일을 찾을 수 없습니다. `models/pipeline.pkl` 경로를 확인해주세요.")
    st.stop()

# ═══════════════════════════════════════════════════════════════
# SIDEBAR ── ① 기본 고객 정보  +  ② 납부 상태
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 💳 연체확률 예측")
    st.caption("고객 정보를 입력 후 **예측하기**를 눌러주세요.")
    st.divider()

    # ① 기본 고객 정보
    st.markdown("### ① 기본 고객 정보")
    LIMIT_BAL = st.number_input(
        "신용한도 LIMIT_BAL (NTD)",
        min_value=10_000, max_value=1_000_000,
        value=200_000, step=10_000,
        help="유효 범위: 10,000 ~ 1,000,000"
    )
    SEX = st.selectbox("성별 SEX", [1, 2],
                       format_func=lambda x: "남성 (1)" if x == 1 else "여성 (2)")
    EDUCATION = st.selectbox(
        "교육수준 EDUCATION", [1, 2, 3, 4],
        format_func=lambda x: {1:"대학원 (1)",2:"대학 (2)",3:"고졸 (3)",4:"기타 (4)"}[x]
    )
    MARRIAGE = st.selectbox(
        "결혼상태 MARRIAGE", [1, 2, 3],
        format_func=lambda x: {1:"기혼 (1)",2:"미혼 (2)",3:"기타 (3)"}[x]
    )
    AGE = st.number_input("나이 AGE", min_value=18, max_value=100, value=30)

    st.divider()

    # ② 납부 상태
    st.markdown("### ② 납부 상태 (PAY)")
    st.caption("-2 소비없음 / -1 정상 / 0 리볼빙 / 1~8 연체 개월수")

    PAY_OPTS   = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8]
    PAY_LABELS = {
        -2:"-2  소비없음", -1:"-1  정상납부", 0:" 0  리볼빙",
         1:" 1  1개월 연체", 2:" 2  2개월 연체", 3:" 3  3개월 연체",
         4:" 4  4개월 연체", 5:" 5  5개월 연체", 6:" 6  6개월 연체",
         7:" 7  7개월 연체", 8:" 8  8개월+ 연체",
    }
    PAY_0 = st.selectbox("PAY_0  (9월 — 최근)", PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
    PAY_2 = st.selectbox("PAY_2  (8월)",         PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
    PAY_3 = st.selectbox("PAY_3  (7월)",         PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
    PAY_4 = st.selectbox("PAY_4  (6월)",         PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
    PAY_5 = st.selectbox("PAY_5  (5월)",         PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
    PAY_6 = st.selectbox("PAY_6  (4월)",         PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])

# ═══════════════════════════════════════════════════════════════
# MAIN ── 청구/납부 금액  +  예측 버튼  +  결과
# ═══════════════════════════════════════════════════════════════
st.title("💳 신용카드 연체확률 예측 서비스")
st.caption("왼쪽 사이드바에서 **기본 정보**와 **납부 상태**를 먼저 입력하세요.  |  모델: RFC + SMOTE + PCA(15)")
st.divider()

# ③ 청구 금액  &  ④ 납부 금액 — 탭으로 분리
tab3, tab4 = st.tabs(["📄  ③ 청구 금액 (BILL_AMT)", "💸  ④ 납부 금액 (PAY_AMT)"])

with tab3:
    st.caption("단위 : NTD  |  범위 : 0 ~ 10,000,000")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        BILL_AMT1 = st.number_input("BILL_AMT1  (9월)", min_value=0, max_value=10_000_000, value=50_000, step=1_000)
        BILL_AMT4 = st.number_input("BILL_AMT4  (6월)", min_value=0, max_value=10_000_000, value=50_000, step=1_000)
    with col_b:
        BILL_AMT2 = st.number_input("BILL_AMT2  (8월)", min_value=0, max_value=10_000_000, value=50_000, step=1_000)
        BILL_AMT5 = st.number_input("BILL_AMT5  (5월)", min_value=0, max_value=10_000_000, value=50_000, step=1_000)
    with col_c:
        BILL_AMT3 = st.number_input("BILL_AMT3  (7월)", min_value=0, max_value=10_000_000, value=50_000, step=1_000)
        BILL_AMT6 = st.number_input("BILL_AMT6  (4월)", min_value=0, max_value=10_000_000, value=50_000, step=1_000)

with tab4:
    st.caption("단위 : NTD  |  범위 : 0 ~ 10,000,000")
    col_d, col_e, col_f = st.columns(3)
    with col_d:
        PAY_AMT1 = st.number_input("PAY_AMT1  (9월)", min_value=0, max_value=10_000_000, value=5_000, step=500)
        PAY_AMT4 = st.number_input("PAY_AMT4  (6월)", min_value=0, max_value=10_000_000, value=5_000, step=500)
    with col_e:
        PAY_AMT2 = st.number_input("PAY_AMT2  (8월)", min_value=0, max_value=10_000_000, value=5_000, step=500)
        PAY_AMT5 = st.number_input("PAY_AMT5  (5월)", min_value=0, max_value=10_000_000, value=5_000, step=500)
    with col_f:
        PAY_AMT3 = st.number_input("PAY_AMT3  (7월)", min_value=0, max_value=10_000_000, value=5_000, step=500)
        PAY_AMT6 = st.number_input("PAY_AMT6  (4월)", min_value=0, max_value=10_000_000, value=5_000, step=500)

# ── EX-03 : 입력값 유효성 검사 ───────────────────────────────────
st.divider()
input_data = {
    'LIMIT_BAL': LIMIT_BAL, 'SEX': SEX,      'EDUCATION': EDUCATION,
    'MARRIAGE':  MARRIAGE,  'AGE': AGE,
    'PAY_0': PAY_0, 'PAY_2': PAY_2, 'PAY_3': PAY_3,
    'PAY_4': PAY_4, 'PAY_5': PAY_5, 'PAY_6': PAY_6,
    'BILL_AMT1': BILL_AMT1, 'BILL_AMT2': BILL_AMT2, 'BILL_AMT3': BILL_AMT3,
    'BILL_AMT4': BILL_AMT4, 'BILL_AMT5': BILL_AMT5, 'BILL_AMT6': BILL_AMT6,
    'PAY_AMT1':  PAY_AMT1,  'PAY_AMT2':  PAY_AMT2,  'PAY_AMT3':  PAY_AMT3,
    'PAY_AMT4':  PAY_AMT4,  'PAY_AMT5':  PAY_AMT5,  'PAY_AMT6':  PAY_AMT6,
}

val_errors = []
if not (10_000 <= LIMIT_BAL <= 1_000_000):
    val_errors.append("신용한도(LIMIT_BAL)가 유효 범위(10,000 ~ 1,000,000)를 벗어났습니다")
if not (18 <= AGE <= 100):
    val_errors.append("나이(AGE)가 유효 범위(18 ~ 100)를 벗어났습니다")
for err in val_errors:
    st.warning(f"⚠️ {err}")

# EX-02 : 유효성 오류 시 버튼 비활성화
btn = st.button("🔍  예측하기", type="primary", use_container_width=True,
                disabled=len(val_errors) > 0)

# ═══════════════════════════════════════════════════════════════
# 예측 실행 + 결과 출력
# ═══════════════════════════════════════════════════════════════
if btn:
    try:
        with st.spinner("예측 중..."):
            df   = pd.DataFrame([input_data], columns=FEATURE_COLS)
            prob = float(pipeline.predict_proba(df)[0][1])

        # EX-04 : 예측값 범위 검사
        if not (0.0 <= prob <= 1.0):
            st.error("❌ 예측에 실패했습니다. 입력값을 확인해주세요.")
            st.stop()

        risk     = get_risk(prob)
        prob_pct = prob * 100

        # ── 결과 카드 ─────────────────────────────────────────────
        st.subheader("📊 예측 결과")

        res1, res2, res3 = st.columns([1.2, 1.2, 1.6])

        with res1:
            with st.container(border=True):
                st.metric("🎯 연체확률", f"{prob_pct:.1f} %")
                st.progress(prob)

        with res2:
            with st.container(border=True):
                st.metric("🏷️ 위험등급", f"{risk['icon']}  {risk['level']}")
                st.caption(f"구간: {'p ≥ 0.7' if risk['level']=='위험' else '0.5 ≤ p < 0.7' if risk['level']=='경고' else '0.3 ≤ p < 0.5' if risk['level']=='주의' else 'p < 0.3'}")

        with res3:
            with st.container(border=True):
                st.markdown("**💡 권장조치**")
                if risk["msg_type"] == "error":
                    st.error(f"{risk['icon']} **{risk['level']}** — {risk['action']}")
                elif risk["msg_type"] == "warning":
                    st.warning(f"{risk['icon']} **{risk['level']}** — {risk['action']}")
                else:
                    st.success(f"{risk['icon']} **{risk['level']}** — {risk['action']}")

        st.divider()

        # ── 입력값 요약 테이블 (FR-07) ───────────────────────────
        with st.expander("📋 입력 요약 테이블 보기", expanded=False):
            edu_map = {1:"대학원", 2:"대학", 3:"고졸", 4:"기타"}
            mar_map = {1:"기혼",   2:"미혼", 3:"기타"}

            summary_df = pd.DataFrame([
                {"항목": "신용한도 (LIMIT_BAL)",        "입력값": f"{LIMIT_BAL:,} NTD"},
                {"항목": "성별 (SEX)",                  "입력값": "남성" if SEX == 1 else "여성"},
                {"항목": "교육수준 (EDUCATION)",         "입력값": edu_map[EDUCATION]},
                {"항목": "결혼상태 (MARRIAGE)",          "입력값": mar_map[MARRIAGE]},
                {"항목": "나이 (AGE)",                  "입력값": f"{AGE}세"},
                {"항목": "납부상태 PAY_0/2/3/4/5/6",    "입력값": f"{PAY_0} / {PAY_2} / {PAY_3} / {PAY_4} / {PAY_5} / {PAY_6}"},
                {"항목": "청구금액 BILL_AMT1~6 (NTD)",  "입력값": f"{BILL_AMT1:,} / {BILL_AMT2:,} / {BILL_AMT3:,} / {BILL_AMT4:,} / {BILL_AMT5:,} / {BILL_AMT6:,}"},
                {"항목": "납부금액 PAY_AMT1~6 (NTD)",   "입력값": f"{PAY_AMT1:,} / {PAY_AMT2:,} / {PAY_AMT3:,} / {PAY_AMT4:,} / {PAY_AMT5:,} / {PAY_AMT6:,}"},
                {"항목": "▶ 예측 연체확률",             "입력값": f"{prob_pct:.1f} %"},
                {"항목": "▶ 위험등급",                  "입력값": f"{risk['icon']} {risk['level']}"},
                {"항목": "▶ 권장조치",                  "입력값": risk["action"]},
            ])
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # EX-05 : 모델 추론 오류
    except Exception as e:
        st.error(f"❌ 서비스 오류가 발생했습니다: {e}")
