import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 프리미엄 CSS ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.markdown("""
    <style>
    /* 배경 및 기본 폰트 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 고정 격자 달력 스타일 (사진 피드백 반영) */
    .calendar-container {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        border: 1px solid #262730;
        background-color: #161920;
    }
    .calendar-cell {
        border: 1px solid #262730;
        min-height: 120px; /* 높이 고정 */
        padding: 10px;
        position: relative;
    }
    .date-header { font-size: 1.5rem; font-weight: bold; color: #E0E0E0; }
    .status-text { font-size: 0.9rem; margin-top: 10px; color: #888; }
    .full-party { background-color: #1e1e10 !important; border: 2px solid #FFD700 !important; }
    .selected-day { background-color: #262730 !important; border: 2px solid #FF4B4B !important; }
    
    /* 그래프 가독성 향상 */
    .plot-container { border-radius: 10px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 (인증 강화) ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gspread"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        # 세션이 끊기지 않도록 매번 새 클라이언트를 반환하거나 캐시를 조절합니다.
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"구글 인증 오류: {e}")
        st.stop()

@st.cache_data(ttl=10) # 짧은 TTL로 실시간성 확보 및 세션 유지
def load_data():
    client = get_gspread_client()
    try:
        # 시트 이름이 'AION2_Raid_Data'인지 확인 필수
        spreadsheet = client.open("AION2_Raid_Data")
        sheet = spreadsheet.sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except Exception as e:
        # 에러 발생 시 빈 데이터프레임 반환하여 앱 중단 방지
        return pd.DataFrame(), None

df, sheet = load_data()

# --- 3. 사이드바 (등록 섹션) ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>🛡️ AION2</h1>", unsafe_allow_html=True)
    st.write("---")
    
    # 2026년 기준 날짜 선택
    fixed_date = datetime.date(2026, 3, 25)
    selected_date = st.date_input("📅 레이드 날짜 선택", fixed_date)
    date_str = str(selected_date)
    
    name = st.selectbox("👤 대원 이름", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("⏰ 접속 가능 시간", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정 (시트 저장)"):
        # 버튼 클릭 시점에 새로 클라이언트를 호출하여 인증 만료 방지
        client = get_gspread_client()
        try:
            curr_sheet = client.open("AION2_Raid_Data").sheet1
            all_values = curr_sheet.get_all_values()
            
            # 기존 데이터 중복 삭제
            for i, row in enumerate(all_values):
                if len(row) >= 2 and row[0] == date_str and row[1] == name:
                    curr_sheet.delete_rows(i + 1)
            
            curr_sheet.append_row([date_str, name, time_range[0], time_range[1]])
            st.success(f"{name}님 일정 저장 완료!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"저장 중 에러 발생: {e}")

# --- 4. 메인 화면: 반듯한 격자형 달력 ---
st.title("🛡️ AION2 공격대 실시간 조율실")
cal_year, cal_month = selected_date.year, selected_date.month
st.subheader(f"🗓️ {cal_year}년 {cal_month}월 일정 현황")

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')
    cal = calendar.monthcalendar(cal_year, cal_month)
    
    # 요일 헤더
    days = ["일", "월", "화", "수", "목", "금", "토"]
    cols = st.columns(7)
    for i, d in enumerate(days):
        color = "#FF4B4B" if i == 0 else "#E0E0E0"
        cols[i].markdown(f"<p style='text-align:center; font-weight:bold; color:{color};'>{d}</p>", unsafe_allow_html=True)

    # 달력 격자 출력 (모든 칸 크기 고정)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div class='calendar-cell' style='opacity: 0.1;'></div>", unsafe_allow_html=True)
                else:
                    this_date = datetime.date(cal_year, cal_month, day)
                    cnt = summary[summary['날짜'] == this_date]['인원'].values[0] if not summary[summary['날짜'] == this_date].empty else 0
                    
                    # 스타일 클래스
                    box_class = "calendar-cell"
                    if cnt >= 8: box_class += " full-party"
                    if this_date == selected_date: box_class += " selected-day"
                    
                    status_html = f"<b style='color:#FFD700;'>🔥 FULL</b>" if cnt >= 8 else f"👥 {cnt}명" if cnt > 0 else ""
                    
                    st.markdown(f"""
                        <div class='{box_class}'>
                            <div class='date-header'>{day}</div>
                            <div class='status-text'>{status_html}</div>
                        </div>
                    """, unsafe_allow_html=True)

# --- 5. 상세 참여 타임라인 (대왕 폰트 버전) ---
st.write("---")
st.markdown(f"### 📊 {selected_date} 상세 타임라인")

day_df = df[df['날짜'] == selected_date].copy()

if not day_df.empty:
    def to_dt(h): return datetime.datetime(2026, 1, 1, min(int(h), 23), 59 if h==24 else 0)

    fig = px.timeline(
        day_df, 
        x_start=day_df['시작'].apply(to_dt),
        x_end=day_df['종료'].apply(to_dt),
        y="이름", color="이름",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_layout(
        xaxis=dict(
            title="", tickformat="%H시", dtick=3600000 * 2,
            tickfont=dict(size=15),
            range=[datetime.datetime(2026, 1, 1, 0), datetime.datetime(2026, 1, 2, 0)]
        ),
        yaxis=dict(
            title="", autorange="reversed",
            tickfont=dict(size=22, color="white", family="Arial Black") # 이름을 압도적으로 크게 설정
        ),
        showlegend=False, height=450, margin=dict(l=10, r=10, t=10, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    if len(day_df) >= 8:
        st.success("🔥 8인 풀파티 매칭 완료! 세로로 막대가 8개 겹치는 시간에 출발하세요.")
else:
    st.info("선택한 날짜에 등록된 대원이 없습니다. 사이드바에서 일정을 추가해 보세요.")
