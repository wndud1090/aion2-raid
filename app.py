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

    date_range = st.date_input(
        "📅 날짜 범위 선택",
        value=(today, today),
        format="YYYY년 MM월 DD일"
    )

    time = st.time_input("시간 선택")
    member = st.selectbox("공대원 선택", members)

    is_impossible = st.checkbox("❌ 이 날 불가능")

    if st.button("저장"):

        start_date, end_date = date_range
        delta = (end_date - start_date).days

        status = "불가능" if is_impossible else "가능"

        # 🔥 기존 데이터 가져오기
        rows = schedule_ws.get_all_values()

        for i in range(delta + 1):
            d = start_date + datetime.timedelta(days=i)
            d_str = str(d)

            # 🔥 덮어쓰기: 기존 행 삭제
            delete_index = []

            for idx, row in enumerate(rows):
                try:
                    if row[0] == d_str and row[2] == member:
                        delete_index.append(idx + 1)  # gspread는 1부터 시작
                except:
                    pass

            # 뒤에서부터 삭제 (인덱스 밀림 방지)
            for index in reversed(delete_index):
                schedule_ws.delete_rows(index)

            # 🔥 새로 추가
            schedule_ws.append_row([
                d_str,
                str(time),
                member,
                status
            ])

        st.success("덮어쓰기 저장 완료!")


# =========================
# 데이터 → 이벤트 변환
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
# 달력 (가로 2달)
# =========================
st.subheader("📆 일정 달력")

col1, col2 = st.columns(2)

with col1:
    cal1 = calendar(
        events=events,
        options={
            "initialView": "dayGridMonth",
            "initialDate": today.strftime("%Y-%m-01"),
            "locale": "ko",
            "height": 800,
        },
    )

next_month = today.month + 1
next_year = today.year

if next_month == 13:
    next_month = 1
    next_year += 1

next_date = f"{next_year}-{str(next_month).zfill(2)}-01"

with col2:
    cal2 = calendar(
        events=events,
        options={
            "initialView": "dayGridMonth",
            "initialDate": next_date,
            "locale": "ko",
            "height": 800,
        },
    )


# =========================
# 날짜 클릭 상세
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
