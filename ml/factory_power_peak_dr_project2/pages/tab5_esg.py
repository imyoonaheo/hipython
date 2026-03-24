# ================================================================
# pages/tab5_esg.py
# 역할 : ESG 리포트 (Tab5) — GRI 302 에너지 집계 + 자동 리포트
# 의존 : data/okm_enriched_final.csv
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# ── 상수 ──────────────────────────────────────────────────────
EMISSION_FACTOR = 0.4781      # 탄소 배출계수 kgCO2/kWh (환경부 고시 2022)
BASIC_RATE      = 8320
MAX_PEAK_2021   = 211.2
CARBON_PRICE    = 10_000
MONTH_LABELS    = {i: f"{i}월" for i in range(1, 13)}

@st.cache_data
def load_esg_data():
    for path in ['data/okm_enriched_final.csv',
                 '../data/okm_enriched_final.csv',
                 './okm_enriched_final.csv']:
        if os.path.exists(path):
            df = pd.read_csv(path, encoding='utf-8-sig')
            df['날짜'] = pd.to_datetime(
                df['날짜'].astype(str), format='%Y%m%d', errors='coerce')
            df['month'] = df['날짜'].dt.month
            return df, path
    return None, None

def calc_gri302(df):
    total_kwh  = df['추정사용전력량'].sum()
    total_gj   = round(total_kwh * 0.0036, 1)
    scope2     = round(total_kwh / 1000 * EMISSION_FACTOR, 2)
    total_prod = df['생산량'].sum()
    intensity  = round(total_kwh / total_prod, 4) if total_prod > 0 else 0
    max_peak   = df['15분'].max() if '15분' in df.columns else MAX_PEAK_2021
    save_10    = round((max_peak * 0.10) * BASIC_RATE * 12)
    save_20    = round((max_peak * 0.20) * BASIC_RATE * 12)
    co2_cost   = round(scope2 * CARBON_PRICE)

    agg = {'kWh합계': ('추정사용전력량', 'sum'),
           '생산량합계': ('생산량', 'sum')}
    if '15분' in df.columns:
        agg['최대피크'] = ('15분', 'max')
    monthly = df.groupby('month').agg(**agg).reset_index()
    monthly['GJ']      = (monthly['kWh합계'] * 0.0036).round(1)
    monthly['tCO2eq']  = (monthly['kWh합계'] / 1000 * EMISSION_FACTOR).round(3)
    monthly['월']      = monthly['month'].map(MONTH_LABELS)
    return dict(total_kwh=total_kwh, total_gj=total_gj, scope2=scope2,
                intensity=intensity, max_peak=max_peak,
                save_10=save_10, save_20=save_20,
                co2_cost=co2_cost, monthly=monthly)

# ══════════════════════════════════════════════════════════════
def render():
# ══════════════════════════════════════════════════════════════

    with st.sidebar:
        st.markdown(
            "<div style='background:#1E293B;color:#fff;border-radius:8px;"
            "padding:10px 14px;margin-bottom:14px;font-size:13px;"
            "font-weight:700;'>🌿 ESG 리포트 — 설정</div>",
            unsafe_allow_html=True)
        st.markdown("**📅 보고 연도**")
        report_year = st.selectbox("연도 선택", [2021], index=0, key="esg_year")
        st.divider()
        st.markdown("**🎯 절감 목표 설정**")
        target_cut = st.slider("피크 절감 목표 (%)", 5, 30, 10, 5, key="esg_cut")
        st.divider()
        gen_btn = st.button("📄 GRI 302 리포트 생성",
                            type="primary", use_container_width=True, key="esg_gen")

    st.markdown("""
    <div style='background:#1E293B;color:#fff;border-radius:10px;
    padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;'>
        <span style='font-size:20px;'>🌿</span>
        <span style='font-size:16px;font-weight:500;'>ESG 리포트 — GRI 302 에너지</span>
        <span style='margin-left:auto;font-size:12px;opacity:.6;'>
        울산 볼트·너트 제조공장 | 2021년
        </span>
    </div>""", unsafe_allow_html=True)

    df, data_path = load_esg_data()
    if df is None:
        st.error("❌ okm_enriched_final.csv 파일을 찾을 수 없습니다.")
        st.info("data/ 폴더에 okm_enriched_final.csv 파일을 넣어주세요.")
        return

    if not gen_btn and "esg_result" not in st.session_state:
        st.info("👈 왼쪽 사이드바에서 **[GRI 302 리포트 생성]** 버튼을 클릭하세요.",
                icon="💡")
        st.caption(f"📂 데이터 경로: {data_path} | {len(df):,}행")
        return

    if gen_btn:
        st.session_state["esg_result"] = calc_gri302(df)

    result  = st.session_state["esg_result"]
    monthly = result['monthly']

    st.success(f"✅ GRI 302 리포트 생성 완료 — {report_year}년 | "
               f"총 {result['total_kwh']:,.0f} kWh", icon="📄")

    # ── KPI 5개 ───────────────────────────────────────────────
    st.markdown("#### 📊 핵심 에너지 지표 (GRI 302-1 / 302-3 / 302-4)")
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.metric("연간 총 전력 소비",  f"{result['total_kwh']:,.0f} kWh")
    with k2: st.metric("GJ 환산",           f"{result['total_gj']:,.1f} GJ")
    with k3: st.metric("Scope 2 탄소 배출", f"{result['scope2']:,.2f} tCO₂eq")
    with k4: st.metric("에너지 집약도",      f"{result['intensity']:.4f} kWh/개")
    with k5: st.metric("탄소 비용 (환산)",   f"₩{result['co2_cost']:,}")

    st.divider()

    # ── 절감 시나리오 + 월별 차트 ────────────────────────────
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown("**🎯 피크 절감 시나리오**")
        rows_sc = []
        for pct in [5, 10, 15, 20]:
            tgt  = round(result['max_peak'] * (1 - pct/100), 1)
            diff = round(result['max_peak'] - tgt, 1)
            bs   = round(diff * BASIC_RATE * 12)
            co2r = round(diff * EMISSION_FACTOR * 8760 * 0.1 / 1000, 2)
            rows_sc.append({'절감률': f"{pct}%", '목표 피크': f"{tgt} kW",
                            '감축량': f"{diff} kW", '기본요금 절감': f"₩{bs:,}",
                            'CO₂ 절감': f"{co2r} t"})
        df_sc = pd.DataFrame(rows_sc)

        def hl(row):
            return (['background-color:#EAF3DE'] * len(row)
                    if row['절감률'] == f"{target_cut}%" else [''] * len(row))
        st.dataframe(df_sc.style.apply(hl, axis=1),
                     hide_index=True, use_container_width=True)
        st.caption(f"📌 연간 최대 피크: {result['max_peak']:.0f} kW | "
                   f"연간 기본요금: ₩{round(result['max_peak']*BASIC_RATE*12):,}")

    with col_r:
        st.markdown("**📈 월별 전력 소비 & 탄소 배출**")
        fig = go.Figure()
        fig.add_bar(x=monthly['월'], y=monthly['kWh합계'],
                    name='전력 소비 (kWh)', marker_color='#2563EB', opacity=0.8)
        fig.add_scatter(x=monthly['월'], y=monthly['tCO2eq'] * 1000,
                        name='탄소 배출 (kg)', mode='lines+markers',
                        line=dict(color='#DC2626', width=2), yaxis='y2')
        fig.update_layout(
            height=260, margin=dict(t=10, b=20, l=10, r=10),
            yaxis=dict(title='전력 소비 (kWh)'),
            yaxis2=dict(title='탄소 배출 (kg)', overlaying='y', side='right'),
            legend=dict(orientation='h', y=-0.3),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── 월별 집계 테이블 ──────────────────────────────────────
    st.markdown("**📋 월별 집계 테이블 (GRI 302-1)**")
    df_show = monthly[['월', 'kWh합계', 'GJ', 'tCO2eq', '생산량합계']].copy()
    df_show.columns = ['월', '전력소비(kWh)', '전력소비(GJ)', '탄소배출(tCO₂eq)', '생산량(개)']
    df_show['전력소비(kWh)']    = df_show['전력소비(kWh)'].apply(lambda x: f"{x:,.0f}")
    df_show['전력소비(GJ)']     = df_show['전력소비(GJ)'].apply(lambda x: f"{x:,.1f}")
    df_show['탄소배출(tCO₂eq)'] = df_show['탄소배출(tCO₂eq)'].apply(lambda x: f"{x:.3f}")
    df_show['생산량(개)']       = df_show['생산량(개)'].apply(lambda x: f"{x:,.0f}")
    st.dataframe(df_show, hide_index=True, use_container_width=True)

    st.divider()

    # ── CSV 다운로드 ──────────────────────────────────────────
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            label="📥 월별 집계 CSV 다운로드",
            data=monthly.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
            file_name=f"GRI302_월별집계_{report_year}.csv",
            mime="text/csv", use_container_width=True)
    with col_d2:
        summary = pd.DataFrame([{
            '보고연도': report_year,
            '총전력소비(kWh)': round(result['total_kwh'], 0),
            '총전력소비(GJ)': result['total_gj'],
            'Scope2(tCO2eq)': result['scope2'],
            '에너지집약도(kWh/개)': result['intensity'],
            '연간최대피크(kW)': result['max_peak'],
            '10%절감기본요금절감(원)': result['save_10'],
            '20%절감기본요금절감(원)': result['save_20'],
        }])
        st.download_button(
            label="📥 GRI 302 요약 CSV 다운로드",
            data=summary.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
            file_name=f"GRI302_요약_{report_year}.csv",
            mime="text/csv", use_container_width=True)
