import streamlit as st
import pandas as pd
import numpy as np
import datetime
import calendar
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(layout="wide")
calendar.setfirstweekday(calendar.SUNDAY)

# ---------------------------
# 🎨 업그레이드 CSS
# ---------------------------
st.markdown("""
<style>
body {
    background: radial-gradient(circle at top, #0a0a0a, #050505);
    color: white;
}

/* 캘린더 */
.calendar {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 12px;
}

/* 카드 */
.day-card {
    position: relative;
    background: rgba(18,18,18,0.8);
    backdrop-filter: blur(10px);
    padding: 14px;
    border-radius: 14px;
    min-height: 120px;
    cursor: pointer;
    transition: all 0.25s ease;
    border: 1px solid #222;
    overflow: hidden;
}

/* hover */
.day-card:hover {
    transform: translateY(-4px) scale(1.02);
    border: 1px solid #ff4dd2;
    box-shadow: 0 0 12px rgba(255,77,210,0.4);
}

/* 선택된 날짜 */
.selected {
    border: 2px solid #ff4dd2 !important;
    box-shadow: 0 0 18px rgba(255,77,210,0.7);
}

/* 성공 */
.success {
    background: linear-gradient(135deg, #FFD700, #b8860b);
    color: black;
    font-weight: bold;
    box-shadow: 0 0 20px rgba(255,215,0,0.6);
}

/* 날짜 */
.day-title {
    font-size: 18px;
    font-weight: bold;
}

/* invisible button */
.day-btn {
    position: absolute;
    top:0; left:0;
    width:100%;
    height:100%;
    opacity:0;
}

/* 타임라인 */
.timeline {
    display: flex;
    overflow-x: auto;
    margin-top: 10px;
}

.slot {
    min-width: 22px;
    height: 40px;
    margin-right: 2px;
    border-radius: 4px;
    background: #333;
    text-align: center;
    font-size: 10px;
}

.slot.full {
    background: gold;
    color: black;
}

/* 모바일 */
@media (max-width: 768px) {
    .calendar {
        grid-template-columns: repeat(7, 1fr);
    }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Google Sheets
# ---------------------------
@st.cache_resource
def connect():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope
    )
    return gspread.authorize(creds)

client = connect()
sheet = client.open("AION2_RAID")

schedule_ws = sheet.worksheet("Sheet1")
members_ws = sheet.worksheet("Sheet2")

def load():
    df = pd.DataFrame(schedule_ws.get_all_records())
    members = pd.DataFrame(members_ws.get_all_records())
    return df, members

df, members_df = load()

# ---------------------------
# 슬롯
# ---------------------------
def slots():
    return [f"{i//2:02d}:{'00' if i%2==0 else '30'}" for i in range(48)]

slot_labels = slots()

# ---------------------------
# 저장
# ---------------------------
def save(name, dates, start, end):
    rows = []
    for d in dates:
        for i in range(start, end):
            rows.append([name, d.strftime("%Y-%m-%d"), i])
    if rows:
        schedule_ws.append_rows(rows)

# ---------------------------
# 매칭
# ---------------------------
def match(df):
    result = {}
    if df.empty:
        return result

    g = df.groupby(["date","slot"]).count().reset_index()

    for d in df["date"].unique():
        day = g[g["date"]==d]
        full = day[day["name"]>=8]
        result[d] = len(full)>=2

    return result

match_dict = match(df)

# ---------------------------
# 세션
# ---------------------------
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

# ---------------------------
# 입력 UI
# ---------------------------
st.title("🎮 AION2 레이드 일정")

c1,c2 = st.columns(2)

with c1:
    name = st.selectbox("공대원", members_df["name"])

with c2:
    dates = st.date_input("날짜 (다중)", [])

start = st.slider("시작",0,47,18)
end = st.slider("종료",0,47,24)

if st.button("저장"):
    save(name, dates, start, end)
    st.success("완료")
    st.rerun()

# ---------------------------
# 캘린더
# ---------------------------
today = datetime.date.today()
year, month = today.year, today.month
cal = calendar.monthcalendar(year, month)

st.subheader(f"{year}년 {month}월")

cols = st.columns(7)

for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.empty()
            else:
                d = datetime.date(year, month, day)
                d_str = d.strftime("%Y-%m-%d")

                success = match_dict.get(d_str, False)
                selected = (st.session_state.selected_date == d_str)

                cls = "day-card"
                if success: cls += " success"
                if selected: cls += " selected"

                # 카드 UI
                st.markdown(f"""
                <div class="{cls}">
                    <div class="day-title">{day} {'🏆' if success else ''}</div>
                </div>
                """, unsafe_allow_html=True)

                # 클릭 버튼 (핵심)
                if st.button("", key=d_str):
                    st.session_state.selected_date = d_str
                    st.rerun()

# ---------------------------
# 📊 상세 패널
# ---------------------------
if st.session_state.selected_date:

    st.markdown("---")
    st.subheader(f"📅 {st.session_state.selected_date} 상세")

    day_df = df[df["date"]==st.session_state.selected_date]

    slot_count = np.zeros(48)

    for _, r in day_df.iterrows():
        slot_count[int(r["slot"])] += 1

    # 타임라인
    html = '<div class="timeline">'
    for i, c in enumerate(slot_count):
        cls = "slot full" if c>=8 else "slot"
        html += f'<div class="{cls}">{int(c)}</div>'
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

    # 설명
    st.write("🟡 금색 = 8명 풀 매칭 슬롯")
    st.write("숫자 = 해당 시간 참여 인원")
