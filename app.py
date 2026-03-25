import streamlit as st
import datetime
import pandas as pd

# 페이지 설정 (넓게 보기)
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.title("⚔️ AION2 8인 레이드 실시간 조율 대시보드")

# --- 왼쪽: 입력 섹션 ---
with st.sidebar:
    st.header("📝 일정 등록/수정")
    # 1. 날짜 선택 (달력 UI)
    input_date = st.date_input("날짜를 선택하세요", datetime.date.today())
    
    # 2. 이름 선택 (8명 고정)
    members = ["유저1", "유저2", "유저3", "유저4", "유저5", "유저6", "유저7", "유저8"]
    name = st.selectbox("본인 이름", members)
    
    # 3. 시간대 선택 (슬라이더)
    time_range = st.select_slider(
        "가능 시간 (0-24)",
        options=list(range(25)),
        value=(20, 23)
    )
    
    if st.button("일정 확정하기"):
        # 여기에 구글 시트 저장 로직 추가 예정
        st.success(f"{name}님 {input_date} 일정 반영 완료!")

# --- 오른쪽: 실시간 현황 섹션 ---
st.header(f"📅 {input_date} 레이드 현황")

# (예시 데이터 - 나중에 DB 연동 시 자동으로 불러옴)
example_data = pd.DataFrame([
    {"이름": "유저1", "시작": 20, "종료": 23},
    {"이름": "유저2", "시작": 21, "종료": 24},
    {"이름": "유저3", "시작": 19, "종료": 22},
])

# 8명 매칭 로직 시각화 (막대 그래프)
if not example_data.empty:
    import plotly.express as px
    fig = px.timeline(example_data, x_start="시작", x_end="종료", y="이름", 
                      color_discrete_sequence=['#FFD700'])
    # 타임라인을 시간 숫자로 표시하기 위한 커스텀
    fig.update_layout(xaxis=dict(title="시간 (시)", tickvals=list(range(25))))
    st.plotly_chart(fig, use_container_width=True)

    # 💡 골든타임 계산 결과 표시
    st.info("🔥 현재 **21:00 ~ 22:00** 시간대에 가장 많은 인원이 모였습니다!")
else:
    st.warning("등록된 일정이 없습니다.")
