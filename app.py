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

# [2] CSS (디자인 개선)
st.markdown("""
<style>
.stApp { background-color: #0E1117; color: #E0E0E0; }

.calendar-card {
    background-color: #1A1D24;
    border: 1px solid #36393E;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

/* 오늘 */
.today-highlight button {
    border: 2px solid #00E5FF !important;
    box-shadow: 0 0 8px rgba(0,229,255,0.5) !important;
}

/* 선택 */
.selected-day button {
    border: 2px solid #FFD700 !important;
    background-color: #2A2E39 !important;
}

/* 인원수 단계 */
.low-count button { opacity: 0.6; }
.mid-count button { border: 1px solid #4B8BFF; }
.high-count button { border: 1px solid #FFD700; }

/* 8인 */
.match-gold button {
    background: linear-gradient(135deg, #443714 0%, #1A1D24 100%) !important;
    border: 1px solid #FFD700 !important;
    color: #FFD700 !important;
    font-weight: bold !important;
    animation: glow 1.5s infinite alternate;
}

@keyframes glow {
    from { box-shadow: 0 0 5px #FFD700; }
    to { box-shadow: 0 0 15px #FFD700; }
}

/* hover */
.stButton > button:hover {
    transform: scale(1.05);
    transition: 0.15s;
}

.month-title {
    letter-spacing: 1px;
    text-shadow: 0 0 6px rgba(255,215,0,0.5);
}

@media (max-width: 767px) {
    [data-testid="column"] {
        width: 14% !important;
        flex: 1 1 14% !important;
        min-width: 14% !important;
        padding: 1px !important;
    }

    [data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        display: flex !important;
        flex-wrap: nowrap !important;
    }

    .stButton > button {
        height: 55px !important;
        font-size: 0.65rem !important;
        padding: 0px !important;
        line-height: 1.1 !important;
    }
}

.sun-text { color: #FF4B4B !important; }
</style>
""", unsafe_allow_html=True)

# [3] 시트 연동 (절대 수정 없음)
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
        if not data.empty:
            data['날짜'] = pd.to_datetime(data['날짜']).dt.date
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

# [4] 사이드바 (수정 없음)
with st.sidebar:
    st.markdown("<h3 style='color:#FF4B4B;'>🛡️ AION2 본부</h3>", unsafe_allow_html=True)
    st.caption(f"📍 KST: {today}")

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
                    rows.append([str(reg_date), name, s_time, e_time])
                    found = True
                else:
                    rows.append(r)
            if not found:
                rows.append([str(reg_date), name, s_time, e_time])
            s1.update('A1', rows)
            st.cache_data.clear()
            st.rerun()

# [5] 8인 체크 (수정 없음)
def check_8man_match(day_df):
    if len(day_df) < 8:
        return False
    timeline = np.zeros(48)
    for _, row in day_df.iterrows():
        s, e = int(row['시작']), int(row['종료'])
        if e <= s:
            e += 24
        timeline[s:e] += 1
    return np.any(timeline >= 8)

# [6] 달력
def draw_calendar(year, month, data_df):
    st.markdown('<div class="calendar-card">', unsafe_allow_html=True)
    st.markdown(f"<p class='month-title' style='text-align:center; color:#FFD700; font-weight:bold;'>{year}년 {month}월</p>", unsafe_allow_html=True)

    headers = ["일", "월", "화", "수", "목", "금", "토"]
    cols = st.columns(7)

    for i, d in enumerate(headers):
        if i == 0:
            color = "#FF4B4B"
        elif i == 6:
            color = "#4B8BFF"
        else:
            color = "#888"
        cols[i].markdown(f"<p style='text-align:center;color:{color};'>{d}</p>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(year, month)

    summary = {}
    if not data_df.empty:
        m_data = data_df[(data_df['날짜'].apply(lambda x: x.year == year and x.month == month))]
        for d in m_data['날짜'].unique():
            day_data = m_data[m_data['날짜'] == d]
            summary[d.day] = {
                'count': day_data['이름'].nunique(),
                'is_match': check_8man_match(day_data)
            }

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day != 0:
                    info = summary.get(day, {'count': 0, 'is_match': False})

                    c_class = ""

                    # 오늘
                    if year == today.year and month == today.month and day == today.day:
                        c_class += " today-highlight"

                    # 선택
                    if st.session_state.view_date == datetime.date(year, month, day):
                        c_class += " selected-day"

                    # 인원수
                    if info['count'] <= 3:
                        c_class += " low-count"
                    elif info['count'] <= 7:
                        c_class += " mid-count"
                    else:
                        c_class += " high-count"

                    # 8인
                    if info['is_match']:
                        c_class += " match-gold"

                    label = f"{day}"
                    if info['count'] > 0:
                        label += f"\n👥{info['count']}"
                    if info['is_match']:
                        label += "\n🏆"

                    st.markdown(f'<div class="{c_class}">', unsafe_allow_html=True)
                    if st.button(label, key=f"btn_{year}_{month}_{day}"):
                        st.session_state.view_date = datetime.date(year, month, day)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.empty()

    st.markdown("</div>", unsafe_allow_html=True)

# [7] 출력
t_month = today.replace(day=1)
n_month = (t_month + timedelta(days=32)).replace(day=1)

col1, col2 = st.columns(2)
with col1:
    draw_calendar(t_month.year, t_month.month, df)
with col2:
    draw_calendar(n_month.year, n_month.month, df)

# [8] 타임라인 (수정 없음)
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
