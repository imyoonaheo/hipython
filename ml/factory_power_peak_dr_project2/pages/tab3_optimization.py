# ================================================================
# pages/tab3_optimization.py
# 역할 : 운영 최적화 (Tab3)
#        Tab1 예측 결과 연동 → 최적 가동 시간대 / 비용 절감 분석
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ── 상수 ──────────────────────────────────────────────────────
BASIC_RATE   = 8320        # 기본요금 원/kW/월
EMISSION     = 0.4781      # 탄소 배출계수 kgCO2/kWh (환경부 고시 2022)
CARBON_PRICE = 10_000      # 탄소 비용 원/tCO2

def get_tou(m, h):
    if m in [6,7,8]:      # 여름
        if 10 <= h <= 17:           return 'max', 155.0
        if h <= 5 or h >= 22:       return 'low',  95.7
        return 'mid', 121.5
    elif m in [11,12,1,2]: # 겨울
        if h in [9,10,17,18,19]:    return 'max', 155.0
        if h <= 5 or h >= 22:       return 'low',  95.7
        return 'mid', 121.5
    else:                  # 봄가을
        if 10 <= h <= 17:           return 'mid', 121.5
        if h <= 5 or h >= 22:       return 'low',  95.7
        return 'mid', 121.5

# ══════════════════════════════════════════════════════════════
def render():
# ══════════════════════════════════════════════════════════════

    # ── 사이드바 ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<div style='background:#1E293B;color:#fff;border-radius:8px;"
            "padding:10px 14px;margin-bottom:14px;font-size:13px;"
            "font-weight:700;'>⚙️ 운영 최적화 — 분석 조건</div>",
            unsafe_allow_html=True)

        st.markdown("**📅 분석 월**")
        opt_month = st.selectbox(
            "월 선택", list(range(1, 13)), index=6,
            format_func=lambda x: f"{x}월", key="opt_month")

        st.divider()
        st.markdown("**💡 절감 시나리오**")
        cut_pct = st.slider(
            "피크 절감 목표 (%)", 5, 30, 10, 5, key="opt_cut",
            help="현재 피크 대비 몇 % 줄일지 설정합니다")

    # ── 헤더 ──────────────────────────────────────────────────
    st.markdown("""
    <div style='background:#1E293B;color:#fff;border-radius:10px;
    padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;'>
        <span style='font-size:20px;'>⚙️</span>
        <span style='font-size:16px;font-weight:500;'>운영 최적화</span>
        <span style='margin-left:auto;font-size:12px;opacity:.6;'>
        Tab1 예측 결과 자동 연동
        </span>
    </div>""", unsafe_allow_html=True)

    # ── Tab1 연동 ─────────────────────────────────────────────
    has_result = "tab1_result" in st.session_state
    if has_result:
        r     = st.session_state["tab1_result"]
        p15   = r["p15"]
        month = r["month"]
        hour  = r["hour"]
        st.success(
            f"✅ Tab1 예측 결과 연동 — "
            f"{month}월 {hour}시 | 예측 피크 **{p15:.1f} kW**",
            icon="🔗")
    else:
        p15   = 112.8
        month = opt_month
        hour  = 10
        st.info(
            "ℹ️ Tab1에서 피크 예측을 먼저 실행하면 결과가 자동으로 연동됩니다. "
            "현재는 기본값(112.8kW)으로 표시합니다.", icon="💡")

    # ── KPI 4개 ───────────────────────────────────────────────
    target_peak  = round(p15 * (1 - cut_pct / 100), 1)
    basic_saving = round((p15 - target_peak) * BASIC_RATE * 12)
    _, tou_price = get_tou(month, hour)
    co2_save     = round((p15 - target_peak) * EMISSION * 8760 * 0.1 / 1000, 2)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("현재 예측 피크", f"{p15:.1f} kW")
    with c2:
        st.metric(f"절감 목표 ({cut_pct}%)", f"{target_peak:.1f} kW",
                  delta=f"-{p15 - target_peak:.1f} kW", delta_color="normal")
    with c3:
        st.metric("연간 기본요금 절감", f"₩{basic_saving:,}")
    with c4:
        st.metric("연간 CO₂ 절감", f"{co2_save:.2f} tCO₂")

    st.divider()

    # ── 24시간 TOU 차트 ───────────────────────────────────────
    col_l, col_r = st.columns([1.8, 1])

    with col_l:
        st.markdown("**📊 24시간 TOU 요금 구간 & 피크 절감 시뮬레이션**")
        hours      = list(range(24))
        tou_data   = [get_tou(month, h) for h in hours]
        tou_prices = [t[1] for t in tou_data]
        tou_labels = [t[0] for t in tou_data]
        colors     = ['#DC2626' if l == 'max' else '#D97706' if l == 'mid'
                      else '#059669' for l in tou_labels]

        fig = go.Figure()
        fig.add_bar(x=hours, y=tou_prices, marker_color=colors,
                    text=[f"{p:.1f}" for p in tou_prices],
                    textposition='outside')
        fig.add_hline(y=p15 * 0.1, line_dash="dash", line_color="#2563EB",
                      annotation_text=f"현재 피크 ({p15:.1f}kW)",
                      annotation_position="top left")
        fig.add_hline(y=target_peak * 0.1, line_dash="dot", line_color="#059669",
                      annotation_text=f"목표 ({target_peak:.1f}kW)",
                      annotation_position="bottom right")
        fig.update_layout(
            height=280, margin=dict(t=20, b=20, l=10, r=10),
            xaxis_title="시간", yaxis_title="TOU 단가 (원/kWh)",
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🔴 최대부하 155.0원 | 🟡 중간부하 121.5원 | 🟢 경부하 95.7원")

    with col_r:
        st.markdown("**💰 절감 시나리오 비교**")
        rows = []
        for pct in [5, 10, 15, 20]:
            tgt  = round(p15 * (1 - pct / 100), 1)
            diff = round(p15 - tgt, 1)
            bs   = round(diff * BASIC_RATE * 12)
            co2  = round(diff * EMISSION * 8760 * 0.1 / 1000, 2)
            rows.append({'절감률': f"{pct}%", '목표피크': f"{tgt} kW",
                         '기본요금절감': f"₩{bs:,}", 'CO₂절감': f"{co2} t"})
        df_sc = pd.DataFrame(rows)

        def hl(row):
            return (['background-color:#EAF3DE'] * len(row)
                    if row['절감률'] == f"{cut_pct}%" else [''] * len(row))
        st.dataframe(df_sc.style.apply(hl, axis=1),
                     hide_index=True, use_container_width=True)

    st.divider()

    # ── 최적 가동 시간대 추천 ─────────────────────────────────
    st.markdown("**⏰ 최적 가동 시간대 추천**")
    cols = st.columns(3)
    bands = [
        ("🟢 경부하 (최적)",
         [h for h in range(24) if get_tou(month, h)[0] == 'low'],
         "#EAF3DE", "#059669", "95.7원/kWh"),
        ("🟡 중간부하 (보통)",
         [h for h in range(24) if get_tou(month, h)[0] == 'mid'],
         "#FAEEDA", "#D97706", "121.5원/kWh"),
        ("🔴 최대부하 (회피)",
         [h for h in range(24) if get_tou(month, h)[0] == 'max'],
         "#FCEBEB", "#DC2626", "155.0원/kWh"),
    ]
    for col, (label, hrs, bg, fc, price) in zip(cols, bands):
        with col:
            h_str = ', '.join([f"{h}시" for h in hrs]) if hrs else "없음"
            st.markdown(f"""
            <div style='background:{bg};border-radius:8px;padding:12px 14px;'>
                <div style='font-size:12px;font-weight:600;color:{fc};
                margin-bottom:6px;'>{label}</div>
                <div style='font-size:11px;color:#475569;line-height:1.7;'>
                    단가: <b>{price}</b><br>시간: {h_str}
                </div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # ── 절감 효과 요약 ────────────────────────────────────────
    st.markdown(f"**📋 절감 효과 요약 ({month}월 기준)**")
    energy_save = round((p15 - target_peak) * tou_price * 8760 * 0.1 / 1000)
    co2_cost    = round(co2_save * CARBON_PRICE)

    s1, s2, s3 = st.columns(3)
    for col, title, val, sub, color in [
        (s1, "연간 기본요금 절감",   f"₩{basic_saving:,}",
         f"피크 {p15-target_peak:.1f}kW × 8,320 × 12개월", "#059669"),
        (s2, "연간 전력량요금 절감", f"₩{energy_save:,}",
         f"TOU {tou_price}원/kWh 기준", "#2563EB"),
        (s3, "탄소 절감 경제적 가치", f"₩{co2_cost:,}",
         f"{co2_save:.2f} tCO₂ × 10,000원", "#D97706"),
    ]:
        with col:
            with st.container(border=True):
                st.markdown(f"""
                <div style='text-align:center;'>
                    <div style='font-size:11px;color:#64748B;'>{title}</div>
                    <div style='font-size:22px;font-weight:700;color:{color};'>
                        {val}</div>
                    <div style='font-size:10px;color:#94A3B8;'>{sub}</div>
                </div>""", unsafe_allow_html=True)
