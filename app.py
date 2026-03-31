import streamlit as st
import datetime
import calendar

st.set_page_config(layout="wide")

# =========================
# 상태
# =========================
if "selected_dates" not in st.session_state:
    st.session_state.selected_dates = []

if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.date.today().replace(day=1)


# =========================
# 더미 데이터 (나중에 구글시트 연결)
# =========================
date_status = {
    "2026-03-10": "불가능",
    "2026-03-12": "가능",
    "2026-03-15": "전원가능",
}


# =========================
# 날짜 포맷
# =========================
def format_date(y, m, d):
    return f"{y}-{m:02d}-{d:02d}"


# =========================
# 달력 생성 함수
# =========================
def render_month(year, month):

    cal = calendar.monthcalendar(year, month)

    st.markdown(f"### {year}년 {month}월")

    for week in cal:
        cols = st.columns(7)

        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
                continue

            date_str = format_date(year, month, day)

            # 상태
            is_selected = date_str in st.session_state.selected_dates
            status = date_status.get(date_str, "")

            # 색상
            color = "#ffffff"

            if status == "불가능":
                color = "#ff4d4d"
            elif status == "전원가능":
                color = "#FFD700"
            elif is_selected:
                color = "#00cc66"

            label = str(day)

            if is_selected:
                label = f"✔ {day}"

            # 버튼
            if cols[i].button(
                label,
                key=date_str,
                use_container_width=True
            ):
                if is_selected:
                    st.session_state.selected_dates.remove(date_str)
                else:
                    st.session_state.selected_dates.append(date_str)

            # 색상 적용
            cols[i].markdown(
                f"""
                <div style="
                    background:{color};
                    text-align:center;
                    padding:8px;
                    border-radius:8px;
                    margin-top:-38px;
                "></div>
                """,
                unsafe_allow_html=True
            )


# =========================
# 상단 컨트롤
# =========================
col1, col2, col3 = st.columns([1,2,1])

with col1:
    if st.button("◀ 이전"):
        prev = st.session_state.current_date - datetime.timedelta(days=1)
        st.session_state.current_date = prev.replace(day=1)

with col3:
    if st.button("다음 ▶"):
        next_m = st.session_state.current_date + datetime.timedelta(days=32)
        st.session_state.current_date = next_m.replace(day=1)


# =========================
# 두 달 표시
# =========================
base = st.session_state.current_date

next_month = (base + datetime.timedelta(days=32)).replace(day=1)

c1, c2 = st.columns(2)

with c1:
    render_month(base.year, base.month)

with c2:
    render_month(next_month.year, next_month.month)


# =========================
# 선택 결과
# =========================
st.markdown("### 선택된 날짜")

st.write(st.session_state.selected_dates)
