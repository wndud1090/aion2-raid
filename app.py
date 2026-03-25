import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# --- 1. 페이지 설정 및 부동의 테이블 UI CSS ---
st.set_page_config(page_title="AION2 Raid Master", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* 테이블 레이아웃 고정 */
    .calendar-table {
        width: 100%;
        max-width: 800px;
        margin: 20px auto;
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
        height: 45px;
        color: #888;
        font-size: 0.8rem;
    }
    /* 날짜 칸 정사각형 유지 및 버튼화 */
    .cal-td { height: 100px; padding: 0 !important; position: relative; }
    
    /* 투명 버튼으로 날짜 칸 전체 클릭 가능하게 설정 */
    .stButton > button {
        width: 100% !important;
        height: 100px !important;
        background: transparent !important;
        border: none !important;
        color: #E0E0E0 !important;
        border-radius: 0px !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover { background: #1F232C !important; }

    /* 일요일/하이라이트 스타일 */
    .sun-text { color: #FF4B4B !important; }
    .has-raid { color: #00FBFF !important; font-size: 0.75rem; font-weight: 900; display: block; }
    .selected-day { background-color: #2D1A1E !important; border: 2px solid #FF4B4B !important; }

    /* 사이드바 저장 버튼 디자인 */
    div[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #FF4B4B 0%, #800000 100%) !important;
        color: white !important;
        height: 50px !important;
        border-radius: 8px !important;
        font-weight: 900 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 및 데이터 로드 ---
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

# --- 3. 세션 상태 (날짜 선택) ---
if 'view_date' not in st.session_state:
    st.session_state.view_date = datetime.date(2026, 3, 25)

# --- 4. 사이드바: 대원 등록 ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B;'>🛡️ AION2</h1>", unsafe_allow_html=True)
    st.write("---")
    reg_date = st.date_input("📅 날짜", st.session_state.view_date)
    name = st.selectbox("👤 대원", [f"유저{i}" for i in range(1, 9)])
    time_range = st.select_slider("⏰ 시간", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정"):
        client = get_client()
        ws = client.open("AION2_Raid_Data").sheet1
        ws.append_row([str(reg_date), name, time_range[0], time_range[1]])
        st.cache_data.clear()
        st.success(f"{name} 등록 완료!")
        st.rerun()

# --- 5. 메인: 2026년 3월 달력 명당 ---
st.markdown(f"<h2 style='text-align:center;'>📅 2026년 3월 현황</h2>", unsafe_allow_html=True)

# 3월 달력 배열 (일요일 시작)
march_days = [
    [1, 2, 3, 4, 5, 6, 7],
    [8, 9, 10, 11, 12, 13, 14],
    [15, 16, 17, 18, 19, 20, 21],
    [22, 23, 24, 25, 26, 27, 28],
    [29, 30, 31, 0, 0, 0, 0]
]

# 인원 요약 데이터
summary = df.groupby('날짜').size() if not df.empty else pd.Series()

# HTML 테이블 생성 시작
html = '<table class="calendar-table"><thead><tr>'
for i, d in enumerate(["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]):
    html += f'<th class="{"sun-text" if i==0 else ""}">{d}</th>'
html += '</tr></thead><tbody>'

st.markdown(html, unsafe_allow_html=True) # 헤더 출력

# 날짜 행별로 처리 (Streamlit 버튼을 넣기 위해 행단위 분할 출력)
for week in march_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.markdown("<div style='height:100px; border:0.5px solid #262730;'></div>", unsafe_allow_html=True)
            else:
                cur_date = datetime.date(2026, 3, day)
                cnt = summary.get(cur_date, 0)
                
                # 버튼 텍스트 구성
                label = f"{day}\n\n👥 {cnt}" if cnt > 0 else f"{day}"
                
                # 날짜 클릭 시 세션 날짜 변경
                if st.button(label, key=f"btn_{day}"):
                    st.session_state.view_date = cur_date
                    st.rerun()

st.markdown("</tbody></table>", unsafe_allow_html=True)

# --- 6. 하단: 선택 날짜 명단 정보 ---
st.write("---")
sel = st.session_state.view_date
st.markdown(f"### 📊 {sel} 참석 명단")

day_df = df[df['날짜'] == sel]
if not day_df.empty:
    for idx, row in day_df.iterrows():
        st.markdown(f"✅ **{row['이름']}** 대원 : {row['시작']}시 ~ {row['종료']}시")
else:
    st.info("해당 날짜에 등록된 인원이 없습니다.")
