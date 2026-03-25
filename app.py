import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 중앙 정렬 CSS ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* [핵심] 달력 전체를 중앙으로 모으고 너비 제한 */
    .main {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    .cal-container {
        width: 850px !important; /* 전체 달력 너비 고정 */
        margin: 0 auto !important;
        display: block;
    }

    /* 버튼을 완벽한 정사각형으로 고정 (120px) */
    .stButton > button {
        width: 110px !important;
        height: 110px !important;
        margin: 0 auto !important; /* 버튼 자체 중앙 정렬 */
        display: block !important;
        border-radius: 0px !important;
        border: 1px solid #262730 !important;
        background-color: #161920 !important;
        color: #555 !important;
        font-weight: bold !important;
    }

    /* 데이터가 있는 날짜 (25일 3명 등) 가독성 강화 */
    .has-data > div > div > button {
        background-color: #1c2533 !important;
        color: #00FBFF !important;
        border: 1px solid #00FBFF !important;
    }

    /* 선택된 날짜 (AION2 레드) */
    .selected-date > div > div > button {
        border: 2px solid #FF4B4B !important;
        background-color: #2D1A1E !important;
        color: #FF4B4B !important;
    }

    /* 요일 헤더 중앙 정렬 */
    .day-header {
        text-align: center;
        font-weight: 900;
        background-color: #1a1d24;
        padding: 10px 0;
        border: 1px solid #262730;
        color: #888;
        font-size: 0.8rem;
    }
    
    /* 제목 및 서브헤더 중앙 정렬 */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 ---
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=5)
def load_data():
    try:
        client = get_client()
        sheet = client.open("AION2_Raid_Data").sheet1
        return pd.DataFrame(sheet.get_all_records()), sheet
    except:
        return pd.DataFrame(), None

df, _ = load_data()

# --- 3. 세션 관리 ---
if 'sel_date' not in st.session_state:
    st.session_state.sel_date = datetime.date(2026, 3, 25)

# --- 4. 사이드바 (등록 기능) ---
with st.sidebar:
    st.title("🛡️ AION2")
    reg_date = st.date_input("날짜 선택", st.session_state.sel_date)
    name = st.selectbox("대원명", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("접속 시간", options=list(range(25)), value=(20, 23))
    if st.button("🚀 일정 저장"):
        client = get_client()
        ws = client.open("AION2_Raid_Data").sheet1
        ws.append_row([str(reg_date), name, time_range[0], time_range[1]])
        st.cache_data.clear()
        st.rerun()

# --- 5. 메인 달력 (중앙 정렬 그리드) ---
st.title("AION2 공격대 조율실")
v_date = st.session_state.sel_date
st.subheader(f"📅 {v_date.year}년 {v_date.month}월 현황")

# [중앙 정렬 컨테이너 시작]
st.markdown("<div class='cal-container'>", unsafe_allow_html=True)

days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
h_cols = st.columns(7)
for i, d in enumerate(days):
    h_cols[i].markdown(f"<div class='day-header'>{d}</div>", unsafe_allow_html=True)

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')

cal = calendar.monthcalendar(v_date.year, v_date.month)
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].markdown("<div style='height:110px;'></div>", unsafe_allow_html=True)
        else:
            cur_date = datetime.date(v_date.year, v_date.month, day)
            cnt = summary[summary['날짜'] == cur_date]['인원'].values[0] if not summary[summary['날짜'] == cur_date].empty else 0
            
            c_class = "has-data" if cnt > 0 else ""
            if cur_date == st.session_state.sel_date: c_class = "selected-date"
            
            label = f"{day}\n\n{f'👥 {cnt}' if cnt > 0 else ''}"
            with cols[i]:
                st.markdown(f"<div class='{c_class}'>", unsafe_allow_html=True)
                if st.button(label, key=f"d_{day}"):
                    st.session_state.sel_date = cur_date
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True) # [중앙 정렬 컨테이너 종료]

# --- 6. 상세 타임라인 ---
st.write("---")
day_df = df[df['날짜'] == st.session_state.sel_date].copy()
if not day_df.empty:
    base = datetime.datetime.combine(st.session_state.sel_date, datetime.time.min)
    day_df['s'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=x))
    day_df['e'] = day_df['종료'].apply(lambda x: base + datetime.timedelta(hours=x))
    fig = px.timeline(day_df, x_start="s", x_end="e", y="이름", color="이름", template="plotly_dark")
    fig.update_layout(xaxis=dict(title="", tickformat="%H시"), yaxis=dict(title="", tickfont=dict(size=18, color="white")), showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)
