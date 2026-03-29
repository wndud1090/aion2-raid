import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import timedelta, timezone
import plotly.express as px
import numpy as np
import calendar

# [1] 기본 설정 및 시간 (서울 기준)
calendar.setfirstweekday(calendar.SUNDAY)
KST = timezone(timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
# 2026년으로 연도 고정 (월, 일은 한국 실시간 반영)
today = datetime.date(2026, now_kst.month, now_kst.day)

st.set_page_config(page_title="AION2 Raid Master", layout="wide")

# [2] CSS: 이중 구조를 삭제하고 날짜 칸 전체를 버튼으로 통합
st.markdown("""
    <style>
    /* 전체 배경 */
    [data-testid="stAppViewContainer"] {
        background-color: #0E1117; color: #E0E0E0;
    }

    /* 달력 그리드 설계 */
    .calendar-container {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }

    /* 요일 헤더 */
    .weekday-header {
        text-align: center; color: #666; font-size: 0.8rem; font-weight: bold;
        padding: 10px 0; border-bottom: 1px solid #36393E;
    }
    .sun-text { color: #ff4b4b !important; }

    /* ★ 핵심: 일체형 날짜 버튼 디자인 ★ */
    /* 버튼을 날짜 칸처럼 스타일링 */
    .stButton > button {
        border: 1px solid #262730 !important;
        background: #121212 !important;
        border-radius: 12px !important;
        height: 100px !important; /* 모바일 대응 시 줄여야 함 */
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
        padding: 12px !important;
        transition: all 0.3s ease !important;
    }

    /* 호버 효과 */
    .stButton > button:hover {
        border-color: #ff4b4b !important;
        background: #1a1a1a !important;
    }

    /* 인원 있음 (녹색 표시) */
    .has-members button { color: #32CD32 !important; font-weight: bold; }

    /* ★ 8명 매칭 성공: 황금색 테두리 및 그라데이션 강제 적용 ★ */
    div.match-gold button {
        background: linear-gradient(135deg, #443714 0%, #1A1D24 100%) !important;
        border: 2px solid #FFD700 !important;
        color: #FFD700 !important;
        font-weight: 900 !important;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.4) !important;
    }
    
    /* 오늘 날짜 표시 */
    div.is-today button { border: 2px solid #555 !important; }

    /* 버튼 내부 텍스트 스타일 */
    .stButton > button div { text-align: left !important; }
    .sun-text-btn { color: #ff4b4b !important; } /* 일요일 숫자 색상 */

    /* 모바일 반응형 (너비가 768px 미만일 때) */
    @media (max-width: 768px) {
        .stButton > button { height: 70px !important; padding: 5px !important; font-size: 0.8rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# [3] 데이터 로직 (Sheet1: 일정, Sheet2: 명단)
def get_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client = gspread.authorize(creds)
        doc = client.open("AION2_Raid_Data")
        return doc.get_worksheet(0), doc.get_worksheet(1)
    except: return None, None

@st.cache_data(ttl=5)
def load_data():
    s1, s2 = get_sheets()
    if s1:
        data = pd.DataFrame(s1.get_all_records())
        if not data.empty: data['날짜'] = pd.to_datetime(data['날짜']).dt.date
    else: data = pd.DataFrame()
    members = s2.col_values(1)[1:] if s2 else ["공대장"]
    return data, members

df, MEMBER_LIST = load_data()

# [4] 매칭 계산 로직
def check_8man_match(day_df):
    if len(day_df) < 8: return False
    timeline = np.zeros(48)
    for _, row in day_df.iterrows():
        s, e = int(row['시작']), int(row['종료'])
        if e <= s: e += 24
        timeline[s:e] += 1
    return np.any(timeline >= 8)

# [5] 일체형 달력 렌더링 함수
def draw_calendar(year, month, data_df):
    st.markdown(f"<h3 style='text-align:center;'>{year}년 {month}월</h3>", unsafe_allow_html=True)
    
    # 요일 헤더
    cols_h = st.columns(7)
    days_h = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    for i, d in enumerate(days_h):
        cols_h[i].markdown(f"<div class='weekday-header {'sun-text' if i==0 else ''}'>{d}</div>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                target_date = datetime.date(year, month, day)
                day_data = data_df[data_df['날짜'] == target_date] if not data_df.empty else pd.DataFrame()
                count = day_data['이름'].nunique()
                is_match = check_8man_match(day_data)
                
                # 버튼에 적용할 클래스 조건
                wrapper_class = ""
                if is_match: wrapper_class = "match-gold"
                elif count > 0: wrapper_class = "has-members"
                if target_date == today: wrapper_class += " is-today"
                
                # 버튼 라벨 구성
                label = f"{day}"
                if count > 0: label += f"\n\n👥 {count}"
                if is_match: label += " 🏆"
                
                with cols[i]:
                    st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
                    if st.button(label, key=f"btn_{year}_{month}_{day}"):
                        st.session_state.target_date = target_date
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                cols[i].empty()

# [6] 메인 인터페이스
if 'target_date' not in st.session_state:
    st.session_state.target_date = today

t_month = today.replace(day=1)
n_month = (t_month + timedelta(days=32)).replace(day=1)

# 달력 영역
c1, c2 = st.columns(2)
with c1: draw_calendar(t_month.year, t_month.month, df)
with c2: draw_calendar(n_month.year, n_month.month, df)

st.divider()

# 하단 등록 및 명단 관리
l_col, r_col = st.columns([1, 2.5])
with l_col:
    st.subheader(f"📅 {st.session_state.target_date}")
    name = st.selectbox("공대원 선택", MEMBER_LIST)
    c_s, c_e = st.columns(2)
    s_t = c_s.number_input("시작", 0, 23, 22)
    e_t = c_e.number_input("종료", 0, 23, 2)
    
    if st.button("🚀 일정 확정", use_container_width=True):
        s1, _ = get_sheets()
        if s1:
            all_data = s1.get_all_values()
            new_rows = [all_data[0]]
            f = False
            for r in all_data[1:]:
                if r[0] == str(st.session_state.target_date) and r[1] == name:
                    new_rows.append([str(st.session_state.target_date), name, s_t, e_t]); f = True
                else: new_rows.append(r)
            if not f: new_rows.append([str(st.session_state.target_date), name, s_t, e_t])
            s1.update('A1', new_rows)
            st.cache_data.clear(); st.rerun()

with r_col:
    sel_df = df[df['날짜'] == st.session_state.target_date]
    if not sel_df.empty:
        st.markdown(f"### 👥 참여 인원 ({len(sel_df)}명)")
        st.dataframe(sel_df[['이름', '시작', '종료']], hide_index=True, use_container_width=True)
    else:
        st.info("선택된 날짜에 등록된 인원이 없습니다.")
