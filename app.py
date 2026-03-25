import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import timedelta, timezone
import plotly.express as px
import numpy as np
import calendar

# [1] 기본 설정: 일요일 시작 고정 및 서울 시간(KST) 세팅
calendar.setfirstweekday(calendar.SUNDAY)
KST = timezone(timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
# 2026년 연도 고정 (월/일은 한국 실시간 반영)
today = datetime.date(2026, now_kst.month, now_kst.day)

st.set_page_config(page_title="AION2 Raid Master", layout="wide")

# [2] 반응형 CSS: PC와 모바일을 구분하여 최적화
st.markdown("""
    <style>
    /* 공통 배경 및 카드 스타일 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .calendar-card {
        background-color: #1A1D24; border: 1px solid #36393E;
        border-radius: 12px; padding: 15px; margin-bottom: 20px;
    }
    
    /* 8명 매칭 성공 시 황금 효과 */
    div.match-gold button {
        background: linear-gradient(135deg, #443714 0%, #1A1D24 100%) !important;
        border: 1px solid #FFD700 !important; color: #FFD700 !important;
        font-weight: bold !important;
        box-shadow: 0 0 8px rgba(255, 215, 0, 0.2) !important;
    }

    /* ---------------------------------
       PC 버전 전용 스타일 (768px 이상)
       --------------------------------- */
    @media (min-width: 768px) {
        .stButton > button {
            height: 85px !important;
            font-size: 0.95rem !important;
        }
        [data-testid="column"] { padding: 0 10px !important; }
    }

    /* ---------------------------------
       모바일 버전 전용 스타일 (767px 이하)
       --------------------------------- */
    @media (max-width: 767px) {
        /* 모바일에서 7열 강제 유지 핵심 설정 */
        [data-testid="column"] {
            width: 14% !important;
            flex: 1 1 14% !important;
            min-width: 14% !important;
            padding: 1px !important;
        }
        
        /* 컬럼 세로 정렬(Stacking) 방지 */
        [data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            display: flex !important;
            flex-wrap: nowrap !important;
        }

        /* 모바일용 버튼 및 텍스트 축소 */
        .stButton > button {
            height: 55px !important;
            font-size: 0.65rem !important;
            padding: 0px !important;
            line-height: 1.1 !important;
        }
        
        .day-header { font-size: 0.6rem !important; }
        .month-title { font-size: 0.9rem !important; }
    }

    .sun-text { color: #FF4B4B !important; }
    </style>
    """, unsafe_allow_html=True)

# [3] 데이터 연동 함수 (구글 시트 Sheet1:일정, Sheet2:명단)
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
        members = s2.col_values(1)[1:] # 헤더 제외
        return members if members else ["공대장"]
    return ["공대장"]

df = load_raid_data()
MEMBER_LIST = load_member_list()

if 'view_date' not in st.session_state:
    st.session_state.view_date = today

# [4] 사이드바: 관리자 설정 및 일정 등록
with st.sidebar:
    st.markdown("<h3 style='color:#FF4B4B;'>🛡️ AION2 본부</h3>", unsafe_allow_html=True)
    st.caption(f"📍 KST: {today}")
    
    with st.expander("🔐 관리자 설정"):
        pw = st.text_input("관리자 PW", type="password")
        if pw == "1234": # 비밀번호 수정 가능
            new_name = st.text_input("새 대원 이름")
            if st.button("➕ 추가"):
                _, s2 = get_sheets(); s2.append_row([new_name])
                st.cache_data.clear(); st.rerun()
            target_del = st.selectbox("삭제 대원", MEMBER_LIST)
            if st.button("❌ 삭제"):
                _, s2 = get_sheets(); cell = s2.find(target_del)
                s2.delete_rows(cell.row); st.cache_data.clear(); st.rerun()

    st.divider()
    reg_date = st.date_input("📅 날짜 선택", st.session_state.view_date)
    name = st.selectbox("👤 이름 선택", MEMBER_LIST)
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

# [5] 달력 렌더링 함수
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
    st.markdown(f"<p class='month-title' style='text-align:center; color:#FFD700; font-weight:bold; margin-bottom:10px;'>{year}년 {month}월</p>", unsafe_allow_html=True)
    
    # 요일 헤더 가로 고정
    h_cols = st.columns(7)
    days_ko = ["일", "월", "화", "수", "목", "금", "토"]
    for i, d in enumerate(days_ko):
        color = "#FF4B4B" if i == 0 else "#888"
        h_cols[i].markdown(f"<p class='day-header' style='text-align:center; color:{color}; margin:0;'>{d}</p>", unsafe_allow_html=True)
    
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
                    label = f"{day}\n" + (f"👥{info['count']}" if info['count']>0 else "") + ("🏆" if info['is_match'] else "")
                    
                    st.markdown(f'<div class="{c_class}">', unsafe_allow_html=True)
                    if st.button(label, key=f"btn_{year}_{month}_{day}"):
                        st.session_state.view_date = datetime.date(year, month, day)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else: st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

# [6] 메인 레이아웃: 이번 달과 다음 달 표시
t_month = today.replace(day=1)
n_month = (t_month + timedelta(days=32)).replace(day=1)

# PC에서는 가로로 2개, 모바일에서는 세로로 2개 자동 배치 (CSS 미디어 쿼리 영향)
col_l, col_r = st.columns(2)
with col_l: draw_calendar(t_month.year, t_month.month, df)
with col_r: draw_calendar(n_month.year, n_month.month, df)

# 하단 상세 타임라인
st.write("---")
sel = st.session_state.view_date
day_df = df[df['날짜'] == sel].copy() if not df.empty else pd.DataFrame()
if not day_df.empty:
    st.markdown(f"<h6>📊 {sel} 타임라인</h6>", unsafe_allow_html=True)
    base = datetime.datetime.combine(sel, datetime.time.min)
    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=int(x)))
    day_df['end_dt'] = day_df.apply(lambda r: base + datetime.timedelta(days=(1 if int(r['종료']) <= int(r['시작']) else 0), hours=int(r['종료'])), axis=1)
    fig = px.timeline(day_df, x_start="start_dt", x_end="end_dt", y="이름", color="이름", template="plotly_dark")
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=0), height=250)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(f"{sel} 등록된 일정이 없습니다.")
