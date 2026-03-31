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
# 상태 저장 (선택 날짜들)
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

events = []

for row in rows:
    try:
        date_val = row[0]
        time_val = row[1]
        member_val = row[2]
        status_val = row[3]

        if status_val == "가능":
            events.append({
                "title": member_val,
                "start": f"{date_val}T{time_val}",
            })
        else:
            events.append({
                "start": date_val,
                "display": "background",
                "color": "#ff4d4d"
            })
    except:
        pass


# =========================
# 달력 (선택 기능 포함)
# =========================
st.subheader("📆 날짜 선택 (클릭해서 여러 개 선택 가능)")

calendar_data = calendar(
    events=events,
    options={
        "initialView": "dayGridMonth",
        "locale": "ko",
        "height": 800,
        "selectable": True,   # 🔥 중요
    },
)

# 날짜 클릭 → 추가
if calendar_data.get("dateClick"):
    clicked = calendar_data["dateClick"]["date"]

    if clicked not in st.session_state.selected_dates:
        st.session_state.selected_dates.append(clicked)


# =========================
# 선택된 날짜 표시
# =========================
st.write("### 선택된 날짜")

if st.session_state.selected_dates:
    st.write(st.session_state.selected_dates)
else:
    st.write("선택 없음")


# =========================
# 사이드바 입력
# =========================
members = ["탱커", "힐러", "딜러1", "딜러2", "딜러3"]

with st.sidebar:
    st.header("일정 입력")

    member = st.selectbox("공대원 선택", members)
    time = st.time_input("시간 선택")

    is_impossible = st.checkbox("❌ 이 날 불가능")

    if st.button("선택 날짜 저장"):

        if not st.session_state.selected_dates:
            st.warning("날짜 먼저 선택하세요")
        else:
            status = "불가능" if is_impossible else "가능"

            rows = schedule_ws.get_all_values()

            for d_str in st.session_state.selected_dates:

                # 🔥 덮어쓰기 (같은 공대원 + 날짜)
                delete_index = []

                for idx, row in enumerate(rows):
                    try:
                        if row[0] == d_str and row[2] == member:
                            delete_index.append(idx + 1)
                    except:
                        pass

                for index in reversed(delete_index):
                    schedule_ws.delete_rows(index)

                # 새로 추가
                schedule_ws.append_row([
                    d_str,
                    str(time),
                    member,
                    status
                ])

            st.success("저장 완료!")

            # 선택 초기화
            st.session_state.selected_dates = []


# =========================
# 전체 일정 리스트
# =========================
st.subheader("📋 전체 일정")

for row in schedule_ws.get_all_values():
    try:
        if row[3] == "불가능":
            st.write(f"❌ {row[0]} / {row[1]} - {row[2]}")
        else:
            st.write(f"✅ {row[0]} / {row[1]} - {row[2]}")
    except:
        pass
