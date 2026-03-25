import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 격자 고정 CSS ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 버튼을 정사각형 격자로 강제 고정 */
    div[data-testid="stColumn"] > div {
        padding: 2px !important;
    }
    
    .stButton > button {
        width: 100% !important;
        height: 100px !important; /* 높이 고정 */
        border-radius: 5px !important;
        border: 1px solid #262730 !important;
        background-color: #161920 !important;
        display: block !important;
        transition: all 0.2s;
    }
    
    /* 마우스 올렸을 때 및 선택 시 효과 */
    .stButton > button:hover {
        border-color: #FF4B4B !important;
        background-color: #1e222b !important;
    }
    
    /* 8인 풀파티 날짜 강조 */
    .full-party-btn > div > div > button {
        border: 2px solid #FFD700 !important;
        color: #FFD700 !important;
    }

    /* 선택된 날짜 강조 */
    .selected-btn > div > div > button {
        border: 2px solid #FF4B4B !important;
        background-color: #262730 !important;
    }

    /* 버튼 내 텍스트 정렬 */
    .stButton > button p {
        font-size: 1.2rem !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 (인증 유지) ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gspread"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"인증 오류: {e}")
        st.stop()

@st.cache_data(ttl=10)
def load_data():
    client = get_gspread_client()
    try:
        sheet = client.open("AION2_Raid_Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except:
        return pd.DataFrame(), None

df, sheet = load_data()

# --- 3. 사이드바 (일정 등록) ---
with st.sidebar:
    st.markdown("<h2 style='color:#FF4B4B;'>🛡️ AION2</h2>", unsafe_allow_html=True)
    fixed_year = 2026
    # 기본 날짜 설정
    if 'target_date' not in st.session_state:
        st.session_state.target_date = datetime.date(fixed_year, 3, 25)
    
    reg_date = st.date_input("등록할 날짜", st.session_state.target_date)
    name = st.selectbox("대원명", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("시간(시)", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정"):
        client = get_gspread_client()
        curr_sheet = client.open("AION2_Raid_Data").sheet1
        all_v = curr_sheet.get_all_values()
        date_str = str(reg_date)
        for i, row in enumerate(all_v):
            if len(row) >= 2 and row[0] == date_str and row[1] == name:
                curr_sheet.delete_rows(i + 1)
        curr_sheet.append_row([date_str, name, time_range[0], time_range[1]])
        st.success("저장되었습니다!")
        st.cache_data.clear()
        st.rerun()

# --- 4. 메인 달력: 클릭 가능한 진짜 격자 ---
st.title("AION2 공격대 실시간 조율실")
view_date = st.session_state.target_date
cal_year, cal_month = view_date.year, view_date.month
st.subheader(f"📅 {cal_year}년 {cal_month}월 (날짜를 클릭하여 현황 확인)")

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')
    cal = calendar.monthcalendar(cal_year, cal_month)
    
    # 요일 헤더
    days = ["일", "월", "화", "수", "목", "금", "토"]
    h_cols = st.columns(7)
    for i, d in enumerate(days):
        h_cols[i].markdown(f"<p style='text-align:center; font-weight:bold;'>{d}</p>", unsafe_allow_html=True)

    # 격자 버튼 생성
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("<div style='height:100px;'></div>", unsafe_allow_html=True)
            else:
                this_date = datetime.date(cal_year, cal_month, day)
                cnt = summary[summary['날짜'] == this_date]['인원'].values[0] if not summary[summary['날짜'] == this_date].empty else 0
                
                # 버튼 레이블 및 스타일 클래스
                label = f"{day}\n({cnt}명)"
                if cnt >= 8: label = f"{day}\n🔥FULL"
                
                # 풀파티/선택 상태에 따른 CSS 컨테이너
                container_class = ""
                if cnt >= 8: container_class = "full-party-btn"
                if this_date == st.session_state.target_date: container_class = "selected-btn"
                
                with cols[i]:
                    st.markdown(f"<div class='{container_class}'>", unsafe_allow_html=True)
                    if st.button(label, key=f"btn_{day}"):
                        st.session_state.target_date = this_date
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 상세 타임라인 (빅폰트) ---
st.write("---")
sel_date = st.session_state.target_date
st.markdown(f"### 📊 {sel_date} 참여 타임라인")

day_df = df[df['날짜'] == sel_date].copy()

if not day_df.empty:
    def to_dt(h): return datetime.datetime(2026, 1, 1, min(int(h), 23), 59 if h==24 else 0)
    
    fig = px.timeline(
        day_df, x_start=day_df['시작'].apply(to_dt), x_end=day_df['종료'].apply(to_dt),
        y="이름", color="이름", template="plotly_dark"
    )
    fig.update_layout(
        xaxis=dict(title="", tickformat="%H시", dtick=3600000 * 2, tickfont=dict(size=14),
                   range=[datetime.datetime(2026, 1, 1, 0), datetime.datetime(2026, 1, 2, 0)]),
        yaxis=dict(title="", autorange="reversed", tickfont=dict(size=20, color="white")),
        showlegend=False, height=400, margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("이날은 등록된 인원이 없습니다.")
