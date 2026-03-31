import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar

# =========================
# 구글 시트 연결 (secrets 사용)
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

# 🔥 여기 본인 시트 이름으로 수정 필요
sheet = client.open("AION2 RAID")
schedule_ws = sheet.worksheet("시트1")


# =========================
# 기본 UI
# =========================
st.title("AION2 레이드 일정 관리")

# ✅ 2. 오늘 날짜 표시
today = datetime.date.today()
st.write(f"📅 오늘 날짜: {today}")


# =========================
# ✅ 1 + 4 사이드바 UI
# =========================
members = ["탱커", "힐러", "딜러1", "딜러2", "딜러3"]

with st.sidebar:
    st.header("일정 입력")

    date = st.date_input("날짜 선택", value=today)
    time = st.time_input("시간 선택")
    member = st.selectbox("공대원 선택", members)

    # ✅ 4. 불가능 체크
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
# ✅ 3. 달력 (이번달 + 다음달)
# =========================
st.subheader("📆 일정 달력")

col1, col2 = st.columns(2)

# 이번달
with col1:
    st.markdown("### 이번달")
    cal1 = calendar.month(today.year, today.month)
    st.text(cal1)

# 다음달 계산
next_month = today.month + 1
next_year = today.year

if next_month == 13:
    next_month = 1
    next_year += 1

with col2:
    st.markdown("### 다음달")
    cal2 = calendar.month(next_year, next_month)
    st.text(cal2)


# =========================
# 일정 출력
# =========================
st.subheader("📋 전체 일정")

rows = schedule_ws.get_all_values()

if rows:
    for row in rows:
        try:
            date_val = row[0]
            time_val = row[1]
            member_val = row[2]
            status_val = row[3]

            if status_val == "불가능":
                st.write(f"❌ {date_val} / {time_val} - {member_val}")
            else:
                st.write(f"✅ {date_val} / {time_val} - {member_val}")

        except:
            pass
else:
    st.write("등록된 일정 없음")
