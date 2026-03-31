import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from streamlit_calendar import calendar

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

    client = gspread.authorize(creds)
    return client


client = connect()

# ✅ 원래 잘 되던 방식으로 복구
sheet = client.open("AION2 RAID")

# ✅ 시트 탭 이름 확인
schedule_ws = sheet.worksheet("시트1")


# =========================
# 기본 UI
# =========================
st.title("AION2 레이드 일정 관리")

today = datetime.date.today()
st.write(f"📅 오늘 날짜: {today}")


# =========================
# 사이드바 입력
# =========================
members = ["탱커", "힐러", "딜러1", "딜러2", "딜러3"]

with st.sidebar:
    st.header("일정 입력")

    date = st.date_input("날짜 선택", value=today)
    time = st.time_input("시간 선택")
    member = st.selectbox("공대원 선택", members)

    is_impossible = st.checkbox("❌ 이 날 불가능")

    if st.button("저장"):
        status = "불가능" if is_impossible else "가능"

        schedule_ws.append_row([
            str(date),
            str(time),
            member,
            status
        ])

        st.success("저장 완료!")


# =========================
# 시트 데이터 → 달력 이벤트 변환
# =========================
rows = schedule_ws.get_all_values()

events = []

for row in rows:
    try:
        date_val = row[0]
        time_val = row[1]
        member_val = row[2]
        status_val = row[3]

        title = member_val

        if status_val == "불가능":
            title = f"❌ {member_val}"

        events.append({
            "title": title,
            "start": f"{date_val}T{time_val}",
        })

    except:
        pass


# =========================
# 🔥 가로 2달 달력
# =========================
st.subheader("📆 일정 달력")

calendar_options = {
    "initialView": "multiMonthYear",
    "locale": "ko",
    "height": 500,
    "fixedWeekCount": False,
    "views": {
        "multiMonthYear": {
            "type": "multiMonth",
            "duration": {"months": 2},
            "multiMonthMaxColumns": 2
        }
    }
}

state = calendar(events=events, options=calendar_options)


# =========================
# 날짜 클릭 시 상세 표시
# =========================
if state.get("dateClick"):
    clicked_date = state["dateClick"]["date"]

    st.subheader(f"📅 {clicked_date} 일정")

    found = False

    for row in rows:
        try:
            if row[0] == clicked_date:
                found = True
                if row[3] == "불가능":
                    st.write(f"❌ {row[2]} / {row[1]}")
                else:
                    st.write(f"✅ {row[2]} / {row[1]}")
        except:
            pass

    if not found:
        st.write("일정 없음")


# =========================
# 전체 일정 리스트
# =========================
st.subheader("📋 전체 일정")

if rows:
    for row in rows:
        try:
            if row[3] == "불가능":
                st.write(f"❌ {row[0]} / {row[1]} - {row[2]}")
            else:
                st.write(f"✅ {row[0]} / {row[1]} - {row[2]}")
        except:
            pass
else:
    st.write("등록된 일정 없음")
