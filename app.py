import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 완전 밀착형 격자 CSS ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 달력 전체 컨테이너 빈틈 제거 및 가로 꽉 채우기 */
    div[data-testid="stColumn"] { padding: 0px !important; margin: 0px !important; }
    div[data-testid="stHorizontalBlock"] { gap: 0 !important; }

    /* 프리미엄 버튼 디자인: 가로/세로 꽉 채우기 */
    .stButton > button {
        width: 100% !important;
        height: 150px !important; /* 높이 대폭 확대 */
        margin: 0 !important;
        padding: 0 !important;
        border-radius: 0px !important; 
        border: 1px solid #262730 !important; 
        background-color: #161920 !important;
        color: #555 !important;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
    }

    /* 인원이 있는 날짜: 네온 블루 테마로 가독성 폭발 */
    .has-data > div > div > button {
        background-color: #1c2533 !important;
        color: #00FBFF !important; /* 형광 하늘색 */
        border: 1px solid #00FBFF !important;
    }
    .has-data > div > div > button p {
        font-weight: 900 !important;
        text-shadow: 0 0 10px rgba(0, 251, 255, 0.4);
    }

    /* 선택된 날짜: 강렬한 레드 */
    .selected-date > div > div > button {
        background-color: #2D1A1E !important;
        border: 2px solid #FF4B4B !important;
        color: #FF4B4B !important;
    }

    /* 요일 헤더 스타일 */
    .day-header {
        text-align: center;
        font-weight: 900;
        background-color: #161920;
        padding: 10px 0;
        border: 1px solid #262730;
        color: #888;
        margin: 0;
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
    st.title("⚔️ AION2")
    reg_date = st.date_input("날짜", st.session_state.sel_date)
    name = st.selectbox("대원", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("시간", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 등록"):
        client = get_client()
        ws = client.open("AION2_Raid_Data").sheet1
        ws.append_row([str(reg_date), name, time_range[0], time_range[1]])
        st.cache_data.clear()
        st.rerun()

# --- 5. 메인 달력: 빈틈없는 7칸 그리드 ---
st.title("AION2 레이드 스케줄러")
v_date = st.session_state.sel_date
cal = calendar.monthcalendar(v_date.year, v_date.month)

# 요일 헤더
days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
h_cols = st.columns(7)
for i, d in enumerate(days):
    h_cols[i].markdown(f"<div class='day-header'>{d}</div>", unsafe_allow_html=True)

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')

# 달력 출력 (빈틈없이 꽉 채우기)
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].markdown("<div style='height:150px; background-color:#0E1117; border:0.5px solid #161920;'></div>", unsafe_allow_html=True)
        else:
            cur_date = datetime.date(v_date.year, v_date.month, day)
            cnt = summary[summary['날짜'] == cur_date]['인원'].values[0] if not summary[summary['날짜'] == cur_date].empty else 0
            
            c_class = ""
            if cnt > 0: c_class = "has-data"
            if cur_date == st.session_state.sel_date: c_class = "selected-date"
            
            # 레이블 가독성 강화
            label = f"{day}\n\n{f'👥 {cnt}명' if cnt > 0 else ''}"
            
            with cols[i]:
                st.markdown(f"<div class='{c_class}'>", unsafe_allow_html=True)
                if st.button(label, key=f"d_{day}"):
                    st.session_state.sel_date = cur_date
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 상세 타임라인 (1970년 시간 오류 수정) ---
st.write("---")
day_df = df[df['날짜'] == st.session_state.sel_date].copy()
st.subheader(f"📊 {st.session_state.sel_date} 참여 타임라인")

if not day_df.empty:
    # 1970년 오류를 막기 위해 오늘 날짜를 기준으로 시간 생성
    base = datetime.datetime.combine(st.session_state.sel_date, datetime.time.min)
    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=x))
    day_df['end_dt'] = day_df['종료'].apply(lambda x: base + datetime.timedelta(hours=x))

    fig = px.timeline(
        day_df, x_start="start_dt", x_end="end_dt", y="이름", color="이름",
        template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig.update_layout(
        xaxis=dict(title="", tickformat="%H시", dtick=3600000 * 2, tickfont=dict(size=14)),
        yaxis=dict(title="", tickfont=dict(size=20, color="white", family="Arial Black")),
        showlegend=False, height=400, margin=dict(l=0, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("선택한 날짜에 등록된 인원이 없습니다.")
