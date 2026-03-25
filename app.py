import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# ---------------------------
# [1] 기본 설정
# ---------------------------
st.set_page_config(layout="wide")

# ---------------------------
# [2] (유지) 시트 데이터 로드
# 👉 기존 함수 그대로 사용하세요
# ---------------------------
@st.cache_data
def load_data():
    # ❗ 기존 구글시트 코드 그대로 넣으세요
    # 예시 형태만 유지
    df = pd.DataFrame(columns=["date", "count", "type"])
    return df

df = load_data()

# ---------------------------
# [3] 상태값
# ---------------------------
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

today = datetime.today().date()

# ---------------------------
# [4] 스타일 (핵심)
# ---------------------------
st.markdown("""
<style>

.card-wrap {
    position: relative;
    height: 90px;
}

.day-card {
    position: absolute;
    width: 100%;
    height: 100%;
    background: #1A1D24;
    border: 1px solid #36393E;
    border-radius: 12px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: 0.2s;
}

.card-wrap:hover .day-card {
    transform: scale(1.05);
    border: 1px solid #888;
}

.day-num {
    font-size: 15px;
    font-weight: bold;
}

.day-info {
    font-size: 11px;
}

/* 상태 */
.today { border: 2px solid #00E5FF !important; }
.selected { border: 2px solid #FFD700 !important; background: #2A2E39; }

.low { opacity: 0.5; }
.mid { border: 1px solid #4B8BFF; }
.high { border: 1px solid #FFD700; }

.raid {
    background: linear-gradient(135deg, #443714 0%, #1A1D24 100%);
    color: #FFD700;
    font-weight: bold;
}

/* 🔥 핵심: 버튼을 카드 위에 덮음 */
.card-wrap button {
    position: absolute !important;
    top: 0;
    left: 0;
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important;
    z-index: 10;
    margin: 0 !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------
# [5] 달력 렌더링
# ---------------------------
def draw_calendar(year, month, df):

    st.markdown(f"<h3 style='text-align:center;color:#FFD700'>{year}년 {month}월</h3>", unsafe_allow_html=True)

    headers = ["일","월","화","수","목","금","토"]
    cols = st.columns(7)

    for i, h in enumerate(headers):
        color = "#FF5A5A" if i == 0 else "#4DA3FF" if i == 6 else "#AAA"
        cols[i].markdown(f"<div style='text-align:center;color:{color}'>{h}</div>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(year, month)

    for week in cal:
        cols = st.columns(7)

        for i, day in enumerate(week):

            if day == 0:
                cols[i].markdown("")
                continue

            date_str = f"{year}-{month:02d}-{day:02d}"
            current_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # -------------------
            # 데이터 처리 (유지)
            # -------------------
            row = df[df["date"] == date_str]

            count = 0
            event_type = ""

            if not row.empty:
                count = int(row.iloc[0]["count"])
                event_type = str(row.iloc[0]["type"])

            # -------------------
            # 스타일 결정
            # -------------------
            classes = []

            if current_date == today:
                classes.append("today")

            if st.session_state.selected_date == date_str:
                classes.append("selected")

            if count >= 10:
                classes.append("high")
            elif count >= 5:
                classes.append("mid")
            elif count > 0:
                classes.append("low")

            if event_type == "RAID":
                classes.append("raid")

            class_str = " ".join(classes)

            # -------------------
            # UI + 버튼 통합
            # -------------------
            with cols[i]:
                st.markdown(f"""
                <div class="card-wrap">
                    <div class="day-card {class_str}">
                        <div class="day-num">{day}</div>
                        <div class="day-info">
                            👥 {count}<br>
                            🏆 {event_type}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if st.button("", key=f"btn_{date_str}"):
                    st.session_state.selected_date = date_str

                st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# [6] 실행
# ---------------------------
now = datetime.now()
draw_calendar(now.year, now.month, df)
