import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import plotly.express as px

# --- 1. 페이지 설정 및 UI ---
st.set_page_config(page_title="AION2 Raid Master", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .calendar-table {
        width: 100%; max-width: 800px; margin: 10px auto;
        border-collapse: collapse; table-layout: fixed;
        background-color: #161920; border: 1px solid #262730;
    }
    .calendar-table th { background-color: #1A1D24; height: 40px; color: #888; border: 1px solid #262730; }
    .stButton > button {
        width: 100% !important; height: 90px !important;
        background: transparent !important; border: 1px solid #262730 !important;
        color: #E0E0E0 !important; border-radius: 0px !important;
    }
    .stButton > button:hover { background: #1F232C !important; }
    .sun-text { color: #FF4B4B !important; }
    div[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #FF4B4B 0%, #800000 100%) !important;
        color: white !important; height: 50px !important; border-radius: 8px !important; font-weight: 900 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 로드 ---
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

if 'view_date' not in st.session_state:
    st.session_state.view_date = datetime.date(2026, 3, 25)

# --- 3. 사이드바: 익일 대응 입력창 ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B;'>🛡️ AION2 설정</h1>", unsafe_allow_html=True)
    
    with st.expander("👥 대원 명단 설정 (8명)", expanded=False):
        raw_names = st.text_area("쉼표(,)로 구분 입력", "공대장, 대원1, 대원2, 대원3, 대원4, 대원5, 대원6, 대원7")
        member_list = [n.strip() for n in raw_names.split(",") if n.strip()][:8]

    st.write("---")
    reg_date = st.date_input("📅 날짜 선택", st.session_state.view_date)
    name = st.selectbox("👤 대원 선택", member_list)
    
    # 시간 선택 방식 변경: 시작과 종료를 각각 선택 (익일 대응을 위해)
    st.write("⏰ **접속 시간 설정**")
    col1, col2 = st.columns(2)
    with col1:
        s_time = st.number_input("시작(시)", 0, 23, 22)
    with col2:
        e_time = st.number_input("종료(시)", 0, 23, 2)
    
    if s_time >= e_time:
        st.warning("🌙 종료가 시작보다 빠르면 '익일 새벽'으로 자동 처리됩니다.")

    if st.button("🚀 일정 확정"):
        client = get_client()
        ws = client.open("AION2_Raid_Data").sheet1
        ws.append_row([str(reg_date), name, s_time, e_time])
        st.cache_data.clear()
        st.success(f"{name} 등록 완료!")
        st.rerun()

# --- 4. 메인: 달력 ---
st.markdown("<h2 style='text-align:center;'>📅 2026년 3월 레이드 현황</h2>", unsafe_allow_html=True)

march_days = [
    [1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14],
    [15, 16, 17, 18, 19, 20, 21], [22, 23, 24, 25, 26, 27, 28],
    [29, 30, 31, 0, 0, 0, 0]
]
summary = df.groupby('날짜').size() if not df.empty else pd.Series()

html_h = '<table class="calendar-table"><thead><tr>'
for i, d in enumerate(["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]):
    html_h += f'<th class="{"sun-text" if i==0 else ""}">{d}</th>'
html_h += '</tr></thead></table>'
st.markdown(html_h, unsafe_allow_html=True)

for week in march_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day != 0:
                cur_date = datetime.date(2026, 3, day)
                cnt = summary.get(cur_date, 0)
                label = f"{day}\n\n👥{cnt}" if cnt > 0 else f"{day}"
                if st.button(label, key=f"d_{day}"):
                    st.session_state.view_date = cur_date
                    st.rerun()
            else:
                st.markdown("<div style='height:90px;'></div>", unsafe_allow_html=True)

# --- 5. 하단: 타임라인 그래프 (익일 로직 적용) ---
st.write("---")
sel = st.session_state.view_date
st.markdown(f"### 📊 {sel} 접속 타임라인")

day_df = df[df['날짜'] == sel].copy()

if not day_df.empty:
    base = datetime.datetime.combine(sel, datetime.time.min)
    
    # 익일 로직 적용 함수
    def get_end_time(row):
        start = int(row['시작'])
        end = int(row['종료'])
        # 종료 시간이 시작 시간보다 작으면 다음 날로 처리
        if end <= start:
            return base + datetime.timedelta(days=1, hours=end)
        return base + datetime.timedelta(hours=end)

    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=int(x)))
    day_df['end_dt'] = day_df.apply(get_end_time, axis=1)
    
    fig = px.timeline(
        day_df, x_start="start_dt", x_end="end_dt", y="이름", color="이름",
        template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # 시간축 표시 범위 최적화 (24시간을 넘기더라도 보여줌)
    fig.update_layout(
        xaxis=dict(title="", tickformat="%H시"), 
        yaxis=dict(title="", autorange="reversed"),
        showlegend=False, height=300, margin=dict(l=0, r=20, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("등록된 인원이 없습니다.")
