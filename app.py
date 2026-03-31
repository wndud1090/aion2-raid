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
sheet = client.open("AION2 RAID")
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
# 데이터 → 이벤트 변환
# =========================
rows = schedule_ws.get_all_values()

events = []

for row in rows:
    try:
        title = row[2]
        if row[3] == "불가능":
            title = f"❌ {row[2]}"

        events.append({
            "title": title,
            "start": f"{row[0]}T{row[1]}",
        })
    except:
        pass


# =========================
# 🔥 가로 2달 강제 배치
# =========================
st.subheader("📆 일정 달력")

col1, col2 = st.columns(2)

# 이번달
with col1:
    st.markdown("### 이번달")

    cal1 = calendar(
        events=events,
        options={
            "initialView": "dayGridMonth",
            "initialDate": today.strftime("%Y-%m-01"),
            "locale": "ko",
            "height": 500,
        },
    )

# 다음달 계산
next_month = today.month + 1
next_year = today.year

if next_month == 13:
    next_month = 1
    next_year += 1

next_date = f"{next_year}-{str(next_month).zfill(2)}-01"

# 다음달
with col2:
    st.markdown("### 다음달")

    cal2 = calendar(
        events=events,
        options={
            "initialView": "dayGridMonth",
            "initialDate": next_date,
            "locale": "ko",
            "height": 500,
        },
    )


# =========================
# 클릭 처리 (두 달 모두 대응)
# =========================
clicked_date = None

if cal1.get("dateClick"):
    clicked_date = cal1["dateClick"]["date"]

if cal2.get("dateClick"):
    clicked_date = cal2["dateClick"]["date"]

if clicked_date:
    st.subheader(f"📅 {clicked_date} 일정")

    found = False

    for row in rows:
        if row[0] == clicked_date:
            found = True
            if row[3] == "불가능":
                st.write(f"❌ {row[2]} / {row[1]}")
            else:
                st.write(f"✅ {row[2]} / {row[1]}")

    if not found:
        st.write("일정 없음")


# =========================
# 전체 리스트
# =========================
st.subheader("📋 전체 일정")

for row in rows:
    try:
        if row[3] == "불가능":
            st.write(f"❌ {row[0]} / {row[1]} - {row[2]}")
        else:
            st.write(f"✅ {row[0]} / {row[1]} - {row[2]}")
    except:
        pass
