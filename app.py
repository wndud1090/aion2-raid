import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import timedelta, timezone
import calendar
import numpy as np

# [1] 시간 및 기본 설정
calendar.setfirstweekday(calendar.SUNDAY)
KST = timezone(timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
today = datetime.date(2026, now_kst.month, now_kst.day)

st.set_page_config(page_title="AION2 RAID MASTER", layout="wide")

# [2] 일체형 디자인을 위한 CSS (이중 구조 삭제)
st.markdown("""
    <style>
    /* 전체 배경 */
    [data-testid="stAppViewContainer"] { background-color: #050505 !important; color: #ffffff; }

    /* 달력 그리드 */
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }

    /* 요일 헤더 */
    .weekday { text-align: center; color: #666; font-size: 0.8rem; font-weight: bold; padding: 10px 0; }
    .sun { color: #ff4b4b !important; }

    /* ★ 핵심: 일체형 날짜 버튼 스타일 ★ */
    .stButton > button {
        border: 1px solid #222 !important;
        background: #121212 !important;
        border-radius: 12px !important;
        height: 100px !important;
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
        padding: 12px !important;
        transition: all 0.3s ease !important;
        color: #aaa !important;
    }

    .stButton > button:hover {
        border-color: #ff4b4b !important;
        background: #1a1a1a !important;
        transform: translateY(-2px);
    }

    /* 선택된 날짜 강조 */
    .stButton > button:focus, .stButton > button:active {
        border: 2px solid #ff4b4b !important;
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.3) !important;
    }

    /* 8명 매칭 성공 시 황금색 일체형 버튼 */
    div.match-gold > div > button {
        background: linear-gradient(145deg, #1e1b0a 0%, #0a0a0a 100%) !important;
        border: 1px solid #ffd700 !important;
        color: #ffd700 !important;
    }
    
    /* 오늘 날짜 표시 */
    div.is-today > div > button { border: 2px solid #555 !important; }

    /* 버튼 내부 텍스트 정렬 */
    .day-label { font-size: 1.1rem; font-weight: bold; }
    .count-label { font-size: 0.75rem; margin-top: auto; color: #00ff88; }
    .trophy { position: absolute; top: 10px; right: 10px; }

    @media (max-width: 768px) {
        .stButton > button { height: 70px !important; padding: 5px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# [3] 데이터 로드 (Sheet1: 일정, Sheet2: 명단)
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
    df = pd.DataFrame(s1.get_all_records()) if s1 else pd.DataFrame()
    if not df.empty: df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    members = s2.col_values(1)[1:] if s2 else ["공대장"]
    return df, members

df, MEMBER_LIST = load_data()

# [4] 매칭 계산
def check_match(day_df):
    if len(day_df) < 8: return False
    timeline = np.zeros(48)
    for _, row in day_df.iterrows():
        s, e = int(row['시작']), int(row['종료'])
        if e <= s: e += 24
        timeline[s:e] += 1
    return np.any(timeline >= 8)

# [5] 일체형 달력 렌더링
def draw_calendar(year, month, data_df):
    st.markdown(f"<h3 style='text-align:center;'>{year}년 {month}월</h3>", unsafe_allow_html=True)
    
    # 요일 표시
    h_cols = st.columns(7)
    for i, w in enumerate(["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]):
        h_cols[i].markdown(f"<div class='weekday {'sun' if i==0 else ''}'>{w}</div>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0: continue
            
            target_date = datetime.date(year, month, day)
            day_data = data_df[data_df['날짜'] == target_date] if not data_df.empty else pd.DataFrame()
            count = day_data['이름'].nunique()
            is_match = check_match(day_data)
            
            # 버튼에 적용할 클래스 조건
            wrapper_class = ""
            if is_match: wrapper_class = "match-gold"
            elif target_date == today: wrapper_class = "is-today"
            
            # 버튼 라벨 구성
            label = f"{day}"
            if count > 0: label += f"\n\n👥 {count}"
            if is_match: label += " 🏆"

            with cols[i]:
                st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
                if st.button(label, key=f"btn-{year}-{month}-{day}"):
                    st.session_state.sel_date = target_date
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# [6] 메인 실행
if 'sel_date' not in st.session_state: st.session_state.sel_date = today

t_month = today.replace(day=1)
n_month = (t_month + timedelta(days=32)).replace(day=1)

c1, c2 = st.columns(2)
with c1: draw_calendar(t_month.year, t_month.month, df)
with c2: draw_calendar(n_month.year, n_month.month, df)

st.divider()

# 하단 등록 및 명단 관리 (공대장 전용 기능 유지)
left, right = st.columns([1, 2])
with left:
    st.subheader(f"📅 {st.session_state.sel_date}")
    name = st.selectbox("대원 선택", MEMBER_LIST)
    s, e = st.columns(2)
    s_t = s.number_input("시작", 0, 23, 22)
    e_t = e.number_input("종료", 0, 23, 2)
    if st.button("🚀 일정 확정", use_container_width=True):
        s1, _ = get_sheets()
        if s1:
            all_v = s1.get_all_values()
            rows = [all_v[0]]
            found = False
            for r in all_v[1:]:
                if r[0] == str(st.session_state.sel_date) and r[1] == name:
                    rows.append([str(st.session_state.sel_date), name, s_t, e_t]); found = True
                else: rows.append(r)
            if not found: rows.append([str(st.session_state.sel_date), name, s_t, e_t])
            s1.update('A1', rows)
            st.cache_data.clear(); st.rerun()

with right:
    day_df = df[df['날짜'] == st.session_state.sel_date]
    if not day_df.empty:
        st.write(f"### 👥 참여 명단 ({len(day_df)}명)")
        st.dataframe(day_df[['이름', '시작', '종료']], hide_index=True, use_container_width=True)
    else:
        st.info("등록된 일정이 없습니다.")
