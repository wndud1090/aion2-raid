import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import timedelta, timezone
import plotly.express as px
import numpy as np
import calendar

# 1. 일요일 시작으로 달력 설정 고정
calendar.setfirstweekday(calendar.SUNDAY)

# [공대장 전용] 대원 명단
MEMBER_LIST = ["공대장", "대원1", "대원2", "대원3", "대원4", "대원5", "대원6", "대원7"]

# 서울 표준시(KST) 및 2026년 날짜 설정
KST = timezone(timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
today = datetime.date(2026, now_kst.month, now_kst.day)

st.set_page_config(page_title="AION2 Raid Master", layout="wide")

# CSS 스타일 (생략 - 기존과 동일하게 유지하시되, 달력 레이아웃 위주로 적용)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .calendar-card { background-color: #1A1D24; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #36393E; }
    .calendar-table { width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 5px; }
    .calendar-table th { height: 35px; color: #888; border-bottom: 1px solid #36393E; text-align: center; font-size: 0.8rem; }
    .sun-text { color: #FF4B4B !important; }
    .stButton > button { width: 100% !important; height: 80px !important; background: #161920 !important; border: 1px solid #262730 !important; color: #E0E0E0 !important; }
    .has-members button { color: #32CD32 !important; font-weight: bold; }
    .match-gold > div > div > button { background: linear-gradient(135deg, #443714 0%, #1A1D24 100%) !important; border: 1px solid #FFD700 !important; color: #FFD700 !important; }
    [data-testid="column"] { padding: 0 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로직 (생략 - 기존 get_worksheet, load_data, check_8man_match 사용)
# ... (기존 코드의 데이터 관련 함수들 위치)

# --- 달력 그리기 함수 (핵심 교정 부분) ---
def draw_calendar(year, month, data_df):
    st.markdown(f'<div class="calendar-card">', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; color:#FFD700;'>{year}년 {month}월</h3>", unsafe_allow_html=True)
    
    # 요일 헤더 (일요일부터 시작)
    st.markdown('<table class="calendar-table"><thead><tr><th class="sun-text">SUN</th><th>MON</th><th>TUE</th><th>WED</th><th>THU</th><th>FRI</th><th>SAT</th></tr></thead></table>', unsafe_allow_html=True)
    
    # calendar.monthcalendar는 setfirstweekday 설정을 따름
    cal = calendar.monthcalendar(year, month)
    
    summary = {}
    if not data_df.empty:
        month_data = data_df[(data_df['날짜'].apply(lambda x: x.year == year and x.month == month))]
        for d in month_data['날짜'].unique():
            day_data = month_data[month_data['날짜'] == d]
            summary[d.day] = {'count': day_data['이름'].nunique(), 'is_match': check_8man_match(day_data)}

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day != 0:
                    info = summary.get(day, {'count': 0, 'is_match': False})
                    c_class = "match-gold" if info['is_match'] else ("has-members" if info['count'] > 0 else "")
                    
                    # 아이콘 및 매칭 표시 로직
                    icon = "👥" if info['count'] > 0 else ""
                    cnt_str = str(info['count']) if info['count'] > 0 else ""
                    match_icon = "🏆" if info['is_match'] else ""
                    
                    label = f"{day}\n\n{icon}{cnt_str}{match_icon}"
                    
                    st.markdown(f'<div class="{c_class}">', unsafe_allow_html=True)
                    if st.button(label, key=f"btn_{year}_{month}_{day}"):
                        st.session_state.view_date = datetime.date(year, month, day)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # 빈 칸 처리 (아무것도 표시 안 함)
                    st.write("")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 메인 실행부 ---
# (기존의 load_data, 사이드바, 컬럼 배치 로직 그대로 사용)
# col_left, col_right = st.columns(2) 로 draw_calendar 호출
