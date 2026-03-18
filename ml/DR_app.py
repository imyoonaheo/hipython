import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="DR 시뮬레이션",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }

    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252840);
        border-radius: 12px;
        padding: 18px 20px;
        border: 1px solid #2e3250;
        text-align: center;
        height: 100%;
    }
    .metric-label {
        font-size: 0.82rem;
        color: #8b8fa8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #6b7280;
        margin-top: 4px;
    }
    .metric-green  { color: #4ade80; }
    .metric-blue   { color: #60a5fa; }
    .metric-yellow { color: #fbbf24; }
    .metric-red    { color: #f87171; }

    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #c5c8e0;
        padding-bottom: 8px;
        border-bottom: 1px solid #2e3250;
        margin-bottom: 16px;
    }

    .result-box {
        background: linear-gradient(135deg, #1a2540, #1e2d4d);
        border: 1px solid #3b5bdb;
        border-radius: 12px;
        padding: 20px;
    }
    .result-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #2a3050;
        font-size: 0.9rem;
        color: #c5c8e0;
    }
    .result-row:last-child { border-bottom: none; }
    .result-val { font-weight: 600; color: #60a5fa; }
    .result-total {
        text-align: center;
        padding-top: 16px;
        font-size: 1.3rem;
        font-weight: 700;
        color: #4ade80;
    }

    .info-tag {
        display: inline-block;
        background: #1e3a5f;
        color: #93c5fd;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.75rem;
        margin-top: 4px;
        margin-right: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv('data/okm_augumented_2021.csv', encoding='utf-8-sig')

    # 시간 이상값 제거 (0~23 범위만 유효)
    df = df[df['시간'].between(0, 23)].copy()

    df['datetime'] = pd.to_datetime(
        df['날짜'].astype(str) + df['시간'].astype(str).str.zfill(2),
        format='%Y%m%d%H'
    )
    df['월'] = df['datetime'].dt.month
    df['요일'] = df['datetime'].dt.dayofweek
    df['평일여부'] = (df['요일'] < 5).astype(int)
    df['분기내_최대'] = df[['15분', '30분', '45분', '60분']].max(axis=1)

    def get_season(m):
        if m in [6, 7, 8]:        return '여름'
        elif m in [11, 12, 1, 2]: return '겨울'
        elif m in [3,4,5]:       return '봄'
        else:                     return '가을'
    df['계절'] = df['월'].apply(get_season)

    def get_load_period(h):
        if h in list(range(0, 8)) + [22, 23]: return '경부하'
        elif h in [11] + list(range(13, 18)):  return '최대부하'
        else:                                   return '중간부하'
    df['시간대'] = df['시간'].apply(get_load_period)

    df['탄소배출_kg'] = df['평균'] * 0.4781
    return df


# 한전 요금 단가
RATE_TABLE = {
    '여름':   {'경부하': 95.7,  '중간부하': 121.5, '최대부하': 155.0},
    '봄가을': {'경부하': 95.7,  '중간부하': 100.5, '최대부하': 119.7},
    '겨울':   {'경부하': 103.1, '중간부하': 120.0, '최대부하': 149.4},
}
EMISSION_FACTOR = 0.4781
CARBON_PRICE    = 10_000


# ─────────────────────────────────────────
# CBL 계산 함수
# ─────────────────────────────────────────
def calc_cbl(df, target_date, target_hours):
    target_dt = pd.to_datetime(str(target_date))
    past_dates = pd.date_range(end=target_dt - timedelta(days=1), periods=30).tolist()
    past_weekdays = [d for d in past_dates if d.weekday() < 5][-10:]

    cbl_vals = []
    for d in past_weekdays:
        day_int = int(d.strftime('%Y%m%d'))
        sub = df[(df['날짜'] == day_int) & (df['시간'].isin(target_hours))]
        if len(sub) > 0:
            cbl_vals.append(sub['평균'].mean())

    if len(cbl_vals) < 2:
        return None

    cbl_vals.sort(reverse=True)
    return round(np.mean(cbl_vals[:4]), 2)


# ─────────────────────────────────────────
# 메인 UI
# ─────────────────────────────────────────
df = load_data()

st.markdown("## ⚡ DR 시뮬레이션 대시보드")
st.markdown(
    "<div style='color:#8b8fa8; margin-bottom:24px;'>"
    "한전 수요반응(DR) 발령 시 예상 감축량 · 정산금 · ESG 탄소 감축 효과를 시뮬레이션합니다."
    "</div>",
    unsafe_allow_html=True
)

# ── 설정 영역 ────────────────────────────
st.markdown('<div class="section-title">⚙️ DR 발령 조건 설정</div>', unsafe_allow_html=True)

available_dates_dt = sorted([
    pd.to_datetime(str(d), format='%Y%m%d').date()
    for d in df['날짜'].unique()
])

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    dr_date = st.date_input(
        "발령일",
        value=available_dates_dt[180],
        min_value=available_dates_dt[14],
        max_value=available_dates_dt[-1]
    )
with c2:
    dr_start = st.selectbox("시작 시간", list(range(9, 20)),
                            index=4, format_func=lambda x: f"{x}:00")
with c3:
    dr_end = st.selectbox("종료 시간", list(range(10, 21)),
                          index=6, format_func=lambda x: f"{x}:00")
with c4:
    dr_unit_price = st.number_input("DR 정산 단가 (원/kWh)", 100, 600, 300, 50)
with c5:
    reduction_pct = st.slider("감축 목표율 (%)", 5, 30, 15, 1)

run = st.button("🚀 시뮬레이션 실행", type="primary")
st.markdown("---")

# ── 결과 ─────────────────────────────────
if run:
    dr_hours    = list(range(dr_start, dr_end + 1))
    dr_date_int = int(dr_date.strftime('%Y%m%d'))
    actual_df   = df[(df['날짜'] == dr_date_int) & (df['시간'].isin(dr_hours))]
    cbl         = calc_cbl(df, dr_date, dr_hours)

    if actual_df.empty:
        st.warning("⚠️ 해당 날짜/시간대 데이터가 없습니다.")
        st.stop()
    if cbl is None:
        st.warning("⚠️ CBL 계산을 위한 직전 평일 데이터가 부족합니다.")
        st.stop()

    actual_avg    = actual_df['평균'].mean()
    simulated_avg = cbl * (1 - reduction_pct / 100)
    reduction_kwh = max(cbl - simulated_avg, 0)
    total_reduc   = reduction_kwh * len(dr_hours)

    month = dr_date.month
    if month in [6,7,8]:        season = '여름'
    elif month in [11,12,1,2]:  season = '겨울'
    else:                        season = '봄가을'

    energy_rate   = RATE_TABLE[season]['최대부하']
    bill_saving   = total_reduc * energy_rate
    dr_reward     = total_reduc * dr_unit_price
    total_benefit = dr_reward + bill_saving
    co2_reduction = total_reduc * EMISSION_FACTOR
    annual_co2    = co2_reduction * 2 * 4   # 월2회 × 피크4개월

    # ── 상단 지표 카드 ───────────────────
    m1, m2, m3, m4 = st.columns(4)
    for col, label, val, unit, cls in [
        (m1, "⚡ 총 감축량",     f"{total_reduc:.1f}",         "kWh",          "metric-blue"),
        (m2, "💵 DR 정산금",     f"{dr_reward/10000:.1f}",     "만원",         "metric-green"),
        (m3, "💰 전기요금 절감", f"{bill_saving/10000:.1f}",   "만원",         "metric-yellow"),
        (m4, "🌿 탄소 감축",     f"{co2_reduction:.2f}",       "kg CO₂",       "metric-green"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {cls}">{val}</div>
            <div class="metric-sub">{unit}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 정산 상세 + CBL 차트 ─────────────
    col_l, col_r = st.columns([1, 1.8])

    with col_l:
        st.markdown('<div class="section-title">📋 DR 정산 상세</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="result-box">
            <div class="result-row"><span>📌 CBL (기준 사용량)</span><span class="result-val">{cbl:.1f} kWh/h</span></div>
            <div class="result-row"><span>📉 감축 목표 사용량</span><span class="result-val">{simulated_avg:.1f} kWh/h</span></div>
            <div class="result-row"><span>⚡ 시간당 감축량</span><span class="result-val">{reduction_kwh:.1f} kWh</span></div>
            <div class="result-row"><span>⏱ 발령 시간 수</span><span class="result-val">{len(dr_hours)} 시간</span></div>
            <div class="result-row"><span>📦 총 감축량</span><span class="result-val">{total_reduc:.1f} kWh</span></div>
            <div class="result-row"><span>💵 DR 정산금</span><span class="result-val">{dr_reward:,.0f} 원</span></div>
            <div class="result-row"><span>💰 전기요금 절감</span><span class="result-val">{bill_saving:,.0f} 원</span></div>
            <div class="result-row"><span>🌿 탄소 감축</span><span class="result-val">{co2_reduction:.2f} kg CO₂</span></div>
            <div class="result-total">💎 총 예상 이익: {total_benefit:,.0f} 원</div>
        </div>
        <div style="margin-top:10px;">
            <span class="info-tag">계절: {season}</span>
            <span class="info-tag">최대부하 단가: {energy_rate}원/kWh</span>
            <span class="info-tag">DR 단가: {dr_unit_price}원/kWh</span>
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-title">📈 CBL vs 실제 vs 감축 목표</div>', unsafe_allow_html=True)

        hours_label = [f"{h}시" for h in dr_hours]
        actual_vals = (
            actual_df.set_index('시간')['평균']
            .reindex(dr_hours)
            .ffill()
            .fillna(actual_avg)
            .tolist()
        )

        fig = go.Figure()
        # 감축 효과 면적
        fig.add_trace(go.Scatter(
            x=hours_label + hours_label[::-1],
            y=[simulated_avg]*len(dr_hours) + [cbl]*len(dr_hours),
            fill='toself', fillcolor='rgba(74,222,128,0.1)',
            line=dict(color='rgba(0,0,0,0)'),
            showlegend=False, hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=hours_label, y=[cbl]*len(dr_hours),
            name='CBL (기준)', line=dict(color='#fbbf24', dash='dash', width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=hours_label, y=actual_vals,
            name='실제 사용량', line=dict(color='#60a5fa', width=2.5),
            fill='tozeroy', fillcolor='rgba(96,165,250,0.08)'
        ))
        fig.add_trace(go.Scatter(
            x=hours_label, y=[simulated_avg]*len(dr_hours),
            name='감축 목표', line=dict(color='#4ade80', dash='dot', width=2.5)
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#c5c8e0'),
            xaxis=dict(gridcolor='#2e3250', title='시간'),
            yaxis=dict(gridcolor='#2e3250', title='전력 (kWh)'),
            legend=dict(bgcolor='rgba(0,0,0,0)', orientation='h',
                        yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=340, margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>")
    st.markdown("---")

    # ── ESG 탄소 감축 ────────────────────
    st.markdown('<div class="section-title">🌿 ESG 탄소 감축 효과</div>', unsafe_allow_html=True)

    e1, e2, e3 = st.columns(3)

    with e1:
        fig_bar = go.Figure(go.Bar(
            x=['DR 전', 'DR 후'],
            y=[actual_avg * len(dr_hours) * EMISSION_FACTOR,
               simulated_avg * len(dr_hours) * EMISSION_FACTOR],
            marker_color=['#ef4444', '#4ade80'],
            text=[f"{actual_avg*len(dr_hours)*EMISSION_FACTOR:.1f}kg",
                  f"{simulated_avg*len(dr_hours)*EMISSION_FACTOR:.1f}kg"],
            textposition='outside', textfont=dict(color='#c5c8e0', size=12)
        ))
        fig_bar.update_layout(
            title='이번 발령 탄소 배출 비교',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#c5c8e0'),
            yaxis=dict(gridcolor='#2e3250', title='kg CO₂'),
            xaxis=dict(gridcolor='#2e3250'),
            height=270, margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with e2:
        months_label = ['3월','4월','5월','6월','7월','8월','9월','10월','11월','12월']
        cumulative   = [co2_reduction * 2 * i for i in range(1, 11)]
        fig_cum = go.Figure(go.Scatter(
            x=months_label, y=cumulative,
            fill='tozeroy', fillcolor='rgba(74,222,128,0.12)',
            line=dict(color='#4ade80', width=2.5),
            mode='lines+markers', marker=dict(color='#4ade80', size=7)
        ))
        fig_cum.update_layout(
            title='연간 탄소 감축 누적 (월 2회 가정)',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#c5c8e0'),
            yaxis=dict(gridcolor='#2e3250', title='누적 kg CO₂'),
            xaxis=dict(gridcolor='#2e3250'),
            height=270, margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_cum, use_container_width=True)

    with e3:
        annual_cost_saving = annual_co2 / 1000 * CARBON_PRICE
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:12px;">
            <div class="metric-label">이번 발령 탄소 감축</div>
            <div class="metric-value metric-green">{co2_reduction:.2f}</div>
            <div class="metric-sub">kg CO₂</div>
        </div>
        <div class="metric-card" style="margin-bottom:12px;">
            <div class="metric-label">연간 환산 탄소 감축</div>
            <div class="metric-value metric-green">{annual_co2/1000:.3f}</div>
            <div class="metric-sub">톤 CO₂ (월 2회 × 피크 4개월)</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">탄소 비용 절감 (연간)</div>
            <div class="metric-value metric-blue">{annual_cost_saving:,.0f}</div>
            <div class="metric-sub">원 (ETS 10,000원/톤 기준)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        "<br><div style='color:#6b7280; font-size:0.78rem;'>"
        "※ 배출계수 0.4781 kgCO₂/kWh (환경부 고시 2022) | "
        "탄소가격 10,000원/톤 (한국 ETS) | "
        "CBL: 직전 10 평일 중 상위 4일 동시간대 평균 (한전 표준)"
        "</div>",
        unsafe_allow_html=True
    )

else:
    st.markdown("""
    <div style="text-align:center; padding:100px 0; color:#8b8fa8;">
        <div style="font-size:4rem;">⚡</div>
        <div style="font-size:1.2rem; margin-top:16px; color:#c5c8e0;">
            DR 발령 조건을 설정하고 시뮬레이션을 실행하세요
        </div>
        <div style="margin-top:12px; font-size:0.9rem;">
            발령일 · 시간 · 정산 단가 · 감축 목표율 입력 후
            <b style="color:#60a5fa;">🚀 시뮬레이션 실행</b> 클릭
        </div>
    </div>
    """, unsafe_allow_html=True)
