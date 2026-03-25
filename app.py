import streamlit as st

# --- 1. 화면 중앙 정렬 및 디자인 CSS ---
st.set_page_config(page_title="2026 March Calendar", layout="centered")

st.markdown("""
    <style>
    /* 배경 및 기본 폰트 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 달력 테이블 스타일 */
    .calendar-table {
        width: 100%;
        max-width: 700px;
        margin: 40px auto;
        border-collapse: collapse;
        table-layout: fixed; /* 칸 크기 강제 고정 */
        background-color: #161920;
        border: 1px solid #262730;
    }

    /* 요일 및 날짜 칸 */
    .calendar-table th, .calendar-table td {
        border: 1px solid #262730;
        text-align: center;
        vertical-align: middle;
        height: 100px; /* 정사각형에 가깝게 높이 고정 */
    }

    /* 요일 헤더 */
    .calendar-table th {
        background-color: #1A1D24;
        height: 50px;
        color: #888;
        font-size: 0.8rem;
        font-weight: 900;
    }

    /* 일요일 빨간색 */
    .sun { color: #FF4B4B !important; }

    /* 날짜 숫자 스타일 */
    .day-num {
        font-size: 1.3rem;
        font-weight: 600;
    }

    /* 25일 하이라이트 (공대장님 예시) */
    .today {
        background-color: #2D1A1E !important;
        border: 2px solid #FF4B4B !important;
        color: #FF4B4B !important;
    }
    
    .raid-info {
        font-size: 0.8rem;
        color: #00FBFF;
        font-weight: 900;
        display: block;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 2026년 3월 달력 구조 직접 생성 ---
# 2026년 3월은 일요일(1일)부터 시작합니다.
march_2026 = [
    [1, 2, 3, 4, 5, 6, 7],
    [8, 9, 10, 11, 12, 13, 14],
    [15, 16, 17, 18, 19, 20, 21],
    [22, 23, 24, 25, 26, 27, 28],
    [29, 30, 31, 0, 0, 0, 0] # 0은 빈칸
]

# --- 3. HTML 테이블 렌더링 ---
st.markdown("<h2 style='text-align:center;'>2026년 3월</h2>", unsafe_allow_html=True)

html = '<table class="calendar-table">'
# 요일 헤더
html += '<thead><tr>'
days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
for i, d in enumerate(days):
    sun_class = 'class="sun"' if i == 0 else ""
    html += f'<th {sun_class}>{d}</th>'
html += '</tr></thead><tbody>'

# 날짜 렌더링
for week in march_2026:
    html += '<tr>'
    for i, day in enumerate(week):
        sun_class = 'class="sun"' if i == 0 else ""
        if day == 0:
            html_content = ""
            td_class = ""
        else:
            td_class = 'class="today"' if day == 25 else ""
            raid_badge = '<span class="raid-info">👥 3명</span>' if day == 25 else ""
            html_content = f'<span class="day-num">{day}</span>{raid_badge}'
            
        html += f'<td {td_class} {sun_class if not td_class else ""}>{html_content}</td>'
    html += '</tr>'

html += '</tbody></table>'

st.markdown(html, unsafe_allow_html=True)
