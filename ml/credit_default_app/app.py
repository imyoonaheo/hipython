"""
app.py — 신용카드 채무불이행 예측 Streamlit 웹 서비스
실행 : conda activate ml_edu  →  streamlit run app.py
"""

import streamlit as st
from predict import predict

# ── 페이지 기본 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="신용카드 채무불이행 예측",
    page_icon="💳",
    layout="wide",
)

st.title("💳 신용카드 채무불이행 고객 예측")
st.caption("고객 정보를 입력하고 **예측하기** 버튼을 누르세요. (모델: RFC + SMOTE + PCA15)")
st.divider()

# ── ① 기본 고객 정보 ──────────────────────────────────────────────
st.subheader("① 기본 고객 정보")
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    LIMIT_BAL = st.number_input(
        "신용한도 LIMIT_BAL",
        min_value=10_000, max_value=1_000_000,
        value=200_000, step=10_000,
        help="단위: NTD (신대만달러)"
    )
with c2:
    SEX = st.selectbox(
        "성별 SEX",
        options=[1, 2],
        format_func=lambda x: "남성 (1)" if x == 1 else "여성 (2)"
    )
with c3:
    EDUCATION = st.selectbox(
        "교육수준 EDUCATION",
        options=[1, 2, 3, 4],
        format_func=lambda x: {1: "대학원 (1)", 2: "대학 (2)",
                                3: "고등학교 (3)", 4: "기타 (4)"}[x]
    )
with c4:
    MARRIAGE = st.selectbox(
        "결혼상태 MARRIAGE",
        options=[1, 2, 3],
        format_func=lambda x: {1: "기혼 (1)", 2: "미혼 (2)", 3: "기타 (3)"}[x]
    )
with c5:
    AGE = st.number_input("나이 AGE", min_value=21, max_value=79, value=30)

# ── ② 납부 상태 ───────────────────────────────────────────────────
st.subheader("② 납부 상태 (PAY)")
st.caption("-2 소비없음 / -1 정상납부 / 0 리볼빙 / 1~8 연체 개월수")

PAY_OPTS   = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8]
PAY_LABELS = {
    -2: "-2 (소비없음)",   -1: "-1 (정상납부)",   0: " 0 (리볼빙)",
     1: " 1 (1개월 연체)",  2: " 2 (2개월 연체)",  3: " 3 (3개월 연체)",
     4: " 4 (4개월 연체)",  5: " 5 (5개월 연체)",  6: " 6 (6개월 연체)",
     7: " 7 (7개월 연체)",  8: " 8 (8개월+ 연체)",
}

p1, p2, p3, p4, p5, p6 = st.columns(6)
with p1: PAY_0 = st.selectbox("PAY_0 (9월)", PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
with p2: PAY_2 = st.selectbox("PAY_2 (8월)", PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
with p3: PAY_3 = st.selectbox("PAY_3 (7월)", PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
with p4: PAY_4 = st.selectbox("PAY_4 (6월)", PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
with p5: PAY_5 = st.selectbox("PAY_5 (5월)", PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])
with p6: PAY_6 = st.selectbox("PAY_6 (4월)", PAY_OPTS, index=2, format_func=lambda x: PAY_LABELS[x])

# ── ③ 청구 금액 ───────────────────────────────────────────────────
st.subheader("③ 청구 금액 (BILL_AMT, 단위: NTD)")
b1, b2, b3, b4, b5, b6 = st.columns(6)
with b1: BILL_AMT1 = st.number_input("BILL_AMT1 (9월)", value=50_000, step=1_000)
with b2: BILL_AMT2 = st.number_input("BILL_AMT2 (8월)", value=50_000, step=1_000)
with b3: BILL_AMT3 = st.number_input("BILL_AMT3 (7월)", value=50_000, step=1_000)
with b4: BILL_AMT4 = st.number_input("BILL_AMT4 (6월)", value=50_000, step=1_000)
with b5: BILL_AMT5 = st.number_input("BILL_AMT5 (5월)", value=50_000, step=1_000)
with b6: BILL_AMT6 = st.number_input("BILL_AMT6 (4월)", value=50_000, step=1_000)

# ── ④ 납부 금액 ───────────────────────────────────────────────────
st.subheader("④ 납부 금액 (PAY_AMT, 단위: NTD)")
a1, a2, a3, a4, a5, a6 = st.columns(6)
with a1: PAY_AMT1 = st.number_input("PAY_AMT1 (9월)", min_value=0, value=5_000, step=500)
with a2: PAY_AMT2 = st.number_input("PAY_AMT2 (8월)", min_value=0, value=5_000, step=500)
with a3: PAY_AMT3 = st.number_input("PAY_AMT3 (7월)", min_value=0, value=5_000, step=500)
with a4: PAY_AMT4 = st.number_input("PAY_AMT4 (6월)", min_value=0, value=5_000, step=500)
with a5: PAY_AMT5 = st.number_input("PAY_AMT5 (5월)", min_value=0, value=5_000, step=500)
with a6: PAY_AMT6 = st.number_input("PAY_AMT6 (4월)", min_value=0, value=5_000, step=500)

# ── 예측 버튼 ─────────────────────────────────────────────────────
st.divider()
btn = st.button("🔍 예측하기", type="primary", use_container_width=True)

if btn:
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

    with st.spinner("예측 중..."):
        result = predict(input_data)

    # ── 결과 출력 ─────────────────────────────────────────────────
    st.subheader("📊 예측 결과")
    r1, r2, r3 = st.columns([1, 1, 2])

    with r1:
        st.metric("채무불이행 확률", f"{result['prob'] * 100:.1f} %")

    with r2:
        st.metric("예측 클래스", f"{'채무불이행 (1)' if result['label'] == 1 else '정상 (0)'}")

    with r3:
        prob_pct = result['prob'] * 100
        if prob_pct >= 50:
            st.error(f"⚠️  위험   채무불이행 확률 {prob_pct:.1f}%")
        elif prob_pct >= 30:
            st.warning(f"🟡  주의   채무불이행 확률 {prob_pct:.1f}%")
        else:
            st.success(f"✅  안전   채무불이행 확률 {prob_pct:.1f}%")

    st.progress(result['prob'], text=f"확률 게이지  {result['prob'] * 100:.1f}%")
