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
def rule_based_proba_row(row: pd.Series) -> float:
    """sklearn 없이도 돌아가는 간단 확률(현재 Prediction의 fallback 로직과 동일 계열)"""
    proba = 0.15
    if TENURE_COL and pd.notna(row.get(TENURE_COL)) and float(row[TENURE_COL]) < 12:
        proba += 0.30
    if MONTHLY_COL and pd.notna(row.get(MONTHLY_COL)) and float(row[MONTHLY_COL]) > 85:
        proba += 0.15
    if CONTRACT_COL and pd.notna(row.get(CONTRACT_COL)) and str(row[CONTRACT_COL]).lower().startswith("month"):
        proba += 0.12
    if TECH_COL and pd.notna(row.get(TECH_COL)) and str(row[TECH_COL]).lower() == "no":
        proba += 0.18
    if SEC_COL and pd.notna(row.get(SEC_COL)) and str(row[SEC_COL]).lower() == "no":
        proba += 0.16
    return float(np.clip(proba, 0.01, 0.95))


def score_df_rule(df_in: pd.DataFrame) -> pd.DataFrame:
    """전체 고객에 churn_proba(확률) 컬럼을 생성(룰 기반이라 100% 동작)"""
    out = df_in.copy()
    out["churn_proba"] = out.apply(rule_based_proba_row, axis=1)
    return out


def apply_actions_rule(df_in: pd.DataFrame, actions: list) -> pd.DataFrame:
    """What-if 액션을 피처에 반영 (룰 기반 시뮬레이션용)"""
    x = df_in.copy()
    for a in actions:
        if a == "TechSupport -> Yes" and TECH_COL and TECH_COL in x.columns:
            x[TECH_COL] = "Yes"
        elif a == "OnlineSecurity -> Yes" and SEC_COL and SEC_COL in x.columns:
            x[SEC_COL] = "Yes"
        elif a == "Contract -> One year" and CONTRACT_COL and CONTRACT_COL in x.columns:
            x[CONTRACT_COL] = "One year"
        elif a == "MonthlyCharges -10%" and MONTHLY_COL and MONTHLY_COL in x.columns:
            x[MONTHLY_COL] = pd.to_numeric(x[MONTHLY_COL], errors="coerce") * 0.9
    return x

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
    if st.button("📌 Simulator", use_container_width=True):
        st.session_state.page = "Simulator"

st.write("")


# -----------------------------
# Pages
# -----------------------------
if st.session_state.page == "Overview":

    # -----------------------------
    # 0) 룰 기반 스코어 (항상 동작)
    # -----------------------------
    def _rule_proba_row(row: pd.Series) -> float:
        proba = 0.15
        if TENURE_COL and pd.notna(row.get(TENURE_COL)) and float(row[TENURE_COL]) < 12:
            proba += 0.30
        if MONTHLY_COL and pd.notna(row.get(MONTHLY_COL)) and float(row[MONTHLY_COL]) > 85:
            proba += 0.15
        if CONTRACT_COL and pd.notna(row.get(CONTRACT_COL)) and str(row[CONTRACT_COL]).lower().startswith("month"):
            proba += 0.12
        if TECH_COL and pd.notna(row.get(TECH_COL)) and str(row[TECH_COL]).lower() == "no":
            proba += 0.18
        if SEC_COL and pd.notna(row.get(SEC_COL)) and str(row[SEC_COL]).lower() == "no":
            proba += 0.16
        return float(np.clip(proba, 0.01, 0.95))

    df_over = df.copy()
    df_over["churn_proba"] = df_over.apply(_rule_proba_row, axis=1)

    # -----------------------------
    # 1) KPI (기준 고정 0.70)
    # -----------------------------
    risk_cut = 0.70

    total_customers = len(df_over)
    cr = churn_rate(df_over)

    high_risk = df_over[df_over["churn_proba"] >= risk_cut]
    high_risk_n = len(high_risk)

    has_value = bool(TOTAL_COL and TOTAL_COL in df_over.columns)
    top_value_risk_n = np.nan
    at_risk_revenue = np.nan

    if has_value:
        df_over[TOTAL_COL] = pd.to_numeric(df_over[TOTAL_COL], errors="coerce")
        tmp = df_over.dropna(subset=[TOTAL_COL]).copy()
        if len(tmp) > 10:
            tmp["value_q"] = pd.qcut(tmp[TOTAL_COL], 4, labels=["Low","Mid","High","Top"])
            top_value_risk = tmp[(tmp["value_q"].astype(str)=="Top") & (tmp["churn_proba"]>=risk_cut)]
            top_value_risk_n = len(top_value_risk)
            at_risk_revenue = top_value_risk[TOTAL_COL].sum()

    st.subheader("Overview")
    st.caption("High Risk 기준: 0.70 (고정)")

    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi_card("전체 고객 수", f"{total_customers:,}")
    with k2: kpi_card("전체 이탈률", fmt_pct(cr))
    with k3: kpi_card("High Risk 고객 수", f"{high_risk_n:,}")
    with k4:
        if has_value:
            kpi_card("Top Value & High Risk", f"{int(top_value_risk_n):,}")
        else:
            kpi_card("Top Value & High Risk", "—")
    with k5:
        if has_value:
            kpi_card("At-risk 매출(합)", fmt_money(at_risk_revenue))
        else:
            kpi_card("At-risk 매출(합)", "—")

    st.write("")

    # -----------------------------
    # 2) Driver Gap 3개
    # -----------------------------
    def _gap_rate(df_in, cond_a, cond_b):
        if "Churn" not in df_in.columns:
            return np.nan
        a = df_in.loc[cond_a,"Churn"].astype(str).str.lower().eq("yes").mean()*100
        b = df_in.loc[cond_b,"Churn"].astype(str).str.lower().eq("yes").mean()*100
        return float(a-b)

    d1,d2,d3 = st.columns(3)

    with d1:
        st.markdown("#### 계약 형태")
        if CONTRACT_COL:
            s = df_over[CONTRACT_COL].astype(str)
            gap = _gap_rate(df_over, s.str.lower().str.startswith("month"), ~s.str.lower().str.startswith("month"))
            st.metric("월단위 - 장기 갭", f"{gap:.1f}%p")
        else:
            st.write("데이터 부족")
    

    with d2:
        st.markdown("#### 문제 해결 경험")
        feat = TECH_COL if TECH_COL else SEC_COL
        if feat:
            s = df_over[feat].astype(str).str.lower()
            gap = _gap_rate(df_over, s.eq("no"), s.eq("yes"))
            st.metric("미이용 - 이용 갭", f"{gap:.1f}%p")
        else:
            st.write("데이터 부족")

    with d3:
        st.markdown("#### 가입 초기")
        if TENURE_COL:
            t = pd.to_numeric(df_over[TENURE_COL], errors="coerce")
            gap = _gap_rate(df_over, t<12, t>=12)
            st.metric("초기<12 - 그 외 갭", f"{gap:.1f}%p")
        else:
            st.write("데이터 부족")

    st.write("")

    # -----------------------------
    # 3) 분포 + Top 10
    # -----------------------------
    left,mid,right = st.columns([1,1,1.2], gap="large")

    with left:
        st.subheader("Risk 분포")
        bins = pd.cut(df_over["churn_proba"],
                      bins=[0,0.4,0.7,1.0],
                      labels=["Low","Mid","High"],
                      include_lowest=True)
        dist = bins.value_counts().reindex(["Low","Mid","High"]).fillna(0)

        fig,ax = plt.subplots()
        ax.bar(dist.index.astype(str), dist.values, color="#9BA986")
        apply_light_style(ax,"Risk Bucket")
        st.pyplot(fig, clear_figure=True)

    with mid:
        st.subheader("가입기간별 이탈률")
        if TENURE_COL:
            tmp = df_over[[TENURE_COL,"Churn"]].dropna()
            tmp[TENURE_COL]=pd.to_numeric(tmp[TENURE_COL],errors="coerce")
            tmp["tenure_bin"]=pd.cut(tmp[TENURE_COL],
                                     bins=[-1,6,12,24,48,72,999],
                                     labels=["0-6","7-12","13-24","25-48","49-72","72+"])
            tmp["is_churn"]=tmp["Churn"].astype(str).str.lower().eq("yes").astype(int)
            rate = tmp.groupby("tenure_bin",observed=True)["is_churn"].mean()*100

            fig,ax = plt.subplots()
            ax.plot(rate.index.astype(str),rate.values,marker="o",color="#9BA986")
            apply_light_style(ax,"Churn by Tenure")
            st.pyplot(fig,clear_figure=True)
        else:
            st.write("데이터 부족")

    with right:
        st.subheader("우선 타겟 Top 10")
        top = df_over.sort_values("churn_proba",ascending=False).head(10)
        cols=[]
        for c in ["customerID",TENURE_COL,MONTHLY_COL,CONTRACT_COL,TECH_COL,SEC_COL,TOTAL_COL,"churn_proba","Churn"]:
            if c and c in top.columns and c not in cols:
                cols.append(c)
        st.dataframe(top[cols] if cols else top,
                     use_container_width=True,
                     height=350)

    

elif st.session_state.page == "EDA":

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


elif st.session_state.page == "Prediction":
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


elif st.session_state.page == "Simulator":

    st.subheader("Strategy Simulator (간단 시뮬레이션)")
    st.markdown(
        "<div class='small-muted'>세그먼트(누구에게) + 액션(무엇을) + 기대효과(얼마나)를 간단 룰로 계산합니다.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    # 1) 룰 기반으로 전체 스코어 생성 (항상 동작)
    df_scored = score_df_rule(df)

    # 2) 세그먼트 만들기: Risk(확률) / Value(총매출) 있으면 같이, 없으면 Risk만
    if TOTAL_COL and TOTAL_COL in df_scored.columns:
        base = df_scored.dropna(subset=[TOTAL_COL]).copy()
        base[TOTAL_COL] = pd.to_numeric(base[TOTAL_COL], errors="coerce")
        base = base.dropna(subset=[TOTAL_COL])

        # 분위수로 간단 구간
        base["risk_q"] = pd.qcut(base["churn_proba"], 4, labels=["Low", "Mid", "High", "Top"])
        base["value_q"] = pd.qcut(base[TOTAL_COL], 4, labels=["Low", "Mid", "High", "Top"])
        base["segment"] = base["value_q"].astype(str) + " / " + base["risk_q"].astype(str)
    else:
        base = df_scored.copy()
        base["risk_q"] = pd.qcut(base["churn_proba"], 4, labels=["Low", "Mid", "High", "Top"])
        base["segment"] = "RiskOnly / " + base["risk_q"].astype(str)

    left, right = st.columns([0.9, 1.1], gap="large")

    with left:
        st.markdown("#### 1) 타겟 세그먼트")
        seg_options = base["segment"].value_counts().index.tolist()
        seg = st.selectbox("세그먼트 선택", options=seg_options, index=0)

        pool = base[base["segment"] == seg].sort_values("churn_proba", ascending=False).copy()

        st.markdown("#### 2) 타겟팅 강도")
        treat_ratio = st.slider("상위 위험 고객 중 몇 %를 대상으로 할까요?", 0.05, 1.00, 0.30, 0.05)
        k = max(1, int(len(pool) * treat_ratio))
        target = pool.head(k).copy()

        st.markdown("#### 3) 액션(What-if)")
        action_choices = []
        st.caption(
"※ 캠페인은 고객 이탈을 방지하기 위한 유지 전략입니다. "
"예: TechSupport 제공, 장기 계약 전환, 요금 할인 등"
)
        if TECH_COL: action_choices.append("TechSupport -> Yes")
        if SEC_COL: action_choices.append("OnlineSecurity -> Yes")
        if CONTRACT_COL: action_choices.append("Contract -> One year")
        if MONTHLY_COL: action_choices.append("MonthlyCharges -10%")

        actions = st.multiselect("적용할 액션(가정)", options=action_choices, default=action_choices[:1] if action_choices else [])

        st.markdown("#### 4) 비용/가치(ROI)")
        st.caption(
"ROI = (기대 매출 방어 - 총 캠페인 비용) / 총 캠페인 비용"
)
        value_per_saved = st.number_input("이탈 1건 방어 가치(원)", min_value=0, value=150000, step=10000)
        cost_per_target = st.number_input("타겟 1명당 캠페인 비용(원)", min_value=0, value=5000, step=500)

        st.write("---")
        st.write(f"- 후보 고객 수: **{len(pool):,}**")
        st.write(f"- 실제 타겟 수: **{len(target):,}**")

    with right:
        st.markdown("#### 결과(기대값)")
        if len(target) == 0:
            st.info("타겟이 없습니다.")
        else:
            # Before
            before = target.copy()

            # After: 액션 적용 → 다시 스코어
            after_features = apply_actions_rule(target, actions)
            after = score_df_rule(after_features)

            expected_before = float(before["churn_proba"].clip(0, 1).sum())
            expected_after = float(after["churn_proba"].clip(0, 1).sum())
            expected_saved = float((before["churn_proba"] - after["churn_proba"]).clip(0, 1).sum())

            revenue_saved = expected_saved * float(value_per_saved)
            total_cost = float(cost_per_target) * len(target)
            roi = (revenue_saved - total_cost) / total_cost if total_cost > 0 else np.nan

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("기대 이탈(전)", f"{expected_before:.1f} 건")
            with m2:
                st.metric("기대 이탈(후)", f"{expected_after:.1f} 건", delta=f"{(expected_after-expected_before):.1f} 건")
            with m3:
                st.metric("기대 방어 이탈", f"{expected_saved:.1f} 건")
            with m4:
                st.metric("기대 매출 방어", f"{revenue_saved:,.0f} 원")

            st.write("---")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("총 캠페인 비용", f"{total_cost:,.0f} 원")
            with c2:
                st.metric("순효과(매출-비용)", f"{(revenue_saved-total_cost):,.0f} 원")
            with c3:
                st.metric("ROI", "—" if pd.isna(roi) else f"{roi*100:.1f}%")

            st.write("---")
            st.markdown("#### 타겟 리스트(상위 위험도 30명)")
            show_cols = []
            for c in ["customerID", "CustomerID", TENURE_COL, MONTHLY_COL, CONTRACT_COL, TECH_COL, SEC_COL, TOTAL_COL, "churn_proba", "Churn"]:
                if c and c in before.columns and c not in show_cols:
                    show_cols.append(c)

            if show_cols:
                st.dataframe(before[show_cols].head(30), use_container_width=True, height=360)
            else:
                st.dataframe(before.head(30), use_container_width=True, height=360)

            st.markdown(
                "<div class='small-muted'>주의: 룰 기반 기대값(확률 합) 시뮬레이션입니다. 실제 운영에서는 A/B 테스트로 효과(uplift)를 검증합니다.</div>",
                unsafe_allow_html=True,
            )

