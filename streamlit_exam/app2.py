import streamlit as st

#layout 요소
st.columns(2)
col1, col2 = st.columns(2)

st.set_page_config(page_title="환경 상태 미니 대시보드", layout="wide")

# =========================
# 예시 데이터 (원하면 API/센서값으로 교체)
# =========================
temp_now = 35
temp_delta = 3          # +면 상승(초록), -면 하락(빨강) 기본 동작

air_label = "좋음"      # 공기질 텍스트 표시
aqi_delta = -30         # 공기질/오염도는 내려가면 '좋아짐'일 수 있음 → inverse로 처리

# =========================
# UI
# =========================
st.write("")  # 상단 여백
col1, col2 = st.columns(2, gap="large")

with col1:
    st.metric(
        label="오늘의 날씨",
        value=f"{temp_now}도",
        delta=f"{temp_delta:+d}"
    )

with col2:
    st.metric(
        label="오늘의 미세먼지",
        value=air_label,
        delta=f"{aqi_delta:+d}",
        delta_color="inverse"  # delta가 음수면 초록(개선), 양수면 빨강(악화)
    )
