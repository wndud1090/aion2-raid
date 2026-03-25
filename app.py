import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 프리미엄 커스텀 CSS ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #0E1117; color: #E0E0E0; font-family: 'Pretendard', sans-serif; }
    
    /* 사이드바 디자인 */
    [data-testid="stSidebar"] { background-color: #161920; border-right: 1px solid #262730; }

    /* 달력 격자 시스템 (고정 높이 및 디자인) */
    div[data-testid="stColumn"] { padding: 0 !important; }
    
    .stButton > button {
        width: 100% !important;
        height: 120px !important; /* 높이 고정 */
        border-radius: 0px !important; /* 각진 프리미엄 디자인 */
        border: 1px solid #262730 !important;
        background: linear-gradient(145deg, #161920, #0e1117) !important;
        color: #888 !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 !important;
    }

    /* 호버 시 효과 */
    .stButton > button:hover {
        border-color: #FF4B4B !important;
        color: #FF4B4B !important;
        transform: scale(0.98);
        z-index: 10;
    }

    /* 선택된 날짜 (Red 테마) */
    .selected-date > div > div > button {
        border: 2px solid #FF4B4B !important;
        background: #1e1e1e !important;
        color: #FF4B4B !important;
        box-shadow: inset 0 0 15px rgba(255, 75, 75, 0.2);
    }

    /* 풀파티 날짜 (Gold 테마) */
    .full-party > div > div > button {
        border: 2px solid #FFD700 !important;
        color: #FFD700 !important;
        background: linear-gradient(145deg, #1e1e10, #0e1117) !important;
    }

    /* 그래프 Y축 이름 폰트 강화 */
    .js-plotly-plot .ytick text {
        font-size: 20px !important;
        font-weight: bold !important;
        fill: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gspread"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except:
        st.error("구글 시트 인증에 실패했습니다.")
        st.stop()

@st.cache_data(ttl=10)
def load_data():
    client = get_gspread_client()
    try:
        sheet = client.open("AION2_Raid_Data").sheet1
        return pd.DataFrame(sheet.get_all_records()), sheet
    except:
        return pd.DataFrame(), None

df, sheet_obj = load_data()

# --- 3. 세션 상태 관리 (클릭 날짜 저장) ---
if 'sel_date' not in st.session_state:
    st.session_state.sel_date = datetime.date(2026, 3, 25)

# --- 4. 사이드바 (등록 기능) ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>🛡️ AION2</h1>", unsafe_allow_html=True)
    st.write("---")
    
    reg_date = st.date_input("📅 날짜 선택", st.session_state.sel_date)
    name = st.selectbox("👤 대원 선택", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("⏰ 가능 시간", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정"):
        client = get_gspread_client()
        ws = client.open("AION2_Raid_Data").sheet1
        all_v = ws.get_all_values()
        d_str = str(reg_date)
        for i, row in enumerate(all_v):
            if len(row) >= 2 and row[0] == d_str and row[1] == name:
                ws.delete_rows(i + 1)
        ws.append_row([d_str, name, time_range[0], time_range[1]])
        st.success("저장 완료!")
        st.cache_data.clear()
        st.rerun()

# --- 5. 메인 섹션: 프리미엄 격자 달력 ---
st.title("⚔️ AION2 공격대 조율실")
view_date = st.session_state.sel_date
st.subheader(f"📅 {view_date.year}년 {view_date.month}월 현황")

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')
    cal = calendar.monthcalendar(view_date.year, view_date.month)
    
    # 요일 헤더
    days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    h_cols = st.columns(7)
    for i, d in enumerate(days):
        color = "#FF4B4B" if i == 0 else "#555"
        h_cols[i].markdown(f"<p style='text-align:center; font-weight:900; color:{color};'>{d}</p>", unsafe_allow_html=True)

    # 격자 버튼 배치
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("<div style='height:120px; border:1px solid #161920;'></div>", unsafe_allow_html=True)
            else:
                cur_date = datetime.date(view_date.year, view_date.month, day)
                cnt = summary[summary['날짜'] == cur_date]['인원'].values[0] if not summary[summary['날짜'] == cur_date].empty else 0
                
                # 상태별 클래스 부여
                c_class = ""
                if cnt >= 8: c_class = "full-party"
                if cur_date == st.session_state.sel_date: c_class = "selected-date"
                
                # 버튼 레이블 (인원수 표시)
                btn_label = f"{day}\n({cnt}명)"
                if cnt >= 8: btn_label = f"{day}\n🔥FULL"
                
                with cols[i]:
                    st.markdown(f"<div class='{c_class}'>", unsafe_allow_html=True)
                    if st.button(btn_label, key=f"d_{day}"):
                        st.session_state.sel_date = cur_date
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. 상세 타임라인 (대왕 폰트) ---
st.write("---")
st.markdown(f"### 📊 {st.session_state.sel_date} 참여 타임라인")

day_df = df[df['날짜'] == st.session_state.sel_date].copy()

if not day_df.empty:
    def to_dt(h): return datetime.datetime(2026, 1, 1, min(int(h), 23), 59 if h==24 else 0)
    
    fig = px.timeline(
        day_df, x_start=day_df['시작'].apply(to_dt), x_end=day_df['종료'].apply(to_dt),
        y="이름", color="이름", template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(
        xaxis=dict(title="", tickformat="%H시", dtick=3600000 * 2, tickfont=dict(size=14, color="#888"),
                   range=[datetime.datetime(2026, 1, 1, 0), datetime.datetime(2026, 1, 2, 0)]),
        yaxis=dict(title="", autorange="reversed", tickfont=dict(size=22, color="white")), # 이름 폰트 극대화
        showlegend=False, height=450, margin=dict(l=0, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("이날은 등록된 대원이 없습니다. 사이드바에서 등록해 주세요.")

st.caption(f"Last Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")
