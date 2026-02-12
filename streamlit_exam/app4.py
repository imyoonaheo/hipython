# app.py
import os
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Telco Churn Dashboard",
    page_icon="📶",
    layout="wide",
)

# -----------------------------
# Style 
# -----------------------------
CSS = """
<style>
/* 1. 전체 폰트 및 배경 설정 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background-color: #EDEAE5; /* 팔레트 1번: 차분한 베이지 그레이 */
}

/* 2. 카드 디자인 (KPI, 패널 공통) */
.stMarkdown div[data-testid="stMarkdownContainer"] > p {
    color: #4A5141; /* 진한 올리브 그린 텍스트 */
}

.kpi, .panel {
    background-color: #F3F3EA; /* 팔레트 2번: 밝은 미색으로 카드 배경 */
    border-radius: 12px;
    padding: 24px;
    box-shadow: none; /* 그라데이션 대신 플랫한 디자인을 위해 그림자 제거 또는 최소화 */
    border: 1px solid #DDDFD1; /* 팔레트 3번: 경계선 */
    margin-bottom: 20px;
}

/* 3. 상단 히어로 섹션 (그라데이션 제거) */
.hero {
    background-color: #9BA986; /* 팔레트 4번: 세이지 그린 단색 적용 */
    border-radius: 12px;
    padding: 35px;
    color: white !important;
    margin-bottom: 30px;
    border-bottom: 4px solid #EDDCAE; /* 하단에 팔레트 5번 포인트 라인 */
}
.hero h1 { 
    color: white !important; 
    font-weight: 700; 
    letter-spacing: -0.02em;
    margin-bottom: 8px;
}
.hero div, .hero span { color: #F3F3EA !important; }

/* 4. KPI 숫자 강조 */
.kpi .label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #9BA986;
    letter-spacing: 0.02em;
}
.kpi .value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #4A5141;
}

/* 5. 버튼 스타일링 */
.stButton>button {
    border-radius: 8px;
    border: 1px solid #DDDFD1;
    background-color: #F3F3EA;
    color: #5A634D;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    background-color: #9BA986;
    color: white;
    border-color: #9BA986;
}

/* 6. 데이터프레임 스타일 */
[data-testid="stDataFrame"] {
    border: 1px solid #DDDFD1;
    border-radius: 8px;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -----------------------------
# Utilities
# -----------------------------
def _coerce_total_charges(s: pd.Series) -> pd.Series:
    # Common in telco churn data: TotalCharges has blanks/spaces
    return pd.to_numeric(s.astype(str).str.strip().replace({"": np.nan, "nan": np.nan}), errors="coerce")

def _standardize_churn(df: pd.DataFrame) -> pd.DataFrame:
    # Make Churn values: Yes/No
    if "Churn" in df.columns:
        df["Churn"] = df["Churn"].astype(str).str.strip()
        df["Churn"] = df["Churn"].replace({"1": "Yes", "0": "No", "True": "Yes", "False": "No"})
    return df

def _find_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

@st.cache_data(show_spinner=False)
def load_data(path=r"C:\Users\Admin\hipython\통신사 데이터셋\data\cust_data_v1.csv") -> pd.DataFrame:
    if os.path.exists(path):
        df = pd.read_csv(path)
        df = _standardize_churn(df)
        # normalize key numeric cols if present
        if "TotalCharges" in df.columns:
            df["TotalCharges"] = _coerce_total_charges(df["TotalCharges"])
        if "MonthlyCharges" in df.columns:
            df["MonthlyCharges"] = pd.to_numeric(df["MonthlyCharges"], errors="coerce")
        if "tenure" in df.columns:
            df["tenure"] = pd.to_numeric(df["tenure"], errors="coerce")
        return df
 

    # Fallback demo dataset (so the app still runs)
    rng = np.random.default_rng(7)
    n = 1200
    tenure = rng.integers(0, 72, size=n)
    monthly = np.clip(rng.normal(70, 25, size=n), 18, 130)
    tech = rng.choice(["Yes", "No"], size=n, p=[0.45, 0.55])
    sec = rng.choice(["Yes", "No"], size=n, p=[0.42, 0.58])
    contract = rng.choice(["Month-to-month", "One year", "Two year"], size=n, p=[0.55, 0.25, 0.20])
    gender = rng.choice(["Female", "Male"], size=n)

    # churn probability (simple synthetic logic)
    p = (
        0.15
        + 0.35 * (tenure < 12)
        + 0.15 * (monthly > 85)
        + 0.20 * (tech == "No")
        + 0.18 * (sec == "No")
        + 0.12 * (contract == "Month-to-month")
    )
    p = np.clip(p, 0.02, 0.92)
    churn = rng.binomial(1, p, size=n)
    total = monthly * np.maximum(tenure, 1)

    df = pd.DataFrame({
        "Churn": np.where(churn == 1, "Yes", "No"),
        "tenure": tenure,
        "MonthlyCharges": monthly.round(2),
        "TotalCharges": total.round(2),
        "Contract": contract,
        "gender": gender,
        "TechSupport": tech,
        "OnlineSecurity": sec,
        "InternetService": rng.choice(["DSL", "Fiber optic", "No"], size=n, p=[0.35, 0.50, 0.15]),
    })
    return df

def churn_rate(df: pd.DataFrame) -> float:
    if "Churn" not in df.columns:
        return np.nan
    return (df["Churn"].astype(str).str.lower().eq("yes").mean()) * 100

def fmt_money(x):
    if pd.isna(x):
        return "—"
    return f"{x:,.0f}"

def fmt_pct(x):
    if pd.isna(x):
        return "—"
    return f"{x:.1f}%"

def kpi_card(label, value, delta_text=None):
    delta_html = f'<div class="delta">{delta_text}</div>' if delta_text else ""
    st.markdown(
        f"""
        <div class="kpi">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    
def apply_light_style(ax, title):
    # 1. 그래프 크기 고정 (가로 4인치, 세로 2.8인치로 대폭 축소)
    ax.figure.set_size_inches(4, 2.8)
    
    # 2. 폰트 사이즈 조절 (크기가 줄어들므로 글자도 작게)
    ax.set_title(title, fontsize=10, fontweight='bold', color='#1e293b', pad=10)
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.xaxis.label.set_size(8)
    ax.yaxis.label.set_size(8)
    
    # 3. 스타일링
    ax.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#e2e8f0')
    ax.spines['bottom'].set_color('#e2e8f0')
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, color='#e2e8f0')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
# -----------------------------
# Data
# -----------------------------
df = load_data()
row_n, col_n = df.shape

# Key columns (allow slight naming differences)
GENDER_COL = _find_col(df, ["gender", "Gender", "Sex"])
CONTRACT_COL = _find_col(df, ["Contract", "contract"])
TENURE_COL = _find_col(df, ["tenure", "Tenure"])
MONTHLY_COL = _find_col(df, ["MonthlyCharges", "monthlycharges", "monthly_charge"])
TOTAL_COL = _find_col(df, ["TotalCharges", "totalcharges", "total_charge"])
TECH_COL = _find_col(df, ["TechSupport", "techsupport"])
SEC_COL = _find_col(df, ["OnlineSecurity", "onlinesecurity"])
PLAN_COL = _find_col(df, ["InternetService", "internetservice", "Plan", "plan"])

# -----------------------------
# Navigation (screen buttons)
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "Overview"

st.markdown(
    f"""
    <div class="hero">
      <div style="display:flex;justify-content:space-between;gap:14px;align-items:flex-start;flex-wrap:wrap;">
        <div>
          <div>
            <span class="badge">📶 Telco</span>
            <span class="badge">Churn</span>
            <span class="badge">Retention</span>
          </div>
          <h1 style="margin:10px 0 6px 0;">통신사 고객 이탈 대시보드</h1>
        </div>
        <div class="small-muted" style="text-align:right;">
        
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

nav_cols = st.columns([1, 1, 1, 1, 6])
with nav_cols[0]:
    if st.button("🏠 Overview", use_container_width=True):
        st.session_state.page = "Overview"
with nav_cols[1]:
    if st.button("🔎 EDA", use_container_width=True):
        st.session_state.page = "EDA"
with nav_cols[2]:
    if st.button("🤖 Prediction", use_container_width=True):
        st.session_state.page = "Prediction"
with nav_cols[3]:
    if st.button("📌 Strategy", use_container_width=True):
        st.session_state.page = "Strategy"

st.write("")

# -----------------------------
# KPIs (always visible)
# -----------------------------
k1, k2, k3, k4 = st.columns(4)

total_customers = len(df)
cr = churn_rate(df)
avg_monthly = df[MONTHLY_COL].mean() if MONTHLY_COL else np.nan
estimated_loss = df.loc[df["Churn"].astype(str).str.lower().eq("yes"), TOTAL_COL].sum() if TOTAL_COL else np.nan

with k1:
    kpi_card("전체 고객 수", f"{total_customers:,}")
with k2:
    kpi_card("이탈률 (Churn Rate)", fmt_pct(cr))
with k3:
    kpi_card("평균 월 요금", fmt_money(avg_monthly))
with k4:
    kpi_card("추정 매출 손실 (TotalCharges 합)", fmt_money(estimated_loss))

st.write("")

# -----------------------------
# Pages
# -----------------------------
if st.session_state.page == "Overview":
    left, right = st.columns([1.2, 1.0], gap="large")
    


    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Project Overview")
        st.write(
            "이 프로젝트는 통신사 고객 이탈(Churn)을 단순 예측 문제가 아니라 "
            "‘경험 누적의 결과’로 보고, 요금·가입기간·서비스 경험·고객가치 관점에서 구조적으로 해석합니다."
        )
        st.markdown(
            """
            <div class="notice">
              <b>분석 질문</b><br/>
              Q1) 요금 수준은 이탈과 어떤 관계가 있는가?<br/>
              Q2) 가입기간(tenure)은 이탈과 어떤 관계가 있는가?<br/>
              Q3) 서비스 이용 경험(지원/보안 등)은 이탈에 어떤 영향을 미치는가?<br/>
              Q4) 이탈 고객 중에서도 반드시 유지해야 할 고객은 누구인가?
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.subheader("Data Preview")
        st.dataframe(df.head(12), use_container_width=True, height=340)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("이탈 분포 (Target Distribution)")
        if "Churn" in df.columns:
            counts = df["Churn"].astype(str).str.title().value_counts()
            fig = plt.figure()
            fig, ax = plt.subplots(figsize=(4, 3))
            plt.bar(counts.index, counts.values, color='#9BA986', width=0.6)
            plt.title("Churn Distribution")
            plt.xlabel("Churn")
            plt.ylabel("Count")
            st.pyplot(fig, clear_figure=True)
            st.markdown(
                f"<div class='small-muted'>현재 이탈 고객 비중은 <b>{fmt_pct(cr)}</b> 입니다.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Churn 컬럼이 없어 분포를 그릴 수 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "EDA":
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("EDA (Q1~Q4 상세 분석)")
    tabs = st.tabs(["Q1 요금", "Q2 가입기간", "Q3 서비스경험", "Q4 고객가치"])

    # ---------- Q1 요금 ----------
    with tabs[0]:
        st.markdown("**관점:** 요금이 높아서 이탈하는가?")
        if MONTHLY_COL and "Churn" in df.columns:
            c1, _ = st.columns([0.6, 0.4]) # 그래프 폭 제한
            with c1:
                fig, ax = plt.subplots()
                yes = df.loc[df["Churn"].astype(str).str.lower().eq("yes"), MONTHLY_COL].dropna()
                no = df.loc[df["Churn"].astype(str).str.lower().eq("no"), MONTHLY_COL].dropna()
                
                # 박스플롯 스타일 (세이지 그린 사용)
                bp = ax.boxplot([no.values, yes.values], labels=["No", "Yes"], patch_artist=True, showfliers=False)
                for patch in bp['boxes']:
                    patch.set_facecolor('#9BA986')
                    patch.set_edgecolor('#4A5141')
                
                apply_light_style(ax, "Monthly Charges by Churn")
                st.pyplot(fig, clear_figure=True)

            if PLAN_COL:
                st.write("---")
                st.write("**(추가) 요금제/서비스 타입별 이탈률**")
                c2, _ = st.columns([0.6, 0.4])
                with c2:
                    tmp = df[[PLAN_COL, "Churn"]].dropna()
                    tmp["is_churn"] = tmp["Churn"].astype(str).str.lower().eq("yes").astype(int)
                    rate = tmp.groupby(PLAN_COL)["is_churn"].mean().sort_values() * 100
                    
                    fig, ax = plt.subplots()
                    ax.barh(rate.index.astype(str), rate.values, color='#9BA986')
                    apply_light_style(ax, f"Churn Rate by {PLAN_COL}")
                    st.pyplot(fig, clear_figure=True)
        else:
            st.info("데이터가 부족하여 시각화할 수 없습니다.")

    # ---------- Q2 가입기간 ----------
    with tabs[1]:
        st.markdown("**관점:** 이탈은 가입 ‘초기’에 집중되는가?")
        if TENURE_COL and "Churn" in df.columns:
            c1, _ = st.columns([0.6, 0.4])
            with c1:
                tmp = df[[TENURE_COL, "Churn"]].dropna()
                tmp["tenure_bin"] = pd.cut(tmp[TENURE_COL], bins=[-1, 3, 6, 12, 24, 36, 48, 60, 72, 999],
                                         labels=["0-3", "4-6", "7-12", "13-24", "25-36", "37-48", "49-60", "61-72", "72+"])
                tmp["is_churn"] = tmp["Churn"].astype(str).str.lower().eq("yes").astype(int)
                rate = tmp.groupby("tenure_bin", observed=True)["is_churn"].mean() * 100

                fig, ax = plt.subplots()
                ax.plot(rate.index.astype(str), rate.values, marker="o", color='#9BA986', linewidth=2)
                apply_light_style(ax, "Churn Rate Trend by Tenure")
                plt.xticks(rotation=45)
                st.pyplot(fig, clear_figure=True)
        else:
            st.info("데이터가 부족하여 시각화할 수 없습니다.")

    # ---------- Q3 서비스경험 ----------
    with tabs[2]:
        st.markdown("**관점:** 문제 해결 경험(지원/보안)의 부재가 이탈을 키우는가?")
        if "Churn" in df.columns:
            col1, col2 = st.columns(2) # Q3는 두 개를 나란히 배치해 크기 조절
            
            with col1:
                if CONTRACT_COL:
                    tmp = df[[CONTRACT_COL, "Churn"]].dropna()
                    tmp["is_churn"] = tmp["Churn"].astype(str).str.lower().eq("yes").astype(int)
                    rate = tmp.groupby(CONTRACT_COL)["is_churn"].mean().sort_values(ascending=False) * 100
                    fig, ax = plt.subplots()
                    ax.bar(rate.index.astype(str), rate.values, color='#9BA986')
                    apply_light_style(ax, "by Contract Type")
                    st.pyplot(fig, clear_figure=True)

            with col2:
                feature = TECH_COL if TECH_COL else SEC_COL
                if feature:
                    tmp = df[[feature, "Churn"]].dropna()
                    tmp["is_churn"] = tmp["Churn"].astype(str).str.lower().eq("yes").astype(int)
                    rate = tmp.groupby(feature)["is_churn"].mean().sort_values(ascending=False) * 100
                    fig, ax = plt.subplots()
                    ax.bar(rate.index.astype(str), rate.values, color='#EDDCAE') # 포인트 컬러 사용
                    apply_light_style(ax, f"by {feature}")
                    st.pyplot(fig, clear_figure=True)
        else:
            st.info("데이터가 부족합니다.")

    # ---------- Q4 고객가치 ----------
    with tabs[3]:
        st.markdown("**관점:** 누구의 이탈이 가장 뼈아픈가? (가치 분석)")
        if TOTAL_COL and "Churn" in df.columns:
            c1, _ = st.columns([0.6, 0.4])
            with c1:
                tmp = df[[TOTAL_COL, "Churn"]].dropna().copy()
                tmp["val_q"] = pd.qcut(tmp[TOTAL_COL], q=5, labels=["Q1(Low)", "Q2", "Q3", "Q4", "Q5(High)"])
                tmp["is_churn"] = tmp["Churn"].astype(str).str.lower().eq("yes").astype(int)
                rate = tmp.groupby("val_q", observed=True)["is_churn"].mean() * 100

                fig, ax = plt.subplots()
                ax.bar(rate.index.astype(str), rate.values, color='#9BA986')
                apply_light_style(ax, "Churn Rate by Value Quintile")
                st.pyplot(fig, clear_figure=True)
            
            st.write("**고가치(Q5) 이탈 고객 리스트 (최상위 10명)**")
            high_churn = df[df["Churn"].astype(str).str.lower() == "yes"].sort_values(by=TOTAL_COL, ascending=False)
            st.dataframe(high_churn.head(10), use_container_width=True)
        else:
            st.info("데이터가 부족합니다.")

    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "Prediction":
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Churn Prediction (입력 → 예측)")
    st.markdown(
        "<div class='small-muted'>간단 모델(가능 시 Logistic Regression) 또는 룰 기반으로 ‘이탈 가능성’을 추정합니다.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    # Try to use sklearn if available
    try:
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import OneHotEncoder
        from sklearn.compose import ColumnTransformer
        from sklearn.pipeline import Pipeline
        from sklearn.linear_model import LogisticRegression
        SKLEARN_OK = True
    except Exception:
        SKLEARN_OK = False

    # Build a minimal feature set based on available columns
    feature_cols = []
    for c in [TENURE_COL, MONTHLY_COL, CONTRACT_COL, GENDER_COL, TECH_COL, SEC_COL, PLAN_COL]:
        if c and c in df.columns:
            feature_cols.append(c)

    if not feature_cols or "Churn" not in df.columns:
        st.info("예측에 필요한 컬럼(Churn 및 주요 피처)이 부족합니다.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Input form
        left, right = st.columns([1.0, 1.2], gap="large")

        with left:
            with st.form("pred_form"):
                st.markdown("#### 고객 정보 입력")
                inputs = {}

                if TENURE_COL:
                    inputs[TENURE_COL] = st.number_input("가입기간(tenure, months)", min_value=0, max_value=200, value=6, step=1)
                if MONTHLY_COL:
                    inputs[MONTHLY_COL] = st.number_input("월 요금(MonthlyCharges)", min_value=0.0, max_value=500.0, value=85.0, step=1.0)

                if GENDER_COL:
                    options = sorted(df[GENDER_COL].dropna().astype(str).unique().tolist())
                    inputs[GENDER_COL] = st.selectbox("성별", options=options, index=0)

                if CONTRACT_COL:
                    options = sorted(df[CONTRACT_COL].dropna().astype(str).unique().tolist())
                    # prefer Month-to-month as default if exists
                    default = options.index("Month-to-month") if "Month-to-month" in options else 0
                    inputs[CONTRACT_COL] = st.selectbox("계약 형태(Contract)", options=options, index=default)

                if PLAN_COL:
                    options = sorted(df[PLAN_COL].dropna().astype(str).unique().tolist())
                    inputs[PLAN_COL] = st.selectbox(f"{PLAN_COL}", options=options, index=0)

                if TECH_COL:
                    options = sorted(df[TECH_COL].dropna().astype(str).unique().tolist())
                    inputs[TECH_COL] = st.selectbox("TechSupport", options=options, index=0)

                if SEC_COL:
                    options = sorted(df[SEC_COL].dropna().astype(str).unique().tolist())
                    inputs[SEC_COL] = st.selectbox("OnlineSecurity", options=options, index=0)

                submitted = st.form_submit_button("예측하기")

        with right:
            st.markdown("#### 결과")

            if not submitted:
                st.markdown(
                    "<div class='notice'>왼쪽에서 값을 입력하고 <b>예측하기</b>를 누르면 결과가 표시됩니다.</div>",
                    unsafe_allow_html=True,
                )
            else:
                x_input = pd.DataFrame([inputs])

                if SKLEARN_OK:
                    # Prepare training data
                    data = df[feature_cols + ["Churn"]].dropna().copy()
                    y = data["Churn"].astype(str).str.lower().eq("yes").astype(int)
                    X = data[feature_cols]

                    num_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]
                    cat_cols = [c for c in feature_cols if c not in num_cols]

                    pre = ColumnTransformer(
                        transformers=[
                            ("num", "passthrough", num_cols),
                            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
                        ]
                    )

                    model = Pipeline(
                        steps=[
                            ("pre", pre),
                            ("clf", LogisticRegression(max_iter=1000)),
                        ]
                    )

                    # Fit (small & quick)
                    model.fit(X, y)
                    proba = float(model.predict_proba(x_input[feature_cols])[:, 1][0])

                else:
                    # Rule-based fallback
                    proba = 0.15
                    if TENURE_COL and x_input[TENURE_COL].iloc[0] < 12:
                        proba += 0.30
                    if MONTHLY_COL and x_input[MONTHLY_COL].iloc[0] > 85:
                        proba += 0.15
                    if CONTRACT_COL and str(x_input[CONTRACT_COL].iloc[0]).lower().startswith("month"):
                        proba += 0.12
                    if TECH_COL and str(x_input[TECH_COL].iloc[0]).lower() == "no":
                        proba += 0.18
                    if SEC_COL and str(x_input[SEC_COL].iloc[0]).lower() == "no":
                        proba += 0.16
                    proba = float(np.clip(proba, 0.01, 0.95))

                pct = proba * 100
                if pct >= 70:
                    level = "High"
                elif pct >= 40:
                    level = "Medium"
                else:
                    level = "Low"

                st.metric("이탈 가능성(추정)", f"{pct:.1f}%")
                st.progress(min(max(proba, 0.0), 1.0))

                st.write(f"위험 레벨: **{level}**")

                # Simple explanation (top factors)
                reasons = []
                if TENURE_COL and inputs.get(TENURE_COL, 999) < 12:
                    reasons.append("가입 초기(tenure < 12개월)")
                if MONTHLY_COL and inputs.get(MONTHLY_COL, 0) > 85:
                    reasons.append("상대적으로 높은 월 요금")
                if CONTRACT_COL and str(inputs.get(CONTRACT_COL, "")).lower().startswith("month"):
                    reasons.append("Month-to-month 계약")
                if TECH_COL and str(inputs.get(TECH_COL, "")).lower() == "no":
                    reasons.append("TechSupport 미이용")
                if SEC_COL and str(inputs.get(SEC_COL, "")).lower() == "no":
                    reasons.append("OnlineSecurity 미이용")

                if reasons:
                    st.markdown("**가능한 원인(설명용):** " + ", ".join(reasons))
                else:
                    st.markdown("**가능한 원인(설명용):** 입력 정보 기준으로 뚜렷한 위험 요인이 적습니다.")

    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "Strategy":
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Business Strategy (분석 결과 → 실행 제안)")
    st.write("")

    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        st.markdown("#### 핵심 인사이트 1")
        st.write("이탈은 ‘장기 사용 중 갑자기’보다 **가입 초기 경험(온보딩/첫 문제 해결)**에서 크게 갈립니다.")

    with c2:
        st.markdown("#### 핵심 인사이트 2")
        st.write("지원/보안 등 **문제 해결 경험(TechSupport/OnlineSecurity)**이 없을 때 이탈이 급증하는 패턴이 나타납니다.")

    with c3:
        st.markdown("#### 핵심 인사이트 3")
        st.write("이탈률만 보면 ‘낮은 가치 고객’이 많지만, **고가치 고객의 이탈은 손실이 비대칭**적으로 큽니다.")

    st.write("")
    st.markdown("#### 전략 매핑 (Insight → Action → KPI)")
    strategy_rows = [
        {
            "Insight": "가입 초기(0~12개월) 이탈 집중",
            "Action": "초기 30일 온보딩(가이드+체크인), 첫 달 문제 해결 SLA 강화",
            "KPI": "D30 잔존율, 초기 CS 해결률, 첫 달 불만 접수율",
        },
        {
            "Insight": "지원/보안 서비스 미이용 고객의 이탈 위험",
            "Action": "TechSupport/OnlineSecurity ‘체험 활성화’ 캠페인 + 번들 구성",
            "KPI": "서비스 활성화율, 서비스 미이용군 이탈률",
        },
        {
            "Insight": "고가치 고객 이탈은 손실이 큼",
            "Action": "고가치·고위험 세그먼트에 전담 유지(혜택/우선 상담/맞춤 요금제)",
            "KPI": "고가치 고객 이탈률, 유지 캠페인 ROI, ARPU 유지",
        },
    ]
    st.dataframe(pd.DataFrame(strategy_rows), use_container_width=True)

    st.write("")
    st.markdown("#### 우선순위 플레이북(권장 세그먼트)")
    st.write(
        "1) **고가치 & 고위험**: tenure 낮고(또는 최근 문제), 지원/보안 미이용 → 즉시 케어\n\n"
        "2) **중가치 & 고위험**: Month-to-month + 서비스 미이용 → 서비스 경험 제공이 핵심\n\n"
        "3) **고가치 & 저위험**: 이탈률은 낮지만 ‘불만 발생 시’ 빠른 해결로 방어"
    )

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Footer note
# -----------------------------
st.write("")
st.markdown(
    "<div class='small-muted'>데이터 파일이 없으면 앱이 데모 데이터로 실행됩니다. 실제 데이터는 <code>data/telco_churn.csv</code> 경로에 두면 자동 로드됩니다.</div>",
    unsafe_allow_html=True,
)
