import streamlit as st
import datetime
import calendar
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)

client = connect()
sheet = client.open("AION2 RAID")
ws = sheet.worksheet("시트1")


# =========================
# 상태
# =========================
if "selected_dates" not in st.session_state:
    st.session_state.selected_dates = []

if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.date.today().replace(day=1)


# =========================
# 공대원
# =========================
members = ["탱커","힐러","딜러1","딜러2","딜러3","딜러4","딜러5","딜러6"]
TOTAL = 8


# =========================
# 데이터 로드
# =========================
rows = ws.get_all_values()

date_map = {}
time_map = {}

for r in rows:
    try:
        d, t, m, s = r

        if d not in date_map:
            date_map[d] = {"가능": [], "불가능": []}

        date_map[d][s].append(m)

        if s == "가능":
            key = (d, t)
            if key not in time_map:
                time_map[key] = []
            time_map[key].append(m)

    except:
        pass


# =========================
# 날짜 포맷
# =========================
def fmt(y,m,d):
    return f"{y}-{m:02d}-{d:02d}"


# =========================
# 달력 렌더
# =========================
def render_month(year, month):

    cal = calendar.monthcalendar(year, month)
    st.markdown(f"## {year}년 {month}월")

    for week in cal:
        cols = st.columns(7)

        for i, day in enumerate(week):

            if day == 0:
                cols[i].markdown("<div style='height:110px'></div>", unsafe_allow_html=True)
                continue

            d = fmt(year, month, day)

            is_selected = d in st.session_state.selected_dates
            info = date_map.get(d, {"가능":[], "불가능":[]})

            possible = len(info["가능"])
            impossible = len(info["불가능"])

            # 기본 색
            bg = "#ffffff"

            # ❌ 불가능 1명이라도
            if impossible > 0:
                bg = "#ff4d4d"

            # 🟡 전원 같은 시간
            for (td, tt), mem in time_map.items():
                if td == d and len(mem) == TOTAL:
                    bg = "#FFD700"

            # 🟢 선택
            if is_selected:
                bg = "#00cc66"

            label = f"{day}"

            if is_selected:
                label = f"✔ {day}"

            if possible > 0:
                label += f"<br><small>{possible}명</small>"

            # 클릭
            if cols[i].button("", key=d):
                if is_selected:
                    st.session_state.selected_dates.remove(d)
                else:
                    st.session_state.selected_dates.append(d)

            # UI
            cols[i].markdown(
                f"""
                <div style="
                    background:{bg};
                    height:110px;
                    border-radius:12px;
                    text-align:center;
                    padding-top:15px;
                    margin-top:-85px;
                    font-size:20px;
                    font-weight:bold;
                ">
                    {label}
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================
# 월 이동
# =========================
c1,c2,c3 = st.columns([1,2,1])

with c1:
    if st.button("◀"):
        prev = st.session_state.current_date - datetime.timedelta(days=1)
        st.session_state.current_date = prev.replace(day=1)

with c3:
    if st.button("▶"):
        nxt = st.session_state.current_date + datetime.timedelta(days=32)
        st.session_state.current_date = nxt.replace(day=1)


# =========================
# 2개월 표시
# =========================
base = st.session_state.current_date
next_m = (base + datetime.timedelta(days=32)).replace(day=1)

col1, col2 = st.columns(2)

with col1:
    render_month(base.year, base.month)

with col2:
    render_month(next_m.year, next_m.month)


# =========================
# 입력 UI
# =========================
with st.sidebar:
    st.header("일정 입력")

    member = st.selectbox("공대원", members)
    time = st.time_input("시간")
    is_impossible = st.checkbox("불가능")

    if st.button("저장"):

        if not st.session_state.selected_dates:
            st.warning("날짜 선택 먼저")
        else:
            status = "불가능" if is_impossible else "가능"

            all_rows = ws.get_all_values()

            for d in st.session_state.selected_dates:

                # 기존 삭제 (덮어쓰기)
                delete_idx = []
                for idx, row in enumerate(all_rows):
                    if row[0] == d and row[2] == member:
                        delete_idx.append(idx+1)

                for i in reversed(delete_idx):
                    ws.delete_rows(i)

                # 추가
                ws.append_row([
                    d,
                    time.strftime("%H:%M:%S"),
                    member,
                    status
                ])

            st.success("저장 완료")
            st.session_state.selected_dates = []
