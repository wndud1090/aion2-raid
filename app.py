import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 디자인 (CSS) ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

# 커스텀 스타일 시트
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 70px;
        border: 1px solid #3e3e3e;
        background-color: #1e1e1e;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        border-color: #FF4B4B;
        transform: translateY(-2px);
    }
    .date-card {
        text-align: center;
        padding: 10px;
        border-radius: 10px;
        background-color: #262730;
    }
    .full-party { border: 2px solid #FFD700 !important; color: #FFD700 !important; }
    .recruiting { border: 1px solid #00BFFF !important; }
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

@st.cache_data(ttl=60) # 1분마다 데이터 갱신
def load_data():
    client = get_gspread_client()
    try:
        sheet = client.open("AION2_Raid_Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except:
        return pd.DataFrame(), None

df, sheet = load_data()

# --- 3. 사이드바 (입력창) ---
with st.sidebar:
    st.image("https://img.danawa.com/new/no_image_600.gif", caption="AION 2 RAID SYSTEM") # 로고가 있다면 교체
    st.header("📝 참여 등록")
    fixed_year = 2026
    input_date = st.date_input("날짜", datetime.date(fixed_year, 3, 25))
    date_str = str(input_date)
    
    name = st.selectbox("대원명", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("접속 가능 시간", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정"):
        if sheet:
            all_v = sheet.get_all_values()
            for i, row in enumerate(all_v):
                if row[0] == date_str and row[1] == name:
                    sheet.delete_rows(i + 1)
            sheet.append_row([date_str, name, time_range[0], time_range[1]])
            st.success("저장되었습니다!")
            st.rerun()

# --- 4. 메인 달력 (Real Calendar UI) ---
st.title("🛡️ AION2 공격대 조율실")
cal_year, cal_month = input_date.year, input_date.month
st.subheader(f"📅 {cal_year}년 {cal_month}월")

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')
    cal = calendar.monthcalendar(cal_year, cal_month)
    
    # 요일 헤더
    days = ["일", "월", "화", "수", "목", "금", "토"]
    cols = st.columns(7)
    for i, d in enumerate(days):
        color = "#FF4B4B" if i == 0 else "#555555"
        cols[i].markdown(f"<p style='text-align:center; color:{color}; font-weight:bold;'>{d}</p>", unsafe_allow_html=True)

    # 달력 날짜 생성
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                t_date = datetime.date(cal_year, cal_month, day)
                cnt = summary[summary['날짜'] == t_date]['인원'].values[0] if not summary[summary['날짜'] == t_date].empty else 0
                
                # 인원에 따른 디자인 분기
                label = f"**{day}**\n\n"
                if cnt >= 8:
                    label += f"🔥 FULL"
                    btn_type = "primary"
                elif cnt > 0:
                    label += f"👤 {cnt}명"
                    btn_type = "secondary"
                else:
                    label += " "
                    btn_type = "secondary"

                if cols[i].button(label, key=f"d_{day}", help=f"{cnt}명 대기중"):
                    st.session_state.selected_date = t_date

# --- 5. 상세 타임라인 (Gantt Chart) ---
st.write("---")
sel_date = st.session_state.get('selected_date', input_date)
st.markdown(f"### 📊 {sel_date} 참여 타임라인")

day_df = df[df['날짜'] == sel_date].copy()

if not day_df.empty:
    # 차트 그리기
    def to_dt(h): return datetime.datetime(2026, 1, 1, min(int(h), 23), 59 if h==24 else 0)

    fig = px.timeline(
        day_df, 
        x_start=day_df['시작'].apply(to_dt),
        x_end=day_df['종료'].apply(to_dt),
        y="이름", color="이름", text="이름",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_layout(
        xaxis=dict(title="시간", tickformat="%H시", dtick=3600000, 
                   range=[datetime.datetime(2026, 1, 1, 0), datetime.datetime(2026, 1, 2, 0)]),
        yaxis=dict(title="", autorange="reversed"),
        showlegend=False, height=350, margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("선택한 날짜에 등록된 대원이 없습니다.")

st.caption(f"Last Sync: {datetime.datetime.now().strftime('%H:%M:%S')}")
