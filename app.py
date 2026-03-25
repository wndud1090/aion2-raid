import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 고정 그리드 CSS ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 달력 격자 고정 */
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 5px;
        margin-bottom: 20px;
    }
    .cal-day {
        background-color: #161920;
        border: 1px solid #262730;
        height: 100px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
    }
    .today { border: 2px solid #FF4B4B !important; }
    .full { border: 2px solid #FFD700 !important; color: #FFD700; }
    
    /* 텍스트 크기 조절 */
    .d-num { font-size: 1.5rem; font-weight: bold; }
    .d-cnt { font-size: 0.9rem; color: #888; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gspread"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"설정 오류: {e}")
        st.stop()

@st.cache_data(ttl=30)
def load_data():
    client = get_gspread_client()
    try:
        sheet = client.open("AION2_Raid_Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except:
        return pd.DataFrame(), None

df, sheet = load_data()

# --- 3. 사이드바 (등록 섹션) ---
with st.sidebar:
    st.title("🛡️ AION2")
    fixed_year = 2026
    # 날짜 입력에서 발생할 수 있는 오류를 방지하기 위해 형식을 고정합니다.
    input_date = st.date_input("기준 날짜", datetime.date(fixed_year, 3, 25))
    date_str = str(input_date)
    
    name = st.selectbox("대원", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("시간(시)", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 등록/수정"):
        if sheet:
            all_v = sheet.get_all_values()
            for i, row in enumerate(all_v):
                if row[0] == date_str and row[1] == name:
                    sheet.delete_rows(i + 1)
            sheet.append_row([date_str, name, time_range[0], time_range[1]])
            st.success("저장 완료!")
            st.cache_data.clear()
            st.rerun()

# --- 4. 메인 섹션: 진짜 달력 UI ---
st.header(f"📅 {input_date.year}년 {input_date.month}월 레이드 현황")

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')
    cal = calendar.monthcalendar(input_date.year, input_date.month)

    # 요일 표시
    day_names = ["일", "월", "화", "수", "목", "금", "토"]
    h_cols = st.columns(7)
    for idx, name_t in enumerate(day_names):
        h_cols[idx].markdown(f"<p style='text-align:center; font-weight:bold;'>{name_t}</p>", unsafe_allow_html=True)

    # 격자형 달력 출력 (에러 방지를 위해 버튼 대신 클릭 선택 바 사용)
    for week in cal:
        w_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                w_cols[i].markdown("<div class='cal-day' style='opacity:0.2;'></div>", unsafe_allow_html=True)
            else:
                this_date = datetime.date(input_date.year, input_date.month, day)
                cnt = summary[summary['날짜'] == this_date]['인원'].values[0] if not summary[summary['날짜'] == this_date].empty else 0
                
                # 스타일 결정
                style_class = "cal-day"
                if cnt >= 8: style_class += " full"
                if this_date == input_date: style_class += " today"
                
                status_txt = f"🔥 FULL" if cnt >= 8 else f"👥 {cnt}명" if cnt > 0 else ""
                
                w_cols[i].markdown(f"""
                    <div class='{style_class}'>
                        <div class='d-num'>{day}</div>
                        <div class='d-cnt'>{status_txt}</div>
                    </div>
                """, unsafe_allow_html=True)

# --- 5. 가로 바 타임라인 (폰트 확대 버전) ---
st.write("---")
st.subheader(f"📊 {input_date} 상세 타임라인")

day_df = df[df['날짜'] == input_date].copy()

if not day_df.empty:
    # Plotly 그래프 가독성 수정
    def to_dt(h): return datetime.datetime(2026, 1, 1, min(int(h), 23), 59 if h==24 else 0)

    fig = px.timeline(
        day_df, 
        x_start=day_df['시작'].apply(to_dt),
        x_end=day_df['종료'].apply(to_dt),
        y="이름", color="이름",
        template="plotly_dark"
    )

    fig.update_layout(
        xaxis=dict(
            title="접속 시간", tickformat="%H시", dtick=3600000 * 2,
            tickfont=dict(size=16), # 시간 글씨 크게
            range=[datetime.datetime(2026, 1, 1, 0), datetime.datetime(2026, 1, 2, 0)]
        ),
        yaxis=dict(
            title="", autorange="reversed",
            tickfont=dict(size=20, color="white", family="Arial Black") # 대원 이름 아주 크게
        ),
        showlegend=False, height=450,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("이날은 아직 등록된 인원이 없습니다. 사이드바에서 일정을 등록해 주세요.")
