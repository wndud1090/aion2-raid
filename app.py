import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 완전 밀착형 정사각형 그리드 CSS ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* [핵심] 컬럼 간격 제거 및 가로 꽉 채우기 */
    div[data-testid="stColumn"] { padding: 0px !important; margin: 0px !important; }
    div[data-testid="stHorizontalBlock"] { gap: 0 !important; }

    /* 정사각형 버튼 디자인: 가로 100% + 세로 고정 */
    .stButton > button {
        width: 100% !important;
        height: 160px !important; /* 높이를 충분히 주어 정사각형 형태 유지 */
        margin: 0 !important;
        padding: 0 !important;
        border-radius: 0px !important; 
        border: 0.5px solid #262730 !important; 
        background-color: #161920 !important;
        color: #666 !important;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* 데이터가 있는 날짜: 네온 블루 하이라이트 */
    .has-data > div > div > button {
        background-color: #1c2533 !important;
        color: #00FBFF !important;
        border: 1px solid #00FBFF !important;
    }
    .has-data > div > div > button p { font-weight: 900 !important; }

    /* 선택된 날짜: AION2 시그니처 레드 */
    .selected-date > div > div > button {
        background-color: #2D1A1E !important;
        border: 2px solid #FF4B4B !important;
        color: #FF4B4B !important;
    }

    /* 요일 헤더 디자인 */
    .day-header {
        text-align: center;
        font-weight: 900;
        background-color: #1a1d24;
        padding: 15px 0;
        border: 1px solid #262730;
        color: #aaa;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 로직 ---
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

# --- 3. 세션 및 날짜 관리 ---
if 'sel_date' not in st.session_state:
    st.session_state.sel_date = datetime.date(2026, 3, 25)

# --- 4. 사이드바 (일정 등록) ---
with st.sidebar:
    st.title("🛡️ AION2")
    reg_date = st.date_input("날짜 선택", st.session_state.sel_date)
    name = st.selectbox("대원", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("시간", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정"):
        client = get_client()
        ws = client.open("AION2_Raid_Data").sheet1
        ws.append_row([str(reg_date), name, time_range[0], time_range[1]])
        st.cache_data.clear()
        st.rerun()

# --- 5. 메인 달력: 빈틈없는 7열 정사각형 그리드 ---
st.title("AION2 8인 레이드 실시간 조율실")
v_date = st.session_state.sel_date
cal = calendar.monthcalendar(v_date.year, v_date.month)

# 요일 표시줄
days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
h_cols = st.columns(7)
for i, d in enumerate(days):
    h_cols[i].markdown(f"<div class='day-header'>{d}</div>", unsafe_allow_html=True)

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')

# 달력 그리드 생성
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].markdown("<div style='height:160px; background-color:#0E1117; border:0.5px solid #161920;'></div>", unsafe_allow_html=True)
        else:
            cur_date = datetime.date(v_date.year, v_date.month, day)
            cnt = summary[summary['날짜'] == cur_date]['인원'].values[0] if not summary[summary['날짜'] == cur_date].empty else 0
            
            c_class = ""
            if cnt > 0: c_class = "has-data"
            if cur_date == st.session_state.sel_date: c_class = "selected-date"
            
            # 레이블 구성 (날짜와 인원수)
            label = f"{day}\n\n{f'👥 {cnt}명' if cnt > 0 else ''}"
            
            with cols[i]:
                st.markdown(f"<div class='{c_class}'>", unsafe_allow_html=True)
                if st.button(label, key=f"d_{day}"):
                    st.session_state.sel_date = cur_date
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 하단 타임라인 (가독성 강화) ---
st.write("---")
day_df = df[df['날짜'] == st.session_state.sel_date].copy()
st.subheader(f"📊 {st.session_state.sel_date} 참여 타임라인")

if not day_df.empty:
    base = datetime.datetime.combine(st.session_state.sel_date, datetime.time.min)
    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=x))
    day_df['end_dt'] = day_df['종료'].apply(lambda x: base + datetime.timedelta(hours=x))

    fig = px.timeline(
        day_df, x_start="start_dt", x_end="end_dt", y="이름", color="이름",
        template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(
        xaxis=dict(title="접속 시간", tickformat="%H시", dtick=3600000 * 2),
        yaxis=dict(title="", tickfont=dict(size=22, color="white", family="Arial Black")),
        showlegend=False, height=450, margin=dict(l=0, r=20, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("해당 날짜에 등록된 대원이 없습니다.")
