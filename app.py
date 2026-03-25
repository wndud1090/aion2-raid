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
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 달력 칸 디자인 */
    .cal-box {
        background-color: #161920;
        border: 1px solid #262730;
        border-radius: 5px;
        padding: 15px;
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: all 0.3s;
        cursor: pointer;
    }
    .cal-box:hover { border-color: #FF4B4B; background-color: #1e222b; }
    .selected-date { border: 2px solid #FF4B4B !important; background-color: #262730; }
    .full-party { border: 2px solid #FFD700 !important; }
    
    .date-num { font-size: 1.4rem; font-weight: bold; margin-bottom: 5px; }
    .date-status { font-size: 0.85rem; color: #888; }
    .full-text { color: #FFD700; font-weight: bold; }

    /* 사이드바 */
    [data-testid="stSidebar"] { background-color: #161920; border-right: 1px solid #262730; }
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

# --- 3. 사이드바 (등록창) ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>🛡️ AION2</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>레이드 일정 조율</p>", unsafe_allow_html=True)
    
    fixed_year = 2026
    input_date = st.date_input("날짜 선택", datetime.date(fixed_year, 3, 25))
    date_str = str(input_date)
    
    name = st.selectbox("대원 이름", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("접속 가능 시간(시)", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정"):
        if sheet:
            all_v = sheet.get_all_values()
            for i, row in enumerate(all_v):
                if row[0] == date_str and row[1] == name:
                    sheet.delete_rows(i + 1)
            sheet.append_row([date_str, name, time_range[0], time_range[1]])
            st.success("데이터가 시트에 저장되었습니다!")
            st.cache_data.clear()
            st.rerun()

# --- 4. 메인 달력 (정밀 격자 UI) ---
st.title("AION2 공격대 실시간 현황")
cal_year, cal_month = input_date.year, input_date.month
st.subheader(f"📅 {cal_year}년 {cal_month}월")

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')
    cal = calendar.monthcalendar(cal_year, cal_month)
    
    days = ["일", "월", "화", "수", "목", "금", "토"]
    cols = st.columns(7)
    for i, d in enumerate(days):
        color = "#FF4B4B" if i == 0 else "#E0E0E0"
        cols[i].markdown(f"<p style='text-align:center; color:{color}; font-weight:bold;'>{d}</p>", unsafe_allow_html=True)

    # 세션 상태 초기화
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = input_date

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("<div style='min-height:100px;'></div>", unsafe_allow_html=True)
            else:
                t_date = datetime.date(cal_year, cal_month, day)
                cnt = summary[summary['날짜'] == t_date]['인원'].values[0] if not summary[summary['날짜'] == t_date].empty else 0
                
                # CSS 클래스 조합
                box_class = "cal-box"
                if t_date == st.session_state.selected_date: box_class += " selected-date"
                if cnt >= 8: box_class += " full-party"
                
                status_html = f"<span class='full-text'>🔥 FULL</span>" if cnt >= 8 else f"👥 {cnt}명" if cnt > 0 else "&nbsp;"
                
                # 버튼 대신 클릭 가능한 카드 구현
                with cols[i]:
                    st.markdown(f"""
                        <div class='{box_class}'>
                            <div class='date-num'>{day}</div>
                            <div class='date-status'>{status_html}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    # 실제 선택을 위한 투명 버튼
                    if st.button(f"선택 {day}", key=f"btn_{day}", label_visibility="collapsed"):
                        st.session_state.selected_date = t_date
                        st.rerun()

# --- 5. 상세 타임라인 (고해상도 그래프) ---
st.write("---")
sel_date = st.session_state.selected_date
st.markdown(f"### 📊 {sel_date} 참여 타임라인 (겹침 확인)")

day_df = df[df['날짜'] == sel_date].copy()

if not day_df.empty:
    def to_dt(h): return datetime.datetime(2026, 1, 1, min(int(h), 23), 59 if h==24 else 0)

    fig = px.timeline(
        day_df, 
        x_start=day_df['시작'].apply(to_dt),
        x_end=day_df['종료'].apply(to_dt),
        y="이름", color="이름",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_layout(
        xaxis=dict(
            title="", tickformat="%H시", dtick=3600000 * 2,
            tickfont=dict(size=14),
            range=[datetime.datetime(2026, 1, 1, 0), datetime.datetime(2026, 1, 2, 0)]
        ),
        yaxis=dict(
            title="", autorange="reversed",
            tickfont=dict(size=16, color="white") # 이름 크게!
        ),
        showlegend=False, height=400,
        margin=dict(l=0, r=10, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    if len(day_df) >= 8:
        st.success("🔥 8인 매칭 완료! 세로로 막대가 8개 겹치는 시간을 확인하세요.")
else:
    st.info("선택한 날짜에 등록된 일정이 없습니다.")
