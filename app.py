import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import timedelta, timezone
import plotly.express as px
import numpy as np
import calendar

# [1] 기본 설정
calendar.setfirstweekday(calendar.SUNDAY)
KST = timezone(timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
today = datetime.date(2026, now_kst.month, now_kst.day)

st.set_page_config(page_title="AION2 Raid Master", layout="wide")

# [2] 모바일 7열 고정 및 레이아웃 최적화 CSS
st.markdown("""
    <style>
    /* 배경 및 기본 폰트 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 모바일에서 7열 강제 유지 핵심 로직 */
    [data-testid="column"] {
        width: 13% !important;
        flex: 1 1 13% !important;
        min-width: 13% !important;
        padding: 2px !important; /* 모바일은 여백을 줄여야 칸이 안 밀림 */
    }

    /* 달력 카드 스타일 */
    .calendar-card {
        background-color: #1A1D24; border: 1px solid #36393E;
        border-radius: 8px; padding: 10px; margin-bottom: 15px;
    }

    /* 버튼 크기 및 텍스트 최적화 (모바일 배려) */
    .stButton > button {
        width: 100% !important; 
        height: 60px !important; /* 높이를 조금 줄임 */
        background: #161920 !important; border: 1px solid #262730 !important;
        font-size: 0.75rem !important; /* 텍스트 크기 축소 */
        padding: 0px !important;
        line-height: 1.2 !important;
    }

    /* 8명 매칭 시 황금 효과 */
    div.match-gold button {
        background: linear-gradient(135deg, #443714 0%, #1A1D24 100%) !important;
        border: 1px solid #FFD700 !important; color: #FFD700 !important;
    }

    /* 헤더 요일 텍스트 크기 */
    .calendar-table th { font-size: 0.65rem; color: #888; text-align: center; }
    .sun-text { color: #FF4B4B !important; }
    
    /* 타임라인 차트 높이 조절 */
    .js-plotly-plot { height: 250px !important; }
    </style>
    """, unsafe_allow_html=True)

# [3] 데이터 연동 (동일)
def get_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client = gspread.authorize(creds)
        doc = client.open("AION2_Raid_Data")
        return doc.get_worksheet(0), doc.get_worksheet(1)
    except: return None, None

@st.cache_data(ttl=5)
def load_raid_data():
    s1, _ = get_sheets()
    if s1:
        data = pd.DataFrame(s1.get_all_records())
        if not data.empty: data['날짜'] = pd.to_datetime(data['날짜']).dt.date
        return data
    return pd.DataFrame()

@st.cache_data(ttl=10)
def load_member_list():
    _, s2 = get_sheets()
    if s2:
        members = s2.col_values(1)[1:]
        return members if members else ["공대장"]
    return ["공대장"]

df = load_raid_data()
MEMBER_LIST = load_member_list()

if 'view_date' not in st.session_state:
    st.session_state.view_date = today

# [4] 사이드바 (기존 관리자 모드 포함)
with st.sidebar:
    st.markdown("<h3 style='color:#FF4B4B;'>🛡️ AION2 본부</h3>", unsafe_allow_html=True)
    with st.expander("🔐 관리자 설정"):
        pw = st.text_input("PW", type="password")
        if pw == "1234":
            new_name = st.text_input("대원 추가")
            if st.button("➕"):
                _, s2 = get_sheets(); s2.append_row([new_name])
                st.cache_data.clear(); st.rerun()
            target_del = st.selectbox("대원 삭제", MEMBER_LIST)
            if st.button("❌"):
                _, s2 = get_sheets(); cell = s2.find(target_del)
                s2.delete_rows(cell.row); st.cache_data.clear(); st.rerun()

    reg_date = st.date_input("📅 날짜", st.session_state.view_date)
    name = st.selectbox("👤 이름", MEMBER_LIST)
    c1, c2 = st.columns(2)
    with c1: s_time = st.number_input("시작", 0, 23, 22)
    with c2: e_time = st.number_input("종료", 0, 23, 2)
    
    if st.button("🚀 일정 확정"):
        s1, _ = get_sheets()
        if s1:
            all_data = s1.get_all_values()
            rows = [all_data[0]]
            found = False
            for r in all_data[1:]:
                if r[0] == str(reg_date) and r[1] == name:
                    rows.append([str(reg_date), name, s_time, e_time]); found = True
                else: rows.append(r)
            if not found: rows.append([str(reg_date), name, s_time, e_time])
            s1.update('A1', rows)
            st.cache_data.clear(); st.rerun()

# [5] 달력 함수 (모바일용 가독성 개선)
def check_8man_match(day_df):
    if len(day_df) < 8: return False
    timeline = np.zeros(48)
    for _, row in day_df.iterrows():
        s, e = int(row['시작']), int(row['종료'])
        if e <= s: e += 24
        timeline[s:e] += 1
    return np.any(timeline >= 8)

def draw_calendar(year, month, data_df):
    st.markdown(f'<div class="calendar-card">', unsafe_allow_html=True)
    st.markdown(f"<h5 style='text-align:center; color:#FFD700; margin-bottom:10px;'>{year}년 {month}월</h5>", unsafe_allow_html=True)
    
    # 요일 헤더
    header_cols = st.columns(7)
    days_ko = ["일", "월", "화", "수", "목", "금", "토"]
    for i, d in enumerate(days_ko):
        color = "#FF4B4B" if i == 0 else "#888"
        header_cols[i].markdown(f"<p style='text-align:center; font-size:0.7rem; color:{color}; font-weight:bold;'>{d}</p>", unsafe_allow_html=True)
    
    cal = calendar.monthcalendar(year, month)
    summary = {}
    if not data_df.empty:
        m_data = data_df[(data_df['날짜'].apply(lambda x: x.year == year and x.month == month))]
        for d in m_data['날짜'].unique():
            day_data = m_data[m_data['날짜'] == d]
            summary[d.day] = {'count': day_data['이름'].nunique(), 'is_match': check_8man_match(day_data)}

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day != 0:
                    info = summary.get(day, {'count': 0, 'is_match': False})
                    c_class = "match-gold" if info['is_match'] else ""
                    # 모바일 가독성을 위해 텍스트 간소화
                    label = f"{day}\n" + (f"👥{info['count']}" if info['count']>0 else "") + ("🏆" if info['is_match'] else "")
                    st.markdown(f'<div class="{c_class}">', unsafe_allow_html=True)
                    if st.button(label, key=f"btn_{year}_{month}_{day}"):
                        st.session_state.view_date = datetime.date(year, month, day)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else: st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

# 메인 실행
t_month = today.replace(day=1)
n_month = (t_month + timedelta(days=32)).replace(day=1)

# 모바일에서는 두 달을 세로로 배치하는 것이 보기에 좋으므로 컬럼 없이 순차적 호출
draw_calendar(t_month.year, t_month.month, df)
draw_calendar(n_month.year, n_month.month, df)

# 타임라인
sel = st.session_state.view_date
day_df = df[df['날짜'] == sel].copy() if not df.empty else pd.DataFrame()
if not day_df.empty:
    st.markdown(f"<h6>📊 {sel}</h6>", unsafe_allow_html=True)
    base = datetime.datetime.combine(sel, datetime.time.min)
    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=int(x)))
    day_df['end_dt'] = day_df.apply(lambda r: base + datetime.timedelta(days=(1 if int(r['종료']) <= int(r['시작']) else 0), hours=int(r['종료'])), axis=1)
    fig = px.timeline(day_df, x_start="start_dt", x_end="end_dt", y="이름", color="이름", template="plotly_dark")
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)
