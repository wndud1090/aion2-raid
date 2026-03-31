import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from streamlit_calendar import calendar

st.set_page_config(layout="wide")

# =========================
# 구글 시트 연결
# =========================
@st.cache_resource
def connect():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_dict = st.secrets["gcp_service_account"]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, scope
    )

    return gspread.authorize(creds)


client = connect()
sheet = client.open("AION2 RAID")
schedule_ws = sheet.worksheet("시트1")


# =========================
# 상태 (선택 날짜)
# =========================
if "selected_dates" not in st.session_state:
    st.session_state.selected_dates = []


# =========================
# 기본 UI
# =========================
st.title("AION2 레이드 일정 관리")

today = datetime.date.today()
st.write(f"📅 오늘 날짜: {today}")


# =========================
# 데이터 불러오기
# =========================
rows = schedule_ws.get_all_values()


# =========================
# 이벤트 생성 (핵심)
# =========================
events = []
date_map = {}

for row in rows:
    try:
        date_val = row[0]
        time_val = row[1]
        member_val = row[2]
        status_val = row[3]

        if date_val not in date_map:
            date_map[date_val] = {
                "가능": [],
                "불가능": []
            }

        date_map[date_val][status_val].append(member_val)

    except:
        pass


TOTAL_MEMBERS = 8  # 필요시 수정

for date_val, data in date_map.items():

    possible_count = len(data["가능"])
    impossible_count = len(data["불가능"])

    # 🔥 인원 표시
    if possible_count > 0:
        events.append({
            "title": f"{possible_count}명",
            "start": date_val,
        })

    # 🔥 ❗ 핵심: 1명이라도 불가능 → 무조건 빨강
    if impossible_count > 0:
        events.append({
            "start": date_val,
            "display": "background",
            "color": "#ff4d4d"
        })

    # 🔥 전원 가능 → 초록 강조
    elif possible_count == TOTAL_MEMBERS:
        events.append({
            "start": date_val,
            "display": "background",
            "color": "#00ff99"
        })


# =========================
# 달력 + 선택 기능
# =========================
st.subheader("📆 날짜 선택")

calendar_data = calendar(
    events=events,
    options={
        "initialView": "dayGridMonth",
        "locale": "ko",
        "height": 800,
    },
)

# 클릭 → 토글 선택
if calendar_data.get("dateClick"):
    clicked = calendar_data["dateClick"]["date"]

    if clicked in st.session_state.selected_dates:
        st.session_state.selected_dates.remove(clicked)
    else:
        st.session_state.selected_dates.append(clicked)


# 선택 표시
st.write("### 선택된 날짜")
st.write(st.session_state.selected_dates)


# =========================
# 사이드바 입력
# =========================
members = ["탱커", "힐러", "딜러1", "딜러2", "딜러3", "딜러4", "딜러5", "딜러6"]

with st.sidebar:
    st.header("일정 입력")

    member = st.selectbox("공대원 선택", members)
    time = st.time_input("시간 선택")

    is_impossible = st.checkbox("❌ 이 날 불가능")

    if st.button("저장"):

        if not st.session_state.selected_dates:
            st.warning("날짜 먼저 선택하세요")
        else:
            status = "불가능" if is_impossible else "가능"

            rows = schedule_ws.get_all_values()

            for d_str in st.session_state.selected_dates:

                delete_index = []

                for idx, row in enumerate(rows):
                    try:
                        if row[0] == d_str and row[2] == member:
                            delete_index.append(idx + 1)
                    except:
                        pass

                for index in reversed(delete_index):
                    schedule_ws.delete_rows(index)

                # 🔥 시간 포맷 FIX
                schedule_ws.append_row([
                    d_str,
                    time.strftime("%H:%M:%S"),
                    member,
                    status
                ])

            st.success("저장 완료!")
            st.session_state.selected_dates = []


# =========================
# 상세 보기
# =========================
if calendar_data.get("dateClick"):
    clicked = calendar_data["dateClick"]["date"]

    st.subheader(f"📅 {clicked} 상세")

    for row in rows:
        if row[0] == clicked:
            if row[3] == "불가능":
                st.write(f"❌ {row[2]} / {row[1]}")
            else:
                st.write(f"✅ {row[2]} / {row[1]}")
