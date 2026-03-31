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
# Google Sheets 연결 (🔥 핵심 수정)
# ---------------------------
@st.cache_resource
def connect():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["gcp_service_account"]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, scope
    )

    return gspread.authorize(creds)

client = connect()

# 🔴 여기 이름 확인
sheet = client.open("AION2_RAID")

schedule_ws = sheet.worksheet("Sheet1")
members_ws = sheet.worksheet("Sheet2")

# ---------------------------
# 데이터 로드
# ---------------------------
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
# UI
# ---------------------------
st.title("🎮 AION2 레이드 일정")

name = st.selectbox("공대원", members_df["name"])
dates = st.date_input("날짜 (다중 선택)", [])

start = st.slider("시작",0,47,18)
end = st.slider("종료",0,47,24)

if st.button("저장"):
    save(name, dates, start, end)
    st.success("저장 완료")
    st.rerun()

# ---------------------------
# 캘린더
# ---------------------------
today = datetime.date.today()
year, month = today.year, today.month
cal = calendar.monthcalendar(year, month)

st.subheader(f"{year}년 {month}월")

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

                st.markdown(
                    f"### {day} {'🏆' if success else ''}"
                )
