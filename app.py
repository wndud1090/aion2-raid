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
    
    /* 달력 전체 컨테이너 빈틈 제거 */
    div[data-testid="stColumn"] { padding: 0 !important; margin: 0 !important; }
    .stHorizontalBlock { gap: 0rem !important; }

    /* 프리미엄 버튼 디자인: 크기 확대 및 완전 밀착 */
    .stButton > button {
        width: 100% !important;
        height: 140px !important; /* 더 크게 확대 */
        margin: 0 !important;
        padding: 0 !important;
        border-radius: 0px !important; /* 각진 그리드 스타일 */
        border: 0.5px solid #262730 !important; /* 미세한 경계선 */
        background-color: #161920 !important;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* 마우스 호버 및 선택 효과 */
    .stButton > button:hover {
        background-color: #262730 !important;
        border: 1px solid #FF4B4B !important;
        z-index: 10;
    }

    /* 인원이 등록된 날짜 하이라이트 (강렬한 가독성) */
    .has-data > div > div > button {
        background-color: #1c2533 !important; /* 푸른빛 도는 진한 다크 */
        color: #00D1FF !important; /* 밝은 하늘색으로 시선 고정 */
    }

    /* 선택된 날짜 강조 */
    .selected-date > div > div > button {
        border: 2px solid #FF4B4B !important;
        background-color: #2D1A1E !important;
        color: #FF4B4B !important;
    }

    /* 풀파티 강조 (Gold) */
    .full-party > div > div > button {
        border: 2px solid #FFD700 !important;
        color: #FFD700 !important;
        background-color: #2D2A1A !important;
    }

    /* 버튼 내 텍스트 스타일: 숫자와 인원 분리 */
    .stButton > button p {
        line-height: 1.5 !important;
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

df, sheet_obj = load_data()

# --- 3. 세션 관리 ---
if 'sel_date' not in st.session_state:
    st.session_state.sel_date = datetime.date(2026, 3, 25)

# --- 4. 사이드바 ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B;'>⚔️ AION2</h1>", unsafe_allow_html=True)
    reg_date = st.date_input("날짜", st.session_state.sel_date)
    name = st.selectbox("대원", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("시간", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 등록"):
        client = get_client()
        ws = client.open("AION2_Raid_Data").sheet1
        ws.append_row([str(reg_date), name, time_range[0], time_range[1]])
        st.cache_data.clear()
        st.rerun()

# --- 5. 메인 달력: 빈틈없는 풀-그리드 ---
st.title("AION2 레이드 대시보드")
v_date = st.session_state.sel_date
cal = calendar.monthcalendar(v_date.year, v_date.month)

# 요일 헤더 (심플 프리미엄)
days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
h_cols = st.columns(7)
for i, d in enumerate(days):
    h_cols[i].markdown(f"<p style='text-align:center; font-weight:900; color:#444; margin:0;'>{d}</p>", unsafe_allow_html=True)

# 달력 출력
if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')

for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].markdown("<div style='height:140px; background-color:#0E1117; border:0.1px solid #161920;'></div>", unsafe_allow_html=True)
        else:
            cur_date = datetime.date(v_date.year, v_date.month, day)
            cnt = summary[summary['날짜'] == cur_date]['인원'].values[0] if not summary[summary['날짜'] == cur_date].empty else 0
            
            # 클래스 분기
            c_class = ""
            if cnt > 0: c_class = "has-data"
            if cnt >= 8: c_class = "full-party"
            if cur_date == st.session_state.sel_date: c_class = "selected-date"
            
            # 가독성 높은 레이블 (인원수 강조)
            label = f"{day}\n\n"
            if cnt > 0: label += f"👥 {cnt}명"
            if cnt >= 8: label = f"{day}\n\n🔥FULL"
            
            with cols[i]:
                st.markdown(f"<div class='{c_class}'>", unsafe_allow_html=True)
                if st.button(label, key=f"d_{day}"):
                    st.session_state.sel_date = cur_date
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 상세 타임라인 ---
st.write("---")
day_df = df[df['날짜'] == st.session_state.sel_date].copy()
st.markdown(f"### 📊 {st.session_state.sel_date} 참여 현황 ({len(day_df)}명 등록됨)")

if not day_df.empty:
    def to_dt(h): return datetime.datetime(2026, 1, 1, min(int(h), 23), 0)
    fig = px.timeline(day_df, x_start=day_df['시작'].apply(to_dt), x_end=day_df['종료'].apply(to_dt), y="이름", color="이름", template="plotly_dark")
    fig.update_layout(
        xaxis=dict(title="", tickformat="%H시", range=[datetime.datetime(2026,1,1,0), datetime.datetime(2026,1,2,0)]),
        yaxis=dict(title="", tickfont=dict(size=20, color="white")),
        showlegend=False, height=400, margin=dict(l=0, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
