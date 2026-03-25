import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import timedelta, timezone
import plotly.express as px
import numpy as np
import calendar

# ==========================================
# [공대장 전용] 대원 명단 설정
# ==========================================
MEMBER_LIST = ["공대장", "대원1", "대원2", "대원3", "대원4", "대원5", "대원6", "대원7"]
# ==========================================

# --- 1. 서울 기준 시간 설정 (KST) ---
# 서버 시간과 상관없이 한국 시간으로 고정
KST = timezone(timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
# 2026년으로 연도 고정 (월, 일은 한국 실시간 반영)
today = datetime.date(2026, now_kst.month, now_kst.day)

# --- 2. 페이지 설정 및 UI ---
st.set_page_config(page_title="AION2 Raid Master (KST)", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .calendar-card {
        background-color: #1A1D24; border: 1px solid #36393E;
        border-radius: 12px; padding: 20px; margin-bottom: 20px;
    }
    .calendar-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .calendar-table th { height: 35px; color: #888; border-bottom: 1px solid #36393E; font-size: 0.8rem; text-align: center; }
    .stButton > button {
        width: 100% !important; height: 75px !important;
        background: #161920 !important; border: 1px solid #262730 !important;
        color: #E0E0E0 !important; margin-top: 4px;
    }
    .has-members button { color: #32CD32 !important; font-weight: bold; }
    .match-gold > div > div > button {
        background: linear-gradient(135deg, #443714 0%, #1A1D24 100%) !important;
        border: 1px solid #FFD700 !important; color: #FFD700 !important;
    }
    .sun-text { color: #FF4B4B !important; }
    [data-testid="column"] { padding: 0 25px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 데이터 로직 ---
def get_worksheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client = gspread.authorize(creds)
        return client.open("AION2_Raid_Data").sheet1
    except: return None

@st.cache_data(ttl=5)
def load_data():
    ws = get_worksheet()
    if ws:
        data = pd.DataFrame(ws.get_all_records())
        if not data.empty: data['날짜'] = pd.to_datetime(data['날짜']).dt.date
        return data
    return pd.DataFrame()

def check_8man_match(day_df):
    if len(day_df) < 8: return False
    timeline = np.zeros(48)
    for _, row in day_df.iterrows():
        s, e = int(row['시작']), int(row['종료'])
        if e <= s: e += 24
        timeline[s:e] += 1
    return np.any(timeline >= 8)

df = load_data()

if 'view_date' not in st.session_state:
    st.session_state.view_date = today

# --- 4. 사이드바 (KST 기준 날짜 입력) ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B;'>🛡️ AION2 본부</h1>")
    st.info(f"📍 서울 기준: {today}")
    reg_date = st.date_input("📅 날짜 선택", st.session_state.view_date)
    name = st.selectbox("👤 대원 선택", MEMBER_LIST)
    col1, col2 = st.columns(2)
    with col1: s_time = st.number_input("시작", 0, 23, 22)
    with col2: e_time = st.number_input("종료", 0, 23, 2)
    
    if st.button("🚀 일정 확정"):
        ws = get_worksheet()
        if ws:
            all_data = ws.get_all_values()
            updated_rows = [all_data[0]]
            found = False
            for r in all_data[1:]:
                if r[0] == str(reg_date) and r[1] == name:
                    updated_rows.append([str(reg_date), name, s_time, e_time]); found = True
                else: updated_rows.append(r)
            if not found: updated_rows.append([str(reg_date), name, s_time, e_time])
            ws.update('A1', updated_rows)
            st.cache_data.clear()
            st.rerun()

# --- 5. 메인: 2026년 서울 기준 2개월 달력 ---
def draw_calendar(year, month, data_df):
    st.markdown(f'<div class="calendar-card">', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; color:#FFD700;'>{year}년 {month}월</h3>", unsafe_allow_html=True)
    st.markdown('<table class="calendar-table"><thead><tr><th class="sun-text">SUN</th><th>MON</th><th>TUE</th><th>WED</th><th>THU</th><th>FRI</th><th>SAT</th></tr></thead></table>', unsafe_allow_html=True)
    
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
                    label = f"{day}\n\n{'👥' if info['count']>0 else ''}{info['count'] if info['count']>0 else ''}{'🏆' if info['is_match'] else ''}"
                    st.markdown(f'<div class="{c_class}">', unsafe_allow_html=True)
                    if st.button(label, key=f"btn_{year}_{month}_{day}"):
                        st.session_state.view_date = datetime.date(year, month, day)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else: st.write("")
    st.markdown('</div>', unsafe_allow_html=True)

# 이번 달 및 다음 달 계산 (KST 기준)
this_month_first = today.replace(day=1)
next_month_first = (this_month_first + timedelta(days=32)).replace(day=1)

col_left, col_right = st.columns(2)
with col_left: draw_calendar(this_month_first.year, this_month_first.month, df)
with col_right: draw_calendar(next_month_first.year, next_month_first.month, df)

# --- 6. 하단 타임라인 ---
st.write("---")
sel = st.session_state.view_date
day_df = df[df['날짜'] == sel].copy() if not df.empty else pd.DataFrame()

if not day_df.empty:
    st.markdown(f"### 📊 {sel} 타임라인 " + ("<span style='color:#FFD700;'>[MATCH]</span>" if check_8man_match(day_df) else ""), unsafe_allow_html=True)
    base = datetime.datetime.combine(sel, datetime.time.min)
    def get_end_time(row):
        s, e = int(row['시작']), int(row['종료'])
        return base + datetime.timedelta(days=(1 if e <= s else 0), hours=e)
    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=int(x)))
    day_df['end_dt'] = day_df.apply(get_end_time, axis=1)
    fig = px.timeline(day_df, x_start="start_dt", x_end="end_dt", y="이름", color="이름", template="plotly_dark")
    fig.update_layout(xaxis=dict(title="", tickformat="%H시"), yaxis=dict(title="", autorange="reversed"), showlegend=False, height=300)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(f"{sel}에 등록된 인원이 없습니다.")
