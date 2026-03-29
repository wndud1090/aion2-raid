import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import timedelta, timezone
import calendar
import numpy as np

# [1] 기본 설정 및 시간 (서울 기준)
calendar.setfirstweekday(calendar.SUNDAY)
KST = timezone(timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
today = datetime.date(2026, now_kst.month, now_kst.day)

st.set_page_config(page_title="AION2 RAID MASTER", layout="wide")

# [2] 압도적인 비주얼을 위한 커스텀 CSS (핵심)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;500;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Noto+Sans+KR', sans-serif;
        background-color: #050505 !important;
        color: #ffffff;
    }

    /* 달력 그리드 설계 */
    .calendar-container {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 8px;
        margin-bottom: 30px;
    }

    /* 요일 헤더 */
    .weekday-header {
        text-align: center;
        font-weight: 700;
        font-size: 0.8rem;
        padding-bottom: 10px;
        color: #666;
        text-transform: uppercase;
    }
    .sun { color: #ff4b4b !important; }

    /* 날짜 카드 기본 디자인 */
    .day-card {
        background: #121212;
        border: 1px solid #222;
        border-radius: 10px;
        aspect-ratio: 1 / 1.1;
        padding: 10px;
        position: relative;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .day-card:hover {
        border-color: #ff4b4b;
        transform: translateY(-3px);
        background: #1a1a1a;
    }

    /* 날짜 숫자 */
    .day-num { font-size: 1rem; font-weight: 500; color: #aaa; }
    
    /* 인원 표시 배지 */
    .member-badge {
        position: absolute;
        bottom: 10px;
        right: 10px;
        font-size: 0.75rem;
        color: #00ff88;
        font-weight: 700;
    }

    /* [하이라이트] 8명 매칭 성공 카드 */
    .match-gold {
        background: linear-gradient(145deg, #1e1b0a 0%, #0a0a0a 100%) !important;
        border: 1px solid #ffd700 !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.2);
    }
    .match-gold .day-num { color: #ffd700; font-weight: 700; }
    .match-gold::after {
        content: '🏆';
        position: absolute;
        top: 8px;
        right: 8px;
        font-size: 0.8rem;
    }

    /* 오늘 날짜 표시 */
    .is-today { border: 2px solid #ff4b4b !important; }

    /* 모바일 대응 */
    @media (max-width: 768px) {
        .calendar-container { gap: 4px; }
        .day-card { padding: 5px; border-radius: 6px; }
        .day-num { font-size: 0.8rem; }
        .member-badge { font-size: 0.6rem; bottom: 5px; right: 5px; }
    }
    </style>
    """, unsafe_allow_html=True)

# [3] 데이터 연동 로직 (Sheet1: 일정, Sheet2: 명단)
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
    if not s1: return pd.DataFrame(), ["공대장"]
    df = pd.DataFrame(s1.get_all_records())
    if not df.empty: df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    members = s2.col_values(1)[1:] if s2 else ["공대장"]
    return df, (members if members else ["공대장"])

df, MEMBER_LIST = load_data()

# [4] 8인 매칭 계산 로직
def check_match(day_df):
    if len(day_df) < 8: return False
    timeline = np.zeros(48)
    for _, row in day_df.iterrows():
        s, e = int(row['시작']), int(row['종료'])
        if e <= s: e += 24
        timeline[s:e] += 1
    return np.any(timeline >= 8)

# [5] 새로운 카드형 달력 렌더링 함수
def render_calendar(year, month, data_df):
    st.markdown(f"<h2 style='text-align:center; color:#fff; margin-bottom:20px;'>{year}년 {month}월</h2>", unsafe_allow_html=True)
    
    # 요일 헤더
    cols = st.columns(7)
    weekdays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    for i, w in enumerate(weekdays):
        cls = "sun" if i == 0 else ""
        cols[i].markdown(f"<div class='weekday-header {cls}'>{w}</div>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("<div style='aspect-ratio:1/1.1;'></div>", unsafe_allow_html=True)
                continue
            
            # 해당 날짜 데이터 추출
            target_date = datetime.date(year, month, day)
            day_data = data_df[data_df['날짜'] == target_date] if not data_df.empty else pd.DataFrame()
            count = day_data['이름'].nunique()
            is_match = check_match(day_data)
            
            # 클래스 결정
            card_class = "day-card"
            if is_match: card_class += " match-gold"
            if target_date == today: card_class += " is-today"
            
            # 카드 출력 (버튼 대신 clickable div 형태 모사)
            with cols[i]:
                # 실제 클릭 기능을 위해 투명 버튼을 카드 위에 겹침
                if st.button(f"{day}", key=f"d-{year}-{month}-{day}", help=f"{count}명 등록됨"):
                    st.session_state.selected_date = target_date
                    st.rerun()
                
                # 시각적 카드 디자인
                badge_html = f"<div class='member-badge'>👥 {count}</div>" if count > 0 else ""
                st.markdown(f"""
                    <div class="{card_class}" style="margin-top:-50px; pointer-events:none;">
                        <div class="day-num">{day}</div>
                        {badge_html}
                    </div>
                """, unsafe_allow_html=True)

# [6] 메인 레이아웃
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = today

# 상단: 달력 영역
t_month = today.replace(day=1)
n_month = (t_month + timedelta(days=32)).replace(day=1)

c1, c2 = st.columns(2)
with c1: render_calendar(t_month.year, t_month.month, df)
with c2: render_calendar(n_month.year, n_month.month, df)

# 하단: 정보 및 등록 영역
st.divider()
left, right = st.columns([1, 2])

with left:
    st.subheader(f"📅 {st.session_state.selected_date}")
    name = st.selectbox("대원 선택", MEMBER_LIST)
    s_t = st.number_input("시작", 0, 23, 22)
    e_t = st.number_input("종료", 0, 23, 2)
    if st.button("일정 저장", use_container_width=True):
        s1, _ = get_sheets()
        if s1:
            all_v = s1.get_all_values()
            new_rows = [all_v[0]]
            found = False
            for r in all_v[1:]:
                if r[0] == str(st.session_state.selected_date) and r[1] == name:
                    new_rows.append([str(st.session_state.selected_date), name, s_t, e_t]); found = True
                else: new_rows.append(r)
            if not found: new_rows.append([str(st.session_state.selected_date), name, s_t, e_t])
            s1.update('A1', new_rows)
            st.cache_data.clear(); st.rerun()

with right:
    # 선택된 날짜의 타임라인을 더 깔끔하게 표시
    sel_df = df[df['날짜'] == st.session_state.selected_date]
    if not sel_df.empty:
        st.write(f"### 👥 참여 인원 ({len(sel_df)}명)")
        # 타임라인 차트 생략 (원하실 경우 추가 가능)
        st.dataframe(sel_df[['이름', '시작', '종료']], hide_index=True, use_container_width=True)
    else:
        st.info("선택된 날짜에 등록된 일정이 없습니다.")
