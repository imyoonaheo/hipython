# ================================================================
# pages/tab4_dr_sim.py
# 역할 : DR 시뮬레이션 (Tab4) — tab3_dr_sim.py render 호출
# ================================================================
import streamlit as st
import sys
import os

def render():
    # pages 폴더 경로를 sys.path에 추가
    pages_dir = os.path.dirname(os.path.abspath(__file__))
    if pages_dir not in sys.path:
        sys.path.insert(0, pages_dir)

    try:
        from tab3_dr_sim import render as _render
        _render()
    except Exception as e:
        st.error(f"DR 시뮬레이션 로드 오류: {e}")
        import traceback
        st.code(traceback.format_exc())
