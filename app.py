import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import timedelta, timezone
import plotly.express as px
import numpy as np
import calendar

# =========================
# [1] 기본 설정
# =========================
calendar.setfirstweekday(calendar.SUNDAY)
KST = timezone(timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
today = datetime.date(2026, now_kst.month, now_kst.day)

st.set_page_config(page_title="AION2 Raid Master", layout="wide")

# =========================
# [2] CSS (전체 재정리)
# =========================
st.markdown("""
<style>
.stApp { background-color: #0E1117; color: #E0E0E0; }

/* 카드 */
.day-card {
    position: relative;
    background: #1A1D24;
    border: 1px solid #36393E;
    border-radius: 10px;
    height: 85px;
    padding: 6px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: 0.2s;
}

.day-card:hover {
    transform: scale(1.04);
    border: 1px solid #888;
}

/* 텍스트 */
.day-num { font-size: 14px; font-weight: bold; }
.day-info { font-size: 11px; }

/* 상태 */
.today { border: 2px solid #00E5FF !important; }
.selected { border: 2px solid #FFD700 !important; background: #2A2E39; }

.low { opacity: 0.5; }
.mid { border: 1px solid #4B8BFF; }
.high { border: 1px solid #FFD700; }

.raid {
    background: linear-gradient(135deg, #443714 0%, #1A1D24 100%);
    color: #FFD700;
    font-weight: bold;
}

/* 클릭 레이어 */
.click-layer button {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
}

/* 모바일 7열 유지 */
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
}
</style>
""", unsafe_allow_html=True)

# =========================
# [3] 시트 연동 (절대 유지)
# =========================
def get_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client = gspread.authorize(creds)
        doc = client.open("AION2_Raid_Data")
        return doc.get_worksheet(0), doc.get_worksheet(1)
    except:
        return None, None

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

# =========================
# [4] 사이드바 (유지)
# =========================
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

# =========================
# [5] 8인 체크 (유지)
# =========================
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

# =========================
# [6] 달력 (완전 교체)
# =========================
def draw_calendar(year, month, data_df):
    st.markdown(f"<h4 style='text-align:center;color:#FFD700'>{year}년 {month}월</h4>", unsafe_allow_html=True)

    headers = ["일", "월", "화", "수", "목", "금", "토"]
    cols = st.columns(7)

    for i, d in enumerate(headers):
        color = "#FF4B4B" if i == 0 else "#4B8BFF" if i == 6 else "#888"
        cols[i].markdown(f"<p style='text-align:center;color:{color};font-size:12px'>{d}</p>", unsafe_allow_html=True)

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
                if day == 0:
                    st.empty()
                    continue

                info = summary.get(day, {'count': 0, 'is_match': False})

                classes = "day-card"

                if year == today.year and month == today.month and day == today.day:
                    classes += " today"

                if st.session_state.view_date == datetime.date(year, month, day):
                    classes += " selected"

                if info['count'] <= 3:
                    classes += " low"
                elif info['count'] <= 7:
                    classes += " mid"
                else:
                    classes += " high"

                if info['is_match']:
                    classes += " raid"

                html = f"""
                <div class="{classes}">
                    <div class="day-num">{day}</div>
                    <div class="day-info">
                        {"👥 " + str(info['count']) if info['count'] else ""}
                        {"<br>🏆 RAID" if info['is_match'] else ""}
                    </div>
                </div>
                """

                st.markdown(html, unsafe_allow_html=True)

                st.markdown('<div class="click-layer">', unsafe_allow_html=True)
                if st.button("", key=f"btn_{year}_{month}_{day}"):
                    st.session_state.view_date = datetime.date(year, month, day)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

# =========================
# [7] 출력
# =========================
t_month = today.replace(day=1)
n_month = (t_month + timedelta(days=32)).replace(day=1)

col1, col2 = st.columns(2)
with col1:
    draw_calendar(t_month.year, t_month.month, df)
with col2:
    draw_calendar(n_month.year, n_month.month, df)

# =========================
# [8] 타임라인 (유지)
# =========================
st.write("---")
sel = st.session_state.view_date
day_df = df[df['날짜'] == sel].copy() if not df.empty else pd.DataFrame()

if not day_df.empty:
    st.markdown(f"<h6>📊 {sel} 타임라인</h6>", unsafe_allow_html=True)
    base = datetime.datetime.combine(sel, datetime.time.min)
    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=int(x)))
    day_df['end_dt'] = day_df.apply(
        lambda r: base + datetime.timedelta(days=(1 if int(r['종료']) <= int(r['시작']) else 0),
                                            hours=int(r['종료'])), axis=1)

    fig = px.timeline(day_df, x_start="start_dt", x_end="end_dt",
                      y="이름", color="이름", template="plotly_dark")

    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=0), height=250)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(f"{sel} 등록된 일정이 없습니다.")
