import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 일체형 그리드 UI CSS ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.markdown("""
    <style>
    /* 배경 및 기본 설정 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* [핵심] 달력 전체를 중앙으로 모으고 여백 제거 */
    .cal-wrapper {
        max-width: 950px; 
        margin: 0 auto;
        padding: 10px;
    }

    /* 요일 헤더와 날짜 버튼이 똑같은 너비를 갖도록 강제 고정 */
    div[data-testid="stColumn"] {
        padding: 0px !important;
        margin: 0px !important;
        flex: 1 1 0% !important;
    }
    div[data-testid="stHorizontalBlock"] { gap: 0 !important; }

    /* 요일 칸 디자인 */
    .day-header {
        text-align: center;
        font-weight: 900;
        background-color: #1a1d24;
        padding: 15px 0;
        border: 1px solid #262730;
        color: #aaa;
        font-size: 0.85rem;
    }

    /* 날짜 버튼: 요일 칸과 1:1로 맞물리는 완벽한 정사각형 */
    .stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important; /* 가로세로 비율 1:1 강제 */
        margin: 0 !important;
        padding: 0 !important;
        border-radius: 0px !important;
        border: 1px solid #262730 !important;
        background-color: #161920 !important;
        color: #666 !important;
        font-size: 1.1rem !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: all 0.2s ease;
    }

    /* 데이터가 있는 날짜: 네온 블루 (가독성 유지) */
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

    /* [사이드바] 일정 저장 버튼 프리미엄 스타일 */
    div[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 55px !important;
        aspect-ratio: auto !important;
        background: linear-gradient(135deg, #FF4B4B 0%, #800000 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        box-shadow: 0 4px 20px rgba(255, 75, 75, 0.4) !important;
        margin-top: 25px !important;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 25px rgba(255, 75, 75, 0.6) !important;
    }

    /* 제목 정렬 */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { text-align: center !important; }
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

# --- 4. 사이드바: 럭셔리 저장 UI ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B;'>🛡️ AION2</h1>", unsafe_allow_html=True)
    st.write("---")
    reg_date = st.date_input("📅 레이드 날짜", st.session_state.sel_date)
    name = st.selectbox("👤 대원 선택", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("⏰ 가능 시간대", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정 및 저장"):
        client = get_client()
        ws = client.open("AION2_Raid_Data").sheet1
        ws.append_row([str(reg_date), name, time_range[0], time_range[1]])
        st.cache_data.clear()
        st.success("데이터베이스 저장 완료!")
        st.rerun()

# --- 5. 메인 달력: 요일-버튼 일체형 그리드 ---
st.markdown("<div class='cal-wrapper'>", unsafe_allow_html=True)
st.title("AION2 공격대 조율실")
v_date = st.session_state.sel_date
st.subheader(f"📅 {v_date.year}년 {v_date.month}월")

# 요일 헤더
days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
h_cols = st.columns(7)
for i, d in enumerate(days):
    color = "#FF4B4B" if i == 0 else "#888"
    h_cols[i].markdown(f"<div class='day-header' style='color:{color};'>{d}</div>", unsafe_allow_html=True)

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')

# 달력 버튼 격자
cal = calendar.monthcalendar(v_date.year, v_date.month)
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].markdown("<div style='aspect-ratio:1/1; border:0.5px solid #161920;'></div>", unsafe_allow_html=True)
        else:
            cur_date = datetime.date(v_date.year, v_date.month, day)
            cnt = summary[summary['날짜'] == cur_date]['인원'].values[0] if not summary[summary['날짜'] == cur_date].empty else 0
            
            c_class = "has-data" if cnt > 0 else ""
            if cur_date == st.session_state.sel_date: c_class = "selected-date"
            
            label = f"{day}\n\n{f'👥 {cnt}명' if cnt > 0 else ''}"
            with cols[i]:
                st.markdown(f"<div class='{c_class}'>", unsafe_allow_html=True)
                if st.button(label, key=f"d_{day}"):
                    st.session_state.sel_date = cur_date
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 하단 타임라인 ---
st.write("---")
day_df = df[df['날짜'] == st.session_state.sel_date].copy()
if not day_df.empty:
    base = datetime.datetime.combine(st.session_state.sel_date, datetime.time.min)
    day_df['s'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=x))
    day_df['e'] = day_df['종료'].apply(lambda x: base + datetime.timedelta(hours=x))
    fig = px.timeline(day_df, x_start="s", x_end="e", y="이름", color="이름", template="plotly_dark")
    fig.update_layout(
        xaxis=dict(title="", tickformat="%H시"),
        yaxis=dict(title="", tickfont=dict(size=18, color="white")),
        showlegend=False, height=350, margin=dict(l=0, r=20, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
