import streamlit as st
import datetime
import calendar

# --- 1. 페이지 설정 및 강제 정렬 CSS ---
st.set_page_config(page_title="AION2 Raid Master", layout="centered")

st.markdown("""
    <style>
    /* 배경 및 기본 폰트 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* [핵심] 달력 전체 컨테이너: 요일과 날짜를 하나의 그리드로 통합 */
    .calendar-board {
        display: grid;
        grid-template-columns: repeat(7, 1fr); /* 무조건 7열 고정 */
        width: 100%;
        max-width: 800px;
        margin: 20px auto;
        border: 1px solid #262730;
        background-color: #161920;
    }

    /* 요일 및 날짜 공통 박스 설정 */
    .cal-box {
        aspect-ratio: 1 / 1; /* 완벽한 정사각형 유지 */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 0.5px solid #262730;
        font-size: 1.1rem;
    }

    /* 요일 헤더 전용 */
    .header-box {
        background-color: #1A1D24;
        height: 60px; /* 요일칸은 조금 슬림하게 */
        aspect-ratio: auto; 
        color: #888;
        font-weight: 900;
        font-size: 0.8rem;
    }

    /* 날짜 숫자 */
    .day-num { font-weight: 700; margin-bottom: 5px; }

    /* 데이터(인원) 표시: 네온 블루 */
    .member-cnt {
        color: #00FBFF;
        font-size: 0.9rem;
        font-weight: 900;
        text-shadow: 0 0 8px rgba(0, 251, 255, 0.4);
    }

    /* 오늘/선택된 날짜: AION2 레드 */
    .highlight-box {
        background-color: #2D1A1E !important;
        border: 2px solid #FF4B4B !important;
        color: #FF4B4B !important;
    }

    /* 사이드바 스타일링 */
    div[data-testid="stSidebar"] { background-color: #11141A; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 시뮬레이션 (공대장님 시트 데이터 연동 가능) ---
# 예시로 3월 25일 3명, 27일 1명을 표시합니다.
raid_data = {25: 3, 27: 1}

# --- 3. 사이드바 (깔끔한 입력창) ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>🛡️ AION2</h1>", unsafe_allow_html=True)
    st.write("---")
    st.date_input("날짜 선택", datetime.date(2026, 3, 25))
    st.selectbox("대원명", [f"유저{i}" for i in range(1, 9)])
    st.button("🚀 레이드 일정 등록")

# --- 4. 메인 달력 생성 ---
st.markdown("<h2 style='text-align:center;'>2026년 3월 현황</h2>", unsafe_allow_html=True)

# 그리드 시작
cal_html = '<div class="calendar-board">'

# 요일 헤더 추가
for day_name in ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]:
    color = "#FF4B4B" if day_name == "SUN" else "#888"
    cal_html += f'<div class="cal-box header-box" style="color:{color};">{day_name}</div>'

# 날짜 계산
cal_obj = calendar.Calendar(firstweekday=6)
month_days = cal_obj.monthdayscalendar(2026, 3)

for week in month_days:
    for day in week:
        if day == 0:
            cal_html += '<div class="cal-box"></div>' # 빈 칸
        else:
            # 스타일 결정
            box_class = "cal-box"
            if day == 25: box_class += " highlight-box"
            
            # 인원 표시
            member_info = f'<span class="member-cnt">👥 {raid_data[day]}</span>' if day in raid_data else ""
            
            cal_html += f'''
                <div class="{box_class}">
                    <span class="day-num">{day}</span>
                    {member_info}
                </div>
            '''

cal_html += '</div>' # 그리드 종료

# 화면에 출력
st.markdown(cal_html, unsafe_allow_html=True)
