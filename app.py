import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import plotly.express as px

# --- 1. 페이지 설정 및 통합 UI CSS ---
st.set_page_config(page_title="AION2 Raid Master", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 테이블 레이아웃 고정 */
    .calendar-table {
        width: 100%;
        max-width: 800px;
        margin: 10px auto;
        border-collapse: collapse;
        table-layout: fixed;
        background-color: #161920;
        border: 1px solid #262730;
    }
    .calendar-table th, .calendar-table td {
        border: 1px solid #262730;
        text-align: center;
        vertical-align: middle;
    }
    .calendar-table th {
        background-color: #1A1D24;
        height: 40px;
        color: #888;
        font-size: 0.8rem;
    }
    
    /* 날짜 칸 버튼화 */
    .stButton > button {
        width: 100% !important;
        height: 90px !important;
        background: transparent !important;
        border: none !important;
        color: #E0E0E0 !important;
        border-radius: 0px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .stButton > button:hover { background: #1F232C !important; }

    .sun-text { color: #FF4B4B !important; }
    .has-raid { color: #00FBFF !important; font-size: 0.7rem; font-weight: 900; }

    /* 사이드바 저장 버튼 */
    div[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #FF4B4B 0%, #800000 100%) !important;
        color: white !important;
        height: 50px !important;
        border-radius: 8px !important;
        font-weight: 900 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 로드 로직 ---
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=5)
def load_data():
    try:
        client = get_client()
        sheet = client.open("AION2_Raid_Data").sheet1
        data = pd.DataFrame(sheet.get_all_records())
        data['날짜'] = pd.to_datetime(data['날짜']).dt.date
        return data, sheet
    except:
        return pd.DataFrame(), None

df, _ = load_data()

# --- 3. 세션 상태 관리 ---
if 'view_date' not in st.session_state:
    st.session_state.view_date = datetime.date(2026, 3, 25)

# --- 4. 사이드바: 등록 시스템 ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B;'>🛡️ AION2</h1>", unsafe_allow_html=True)
    st.write("---")
    reg_date = st.date_input("📅 날짜 선택", st.session_state.view_date)
    name = st.selectbox("👤 대원명", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("⏰ 접속 시간", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정"):
        client = get_client()
        ws = client.open("AION2_Raid_Data").sheet1
        ws.append_row([str(reg_date), name, time_range[0], time_range[1]])
        st.cache_data.clear()
        st.success("기록 완료!")
        st.rerun()

# --- 5. 메인: 2026년 3월 달력 ---
st.markdown("<h2 style='text-align:center;'>📅 2026년 3월 레이드 현황</h2>", unsafe_allow_html=True)

march_days = [
    [1, 2, 3, 4, 5, 6, 7],
    [8, 9, 10, 11, 12, 13, 14],
    [15, 16, 17, 18, 19, 20, 21],
    [22, 23, 24, 25, 26, 27, 28],
    [29, 30, 31, 0, 0, 0, 0]
]

summary = df.groupby('날짜').size() if not df.empty else pd.Series()

# 헤더 출력
html_h = '<table class="calendar-table"><thead><tr>'
for i, d in enumerate(["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]):
    html_h += f'<th class="{"sun-text" if i==0 else ""}">{d}</th>'
html_h += '</tr></thead></table>'
st.markdown(html_h, unsafe_allow_html=True)

# 날짜 버튼 그리드
for week in march_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day != 0:
                cur_date = datetime.date(2026, 3, day)
                cnt = summary.get(cur_date, 0)
                label = f"{day}\n\n👥{cnt}" if cnt > 0 else f"{day}"
                
                # 선택된 날짜 강조 스타일은 버튼 key로 구분 (실제 CSS 적용은 생략, 기능 위주)
                if st.button(label, key=f"d_{day}"):
                    st.session_state.view_date = cur_date
                    st.rerun()
            else:
                st.markdown("<div style='height:90px;'></div>", unsafe_allow_html=True)

# --- 6. 하단: 타임라인 바 그래프 (핵심 추가) ---
st.write("---")
sel = st.session_state.view_date
st.markdown(f"### 📊 {sel} 접속 타임라인")

day_df = df[df['날짜'] == sel].copy()

if not day_df.empty:
    # Plotly용 시간 데이터 변환
    base = datetime.datetime.combine(sel, datetime.time.min)
    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=int(x)))
    day_df['end_dt'] = day_df['종료'].apply(lambda x: base + datetime.timedelta(hours=int(x)))
    
    fig = px.timeline(
        day_df, 
        x_start="start_dt", 
        x_end="end_dt", 
        y="이름", 
        color="이름",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_layout(
        xaxis=dict(title="접속 시간대", tickformat="%H시", dtick=3600000 * 2),
        yaxis=dict(title="", autorange="reversed", tickfont=dict(size=16)),
        showlegend=False,
        height=300,
        margin=dict(l=0, r=20, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 텍스트 명단도 함께 표시
    for _, row in day_df.iterrows():
        st.markdown(f"🔹 **{row['이름']}**: {row['시작']}시 ~ {row['종료']}시")
else:
    st.info("선택한 날짜에 등록된 인원이 없습니다.")
