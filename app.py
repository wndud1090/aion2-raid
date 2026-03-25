import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 고강도 디자인 (CSS) ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

# 프리미엄 디자인을 위한 커스텀 CSS
st.markdown("""
    <style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 달력 격자 고정 (핵심) */
    .stHorizontalBlock { gap: 0rem; }
    div[data-testid="stColumn"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* 날짜 버튼 스타일 (크기 고정) */
    .stButton>button {
        width: 100%;
        aspect-ratio: 1 / 1; /* 정사각형 유지 */
        border-radius: 0px; /* 각진 프리미엄 디자인 */
        border: 1px solid #262730;
        background-color: #161920;
        transition: all 0.2s;
        margin: 0 !important;
        padding: 0 !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    /* 빈 칸도 크기 고정 */
    .empty-date {
        width: 100%;
        aspect-ratio: 1 / 1;
        background-color: #0E1117;
        border: 1px solid #161920;
    }

    /* 버튼 호버 및 선택 효과 */
    .stButton>button:hover {
        background-color: #262730;
        border-color: #FF4B4B;
    }
    .stButton>button:focus:not(:active) {
        border-color: #FF4B4B;
        box-shadow: none;
    }
    
    /* 황금색 풀파티 강조 */
    .full-party button { border: 2px solid #FFD700 !important; color: #FFD700 !important; }
    
    /* 날짜 숫자 크기 */
    .date-num { font-size: 1.5rem; font-weight: bold; margin-bottom: 0.2rem; }
    .date-count { font-size: 0.8rem; color: #888; }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { background-color: #161920; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 (기존과 동일) ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gspread"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"설정 오류: {e}")
        st.stop()

@st.cache_data(ttl=60)
def load_data():
    client = get_gspread_client()
    try:
        # 시트 이름을 실제 이름과 확인하세요.
        sheet = client.open("AION2_Raid_Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except:
        return pd.DataFrame(), None

df, sheet = load_data()

# --- 3. 사이드바 (입력창, 디자인 수정) ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#FF4B4B;'>🛡️ AION2</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center; color:#E0E0E0; margin-bottom:2rem;'>참여 등록</h4>", unsafe_allow_html=True)
    
    fixed_year = 2026
    input_date = st.date_input("날짜", datetime.date(fixed_year, 3, 25))
    date_str = str(input_date)
    
    name = st.selectbox("대원명", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("접속 가능 시간", options=list(range(25)), value=(20, 23))
    
    st.write("")
    if st.button("🚀 일정 확정"):
        if sheet:
            all_v = sheet.get_all_values()
            for i, row in enumerate(all_v):
                if row[0] == date_str and row[1] == name:
                    sheet.delete_rows(i + 1)
            sheet.append_row([date_str, name, time_range[0], time_range[1]])
            st.success("저장되었습니다!")
            st.cache_data.clear() # 캐시 초기화
            st.rerun()

# --- 4. 메인 달력 (진짜 격자형 UI) ---
st.markdown("<h1 style='text-align:center; color:#E0E0E0;'>AION2 공격대 조율실</h1>", unsafe_allow_html=True)
cal_year, cal_month = input_date.year, input_date.month
st.markdown(f"<h3 style='text-align:center; color:#888;'>{cal_year}년 {cal_month}월</h3>", unsafe_allow_html=True)
st.write("")

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')
    cal = calendar.monthcalendar(cal_year, cal_month)
    
    # 요일 헤더
    days = ["일", "월", "화", "수", "목", "금", "토"]
    cols = st.columns(7)
    for i, d in enumerate(days):
        color = "#FF4B4B" if i == 0 else "#E0E0E0"
        cols[i].markdown(f"<p style='text-align:center; color:{color}; font-weight:bold; margin-bottom:0.5rem;'>{d}</p>", unsafe_allow_html=True)

    # 달력 격자 생성 (0인 칸도 크기 고정)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                # 빈 날짜 칸 디자인
                cols[i].markdown("<div class='empty-date'></div>", unsafe_allow_html=True)
            else:
                t_date = datetime.date(cal_year, cal_month, day)
                cnt = summary[summary['날짜'] == t_date]['인원'].values[0] if not summary[summary['날짜'] == t_date].empty else 0
                
                # 버튼 라벨 (HTML로 크기 조절)
                label_html = f"<div class='date-num'>{day}</div>"
                if cnt > 0:
                    label_html += f"<div class='date-count'>👥 {cnt}명</div>"
                else:
                    label_html += "<div class='date-count'>&nbsp;</div>" # 높이 유지용

                # 풀파티 시 클래스 추가
                btn_class = "full-party" if cnt >= 8 else ""
                
                with cols[i]:
                    st.markdown(f"<div class='{btn_class}'>", unsafe_allow_html=True)
                    if st.button(label_html, key=f"d_{day}", help=f"{cnt}명 대기중", unsafe_allow_html=True):
                        st.session_state.selected_date = t_date
                    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 상세 타임라인 (고해상도, 빅폰트 UI) ---
st.write("---")
sel_date = st.session_state.get('selected_date', input_date)
st.markdown(f"### 📊 {sel_date} 참여 타임라인")

day_df = df[df['날짜'] == sel_date].copy()

if not day_df.empty:
    # Plotly 데이터 전처리 (시간을 2026-01-01 기준으로 가상화)
    def to_dt(h): return datetime.datetime(2026, 1, 1, min(int(h), 23), 59 if h==24 else 0)

    # 타임라인 차트 생성
    fig = px.timeline(
        day_df, 
        x_start=day_df['시작'].apply(to_dt),
        x_end=day_df['종료'].apply(to_dt),
        y="이름", color="이름",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    # 그래프 레이아웃 대폭 수정 (가독성 핵심)
    fig.update_layout(
        # X축(시간) 설정: 눈금 크고 촘촘하게
        xaxis=dict(
            title="", 
            tickformat="%H시", 
            dtick=3600000 * 2, # 2시간 간격
            tickfont=dict(size=14, color="#E0E0E0"),
            range=[datetime.datetime(2026, 1, 1, 0), datetime.datetime(2026, 1, 2, 0)],
            gridcolor="#262730"
        ),
        # Y축(이름) 설정: 이름 크기를 대폭 키움
        yaxis=dict(
            title="", 
            autorange="reversed",
            tickfont=dict(size=18, font_properties={'weight': 'bold'}, color="#E0E0E0"), # 이름 폰트 크게!
            gridcolor="#262730"
        ),
        showlegend=False, 
        height=400, # 그래프 높이 고정
        margin=dict(l=0, r=10, t=10, b=0), # 여백 최소화
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117"
    )
    
    # 바(Bar) 위에 이름 텍스트 제거 (Y축으로 뺐으므로)
    fig.update_traces(texttemplate="") 
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # 인원수 체크
    if len(day_df) >= 8:
        st.balloons()
        st.success("🔥 8인 풀파티 매칭 완료!")
else:
    st.info("선택한 날짜에 등록된 대원이 없습니다.")

st.caption(f"Last Sync: {datetime.datetime.now().strftime('%H:%M:%S')}")
