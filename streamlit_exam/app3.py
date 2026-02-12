import streamlit as st

# layout 요소 2

st.sidebar.radio(
  "이동",
  ["메인페이지","분석보고서","설정"]
)
st.sidebar.metric('접속자수:',
'백만명', "+백만명")

if st.sidebar.button('눌러봐!!'):
  st.balloons()
  
  
# 바이브를 위한 프롬프트
# 파이썬 스트림릿 대시보드를 만들어주세요.
# 아래의 구조를 실행가능한 파이썬 코드로 완성하세요
# 기본구성
# 페이지 제목 표시, Formula1 이미지 1장 넣기
# 사이드바는 컨트롤 센터로 지정
# 사이드바에 메뉴이동 라디오버튼(메인페이지) 팀마다 분석보고서 라디오버튼으로 만들어주기
# 메인페이지
# 2개의 컬럼으로 kpi 대시보드 구성 
# 방문자수, 활성 사용자수를 메트릭 카드로 구성 
# 분석페이지
# 팀으로 구성(차트/데이터/설정)
# 차트에는 간단한 사용자 방문현황 그래프
# 데이터탭에는 데이터 테이블 출력
# 설정 탭에는 연결시 옵션 체크박스
# 추가요구사항
# streamlit 함수: 기발하고 예쁜 것 위주로 적용
# 코드 전체를 한번에 출력
# 꼭 실행가능한 코드여야 함

# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import date, timedelta

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="F1 Weekly Insights Dashboard",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# Minimal base style
# ----------------------------
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.3rem; }
      [data-testid="stMetricValue"] { font-size: 2rem; }
      [data-testid="stMetricDelta"] { font-size: 0.95rem; }
      div[data-testid="stSidebar"] { border-right: 1px solid rgba(49,51,63,0.12); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Teams + Theme Colors
# ----------------------------
TEAMS = ["Red Bull", "Ferrari", "Mercedes", "McLaren", "Aston Martin"]

TEAM_COLOR = {
    "Red Bull": "#1E41FF",
    "Ferrari": "#DC0000",
    "Mercedes": "#00D2BE",
    "McLaren": "#FF8700",
    "Aston Martin": "#006F62",
}

# 대표 F1 이미지(항상 표시)
F1_HERO_IMG = "https://admin.itsnicethat.com/images/KSCWrw-O8wD3zBb5cQZtiW1zOVU=/7230/format-webp%7Cwidth-2880/5a1bec507fa44c0e69000b24.png"

# 팀 로고(되도록 PNG 권장: SVG는 환경에 따라 표시가 불안정할 수 있음)
TEAM_LOGO = {
    "Red Bull": "https://logodownload.org/wp-content/uploads/2014/09/red-bull-logo-1.png",
    "Ferrari": "https://logodownload.org/wp-content/uploads/2014/09/ferrari-logo-0.png",
    "Mercedes": "https://logodownload.org/wp-content/uploads/2014/04/mercedes-benz-logo-1.png",
    "McLaren": "https://logodownload.org/wp-content/uploads/2021/12/mclaren-logo-0.png",
    "Aston Martin": "https://logodownload.org/wp-content/uploads/2021/11/aston-martin-logo-0.png",
}

# ----------------------------
# Data (dummy, reproducible)
# ----------------------------
@st.cache_data
def make_dummy_data(n_weeks: int = 8, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    today = date.today()
    start = today - timedelta(days=7 * (n_weeks - 1))

    weeks = []
    for i in range(n_weeks):
        d = start + timedelta(days=7 * i)
        weeks.append(f"{d.year}-W{d.isocalendar().week:02d}")

    base_by_team = {
        "Red Bull": 5200,
        "Ferrari": 4800,
        "Mercedes": 4500,
        "McLaren": 4300,
        "Aston Martin": 3900,
    }

    rows = []
    for team in TEAMS:
        base = base_by_team[team]
        trend = np.linspace(0, rng.integers(-250, 450), n_weeks)
        noise = rng.normal(0, 250, n_weeks)

        visitors = np.maximum(0, (base + trend + noise).round().astype(int))
        active_users = np.maximum(0, (visitors * rng.uniform(0.22, 0.42)).round().astype(int))

        for w, v, a in zip(weeks, visitors, active_users):
            rows.append({"week": w, "team": team, "visitors": int(v), "active_users": int(a)})

    return pd.DataFrame(rows)

df = make_dummy_data()

# ----------------------------
# Sidebar: Control Center
# ----------------------------
with st.sidebar:
    st.title("Control Center")
    st.caption("팀/페이지 선택에 따라 테마 컬러가 바뀝니다.")

    team = st.radio("팀 선택", TEAMS, index=0)
    page = st.radio("페이지 이동", ["메인페이지", "분석보고서"], index=0)

    st.divider()
    st.caption("옵션(데모)")
    use_cache = st.checkbox("캐시 사용", value=True)
    auto_refresh = st.checkbox("자동 새로고침", value=False)
    verify_ssl = st.checkbox("SSL 검증", value=True)

# ----------------------------
# Dynamic Theme CSS (팀 선택 직후!)
# ----------------------------
team_color = TEAM_COLOR.get(team, "#E10600")  # 기본값(F1 레드)

st.markdown(
    f"""
    <style>
      /* 전체 배경에 은은한 팀 컬러 */
      .stApp {{
        background: linear-gradient(135deg, {team_color}12, white);
      }}

      /* 헤더/서브헤더 */
      h1, h2, h3 {{
        color: {team_color};
      }}

      /* 메트릭 값 강조 */
      [data-testid="stMetricValue"] {{
        color: {team_color};
      }}

      /* 구분선 */
      hr {{
        border-top: 2px solid {team_color} !important;
      }}

      /* 버튼 */
      .stButton > button {{
        background-color: {team_color};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 0.9rem;
      }}
      .stButton > button:hover {{
        filter: brightness(0.95);
      }}

      /* expander 테두리(약하게) */
      details {{
        border: 1px solid rgba(49,51,63,0.14);
        border-radius: 12px;
        padding: 0.2rem 0.6rem;
        background: rgba(255,255,255,0.65);
        backdrop-filter: blur(8px);
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Header area
# ----------------------------
st.title("F1 Weekly Insights Dashboard")
st.caption("주간(weekly) 방문/활성 사용자 데이터를 팀별로 확인하는 미니 대시보드입니다.")

# 대표 F1 이미지(항상)
st.image(F1_HERO_IMG, caption="Formula 1 (Hero)", use_container_width=True)

# 팀 로고(팀 선택 시)
st.subheader(f"선택 팀: {team}")
logo_url = TEAM_LOGO.get(team)
if logo_url:
    st.image(logo_url, width=260)

st.divider()

# ----------------------------
# Helper
# ----------------------------
team_df = df[df["team"] == team].sort_values("week").reset_index(drop=True)

latest = team_df.iloc[-1]
prev = team_df.iloc[-2] if len(team_df) >= 2 else None

def make_delta(curr: int, prev_val: int | None):
    if prev_val is None:
        return None
    return curr - prev_val

# ----------------------------
# Pages
# ----------------------------
if page == "메인페이지":
    st.subheader("메인페이지 · KPI")

    with st.container(border=True):
        c1, c2 = st.columns(2, gap="large")

        v_delta = make_delta(int(latest["visitors"]), int(prev["visitors"]) if prev is not None else None)
        a_delta = make_delta(int(latest["active_users"]), int(prev["active_users"]) if prev is not None else None)

        with c1:
            st.metric(
                label="방문자수 (최신 주차)",
                value=f"{int(latest['visitors']):,}",
                delta=(f"{v_delta:+,}" if v_delta is not None else None),
            )
            st.caption(f"주차: {latest['week']}")

        with c2:
            st.metric(
                label="활성 사용자수 (최신 주차)",
                value=f"{int(latest['active_users']):,}",
                delta=(f"{a_delta:+,}" if a_delta is not None else None),
            )
            st.caption(f"주차: {latest['week']}")

    with st.expander("해석 가이드", expanded=False):
        st.write(
            "delta는 **직전 주 대비 변화량**입니다. "
            "주간 데이터는 변동성이 있으므로 추세(차트)와 함께 보는 것이 안전합니다."
        )

    st.subheader("주간 추이 미리보기")

    long_df = team_df.melt(
        id_vars=["week", "team"],
        value_vars=["visitors", "active_users"],
        var_name="metric",
        value_name="value",
    )

    chart = (
        alt.Chart(long_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("week:N", title="Week", sort=list(team_df["week"])),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color("metric:N", title="Metric"),
            tooltip=["team:N", "week:N", "metric:N", alt.Tooltip("value:Q", format=",.0f")],
        )
        .properties(height=340)
    )
    st.altair_chart(chart, use_container_width=True)

    if auto_refresh:
        st.toast("자동 새로고침 옵션이 켜져 있습니다(데모).", icon="⏱️")

else:
    st.subheader("분석보고서")
    st.caption("차트/데이터/설정 탭으로 구성됩니다.")

    tab_chart, tab_data, tab_settings = st.tabs(["차트", "데이터", "설정"])

    with tab_chart:
        st.write("선택한 팀의 주간 방문자수/활성 사용자수 추이입니다.")

        long_df = team_df.melt(
            id_vars=["week", "team"],
            value_vars=["visitors", "active_users"],
            var_name="metric",
            value_name="value",
        )

        chart = (
            alt.Chart(long_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("week:N", title="Week", sort=list(team_df["week"])),
                y=alt.Y("value:Q", title="Value"),
                color=alt.Color("metric:N", title="Metric"),
                tooltip=["week:N", "metric:N", alt.Tooltip("value:Q", format=",.0f")],
            )
            .properties(height=420)
        )
        st.altair_chart(chart, use_container_width=True)

        st.info("팁: 4~8주 단위로 추세를 보는 방식이 일반적입니다.", icon="ℹ️")

    with tab_data:
        st.write("선택한 팀 데이터 테이블과 요약 통계입니다.")
        st.dataframe(team_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("요약 통계")
        st.dataframe(team_df[["visitors", "active_users"]].describe().round(2), use_container_width=True)

        avg_ratio = (team_df["active_users"] / team_df["visitors"]).replace([np.inf, -np.inf], np.nan).mean()
        st.caption(f"평균 활성/방문 비율: {avg_ratio:.2%}")

    with tab_settings:
        st.write("연결/운영 옵션(데모)입니다.")
        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.checkbox("캐시 사용", value=use_cache, disabled=True)
            st.checkbox("자동 새로고침", value=auto_refresh, disabled=True)
            st.checkbox("SSL 검증", value=verify_ssl, disabled=True)

        with col2:
            st.markdown("**현재 설정 요약**")
            st.code(
                f"""team = {team}
page = {page}
use_cache = {use_cache}
auto_refresh = {auto_refresh}
verify_ssl = {verify_ssl}
""",
                language="text",
            )

        with st.status("설정 적용 상태", expanded=True) as status:
            st.write("현재 설정은 데모 상태이며, 실제 환경에서는 API/DB 연결 옵션으로 확장합니다.")
            status.update(state="complete")

st.divider()
st.caption("© Demo dashboard for learning Streamlit UI + weekly KPI patterns.")
