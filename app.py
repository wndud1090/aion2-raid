import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from streamlit_calendar import calendar

st.set_page_config(layout="wide")

# =========================
# CSS (깜빡임)
# =========================
st.markdown("""
<style>
@keyframes blink {
  0% {opacity: 1;}
  50% {opacity: 0.2;}
  100% {opacity: 1;}
}
.blink {
  animation: blink 1s infinite;
  font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


# =========================
# 구글 시트 연결
# =========================
@st.cache_resource
def connect():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)


client = connect()
sheet = client.open("AION2 RAID")
schedule_ws = sheet.worksheet("시트1")


# =========================
# 상태
# =========================
if "selected_dates" not in st.session_state:
    st.session_state.selected_dates = []


# =========================
# 공대원 색상
# =========================
member_colors = {
    "탱커": "#ff9900",
    "힐러": "#3399ff",
    "딜러1": "#66cc66",
    "딜러2": "#cc66ff",
    "딜러3": "#ff6699",
    "딜러4": "#00cccc",
    "딜러5": "#9999ff",
    "딜러6": "#ffcc00",
}


# =========================
# 데이터 로드
# =========================
rows = schedule_ws.get_all_values()

date_map = {}
time_map = {}

for row in rows:
    try:
        date_val = row[0]
        time_val = row[1]
        member = row[2]
        status = row[3]

        if date_val not in date_map:
            date_map[date_val] = {"가능": [], "불가능": []}

        date_map[date_val][status].append(member)

        if status == "가능":
            key = (date_val, time_val)
            if key not in time_map:
                time_map[key] = []
            time_map[key].append(member)

    except:
        pass


# =========================
# 이벤트 생성
# =========================
events = []
TOTAL_MEMBERS = 8

for date_val, data in date_map.items():

    possible_count = len(data["가능"])
    impossible_count = len(data["불가능"])

    # ❌ 불가능 1명이라도 → 빨강
    if impossible_count > 0:
        events.append({
            "start": date_val,
            "display": "background",
            "color": "#ff4d4d"
        })

    # 🟢 전원 가능
    elif possible_count == TOTAL_MEMBERS:
        events.append({
            "start": date_val,
            "display": "background",
            "color": "#00ff99"
        })

    # 인원 수 표시
    if possible_count > 0:
        events.append({
            "title": f"{possible_count}명",
            "start": date_val,
        })


# =========================
# 🔥 시간 겹침 (전원)
# =========================
for (date_val, time_val), members in time_map.items():
    if len(members) == TOTAL_MEMBERS:
        events.append({
            "start": date_val,
            "display": "background",
            "color": "#FFD700"
        })


# =========================
# 공대원 개별 표시
# =========================
for row in rows:
    try:
        date_val = row[0]
        time_val = row[1]
        member = row[2]
        status = row[3]

        if status == "가능":
            events.append({
                "title": member,
                "start": f"{date_val}T{time_val}",
                "color": member_colors.get(member, "#888")
            })

    except:
        pass


# =========================
# 🔥 선택 날짜 (✔ 무조건 표시)
# =========================
for d in st.session_state.selected_dates:
    events.append({
        "title": "✔",
        "start": d,
        "allDay": True,
        "color": "#00cc66",
        "textColor": "#ffffff",
        "classNames": ["blink"]
    })


# =========================
# 달력
# =========================
calendar_data = calendar(
    events=events,
    options={
        "initialView": "dayGridMonth",
        "locale": "ko",
        "height": 850,
    },
)


# =========================
# 클릭 → 토글
# =========================
if calendar_data.get("dateClick"):
    clicked = calendar_data["dateClick"]["date"]

    if clicked in st.session_state.selected_dates:
        st.session_state.selected_dates.remove(clicked)
    else:
        st.session_state.selected_dates.append(clicked)


# =========================
# 입력
# =========================
members = list(member_colors.keys())

with st.sidebar:
    st.header("일정 입력")

    member = st.selectbox("공대원", members)
    time = st.time_input("시간")

    is_impossible = st.checkbox("❌ 불가능")

    if st.button("저장"):

        if not st.session_state.selected_dates:
            st.warning("날짜 선택 먼저")
        else:
            status = "불가능" if is_impossible else "가능"
            rows = schedule_ws.get_all_values()

            for d in st.session_state.selected_dates:

                delete_index = []

                for idx, row in enumerate(rows):
                    if row[0] == d and row[2] == member:
                        delete_index.append(idx + 1)

                for i in reversed(delete_index):
                    schedule_ws.delete_rows(i)

                schedule_ws.append_row([
                    d,
                    time.strftime("%H:%M:%S"),
                    member,
                    status
                ])

            st.success("저장 완료")
            st.session_state.selected_dates = []
