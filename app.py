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

# [2] CSS (비밀번호 입력창 및 관리자 UI 스타일 추가)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .calendar-card { background-color: #1A1D24; border: 1px solid #36393E; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    .admin-box { background-color: #262730; border: 1px dashed #FF4B4B; padding: 15px; border-radius: 10px; margin-top: 20px; }
    div.match-gold button {
        background: linear-gradient(135deg, #443714 0%, #1A1D24 100%) !important;
        border: 2px solid #FFD700 !important; color: #FFD700 !important; font-weight: 900 !important;
    }
    .stButton > button { width: 100% !important; height: 85px !important; background: #161920 !important; border: 1px solid #262730 !important; }
    </style>
    """, unsafe_allow_html=True)

# [3] 데이터 연동 함수 (명단 전용 Sheet2 추가)
def get_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client = gspread.authorize(creds)
        doc = client.open("AION2_Raid_Data")
        return doc.get_worksheet(0), doc.get_worksheet(1) # Sheet1: 일정, Sheet2: 명단
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
        members = s2.col_values(1)[1:] # 첫 줄(헤더) 제외
        return members if members else ["공대장"]
    return ["공대장"]

df = load_raid_data()
MEMBER_LIST = load_member_list()

if 'view_date' not in st.session_state:
    st.session_state.view_date = today

# [4] 사이드바: 관리자 모드 및 일정 등록
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B;'>🛡️ AION2 본부</h1>", unsafe_allow_html=True)
    
    # --- 관리자 로그인 섹션 ---
    with st.expander("🔐 관리자 설정"):
        pw = st.text_input("비밀번호 입력", type="password")
        if pw == "1234": # 공대장님만의 비밀번호로 수정하세요
            st.success("인증 성공: 명단 수정 가능")
            new_name = st.text_input("새 대원 이름")
            if st.button("➕ 대원 추가"):
                _, s2 = get_sheets()
                s2.append_row([new_name])
                st.cache_data.clear()
                st.rerun()
            
            target_del = st.selectbox("삭제할 대원", MEMBER_LIST)
            if st.button("❌ 선택 삭제"):
                _, s2 = get_sheets()
                cell = s2.find(target_del)
                s2.delete_rows(cell.row)
                st.cache_data.clear()
                st.rerun()
        elif pw != "":
            st.error("비밀번호가 틀렸습니다.")

    st.divider()
    
    # --- 일반 일정 등록 섹션 ---
    reg_date = st.date_input("📅 날짜 선택", st.session_state.view_date)
    name = st.selectbox("👤 본인 이름 선택", MEMBER_LIST)
    c1, c2 = st.columns(2)
    with c1: s_time = st.number_input("시작(시)", 0, 23, 22)
    with c2: e_time = st.number_input("종료(시)", 0, 23, 2)
    
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
            st.cache_data.clear()
            st.rerun()

# [5] 메인 화면 (달력 그리기 로직 - 기존과 동일)
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
    st.markdown(f"<h3 style='text-align:center; color:#FFD700;'>{year}년 {month}월</h3>", unsafe_allow_html=True)
    st.markdown('<table style="width:100%; text-align:center; color:#888;"><tr><th>SUN</th><th>MON</th><th>TUE</th><th>WED</th><th>THU</th><th>FRI</th><th>SAT</th></tr></table>', unsafe_allow_html=True)
    
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
                    label = f"{day}\n\n" + (f"👥{info['count']}" if info['count']>0 else "") + (" 🏆" if info['is_match'] else "")
                    st.markdown(f'<div class="{c_class}">', unsafe_allow_html=True)
                    if st.button(label, key=f"btn_{year}_{month}_{day}"):
                        st.session_state.view_date = datetime.date(year, month, day)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 메인 레이아웃 실행
t_month = today.replace(day=1)
n_month = (t_month + timedelta(days=32)).replace(day=1)
col_l, col_r = st.columns(2)
with col_l: draw_calendar(t_month.year, t_month.month, df)
with col_r: draw_calendar(n_month.year, n_month.month, df)

# 하단 타임라인 상세
st.write("---")
sel = st.session_state.view_date
day_df = df[df['날짜'] == sel].copy() if not df.empty else pd.DataFrame()
if not day_df.empty:
    st.markdown(f"### 📊 {sel} 타임라인")
    base = datetime.datetime.combine(sel, datetime.time.min)
    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=int(x)))
    day_df['end_dt'] = day_df.apply(lambda r: base + datetime.timedelta(days=(1 if int(r['종료']) <= int(r['시작']) else 0), hours=int(r['종료'])), axis=1)
    fig = px.timeline(day_df, x_start="start_dt", x_end="end_dt", y="이름", color="이름", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
