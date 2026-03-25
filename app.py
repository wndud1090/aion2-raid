import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import plotly.express as px
import numpy as np

# ==========================================
# [공대장 전용] 대원 명단 설정 (여기서 직접 수정하세요)
# ==========================================
MEMBER_LIST = ["공대장", "대원1", "대원2", "대원3", "대원4", "대원5", "대원6", "대원7"]
# ==========================================

# --- 1. 페이지 설정 및 UI (녹색 아이콘 CSS 추가) ---
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
    
    /* 기본 버튼 스타일 */
    .stButton > button {
        width: 100% !important; height: 95px !important;
        background: transparent !important; border: 1px solid #262730 !important;
        color: #E0E0E0 !important; border-radius: 0px !important;
    }
    
    /* [핵심 수정] 인원이 있는 날짜: 선명한 녹색 아이콘 적용 */
    .has-members .member-icon { color: #32CD32 !important; font-weight: 900; }

    /* 8명 매칭 성공 시 (황금색 점등 유지) */
    .match-gold > div > div > button {
        background: linear-gradient(135deg, #443714 0%, #161920 100%) !important;
        border: 2px solid #FFD700 !important;
    }
    .match-gold .member-icon { color: #FFD700 !important; } /* 매칭 시 아이콘도 금색 */

    .sun-text { color: #FF4B4B !important; }
    div[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #FF4B4B 0%, #800000 100%) !important;
        color: white !important; height: 50px !important; border-radius: 8px !important; font-weight: 900 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 처리 및 매칭 로직 (동일) ---
def get_worksheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client = gspread.authorize(creds)
        return client.open("AION2_Raid_Data").sheet1
    except: return None

@st.cache_data(ttl=5)
def load_data():
    ws = get_worksheet()
    if ws:
        data = pd.DataFrame(ws.get_all_records())
        if not data.empty: data['날짜'] = pd.to_datetime(data['날짜']).dt.date
        return data
    return pd.DataFrame()

def check_8man_match(day_df):
    if len(day_df) < 8: return False
    timeline = np.zeros(48)
    for _, row in day_df.iterrows():
        s, e = int(row['시작']), int(row['종료'])
        if e <= s: e += 24
        timeline[s:e] += 1
    return np.any(timeline >= 8)

df = load_data()
if 'view_date' not in st.session_state:
    st.session_state.view_date = datetime.date(2026, 3, 25)

# --- 3. 사이드바: 입력창 (동일) ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B;'>🛡️ AION2 본부</h1>", unsafe_allow_html=True)
    st.write("---")
    
    reg_date = st.date_input("📅 날짜 선택", st.session_state.view_date)
    name = st.selectbox("👤 대원 선택", MEMBER_LIST)
    
    col1, col2 = st.columns(2)
    with col1: s_time = st.number_input("시작", 0, 23, 22)
    with col2: e_time = st.number_input("종료", 0, 23, 2)
    
    if st.button("🚀 일정 확정"):
        ws = get_worksheet()
        if ws:
            all_data = ws.get_all_values()
            updated_rows = [all_data[0]]
            found = False
            for r in all_data[1:]:
                if r[0] == str(reg_date) and r[1] == name:
                    updated_rows.append([str(reg_date), name, s_time, e_time])
                    found = True
                else: updated_rows.append(r)
            if not found: updated_rows.append([str(reg_date), name, s_time, e_time])
            ws.update('A1', updated_rows)
            st.cache_data.clear()
            st.rerun()

# --- 4. 메인: 달력 (녹색 아이콘 HTML 적용) ---
st.markdown("<h2 style='text-align:center;'>📅 2026년 3월 레이드 현황</h2>", unsafe_allow_html=True)

march_days = [
    [1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14],
    [15, 16, 17, 18, 19, 20, 21], [22, 23, 24, 25, 26, 27, 28],
    [29, 30, 31, 0, 0, 0, 0]
]

summary = {}
if not df.empty:
    for d in df['날짜'].unique():
        day_data = df[df['날짜'] == d]
        summary[d] = {'count': day_data['이름'].nunique(), 'is_match': check_8man_match(day_data)}

st.markdown('<table class="calendar-table"><thead><tr><th class="sun-text">SUN</th><th>MON</th><th>TUE</th><th>WED</th><th>THU</th><th>FRI</th><th>SAT</th></tr></thead></table>', unsafe_allow_html=True)

for week in march_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day != 0:
                cur_date = datetime.date(2026, 3, day)
                info = summary.get(cur_date, {'count': 0, 'is_match': False})
                
                # 매칭 여부에 따라 CSS 클래스 결정
                container_class = "match-gold" if info['is_match'] else ("has-members" if info['count'] > 0 else "")
                
                # [핵심] 인원수 앞 아이콘에 'member-icon' 클래스 부여
                member_label = f"\n\n<span class='member-icon'>👥</span> {info['count']}" if info['count'] > 0 else ""
                match_icon = " 🏆" if info['is_match'] else ""
                
                with st.container():
                    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
                    # Streamlit 버튼 내부 HTML 렌더링을 위해 unsafe_allow_html은 사용할 수 없으므로,
                    # CSS 선택자를 통해 버튼 내부의 텍스트 색상을 제어합니다.
                    # 하지만 Streamlit 버튼은 HTML 태그를 해석하지 않으므로, 
                    # 대신 특정 클래스 하위의 버튼 텍스트 색상을 제어하는 방식을 사용합니다.
                    if st.button(f"{day}\n\n{'👥' if info['count'] > 0 else ''} {info['count'] if info['count'] > 0 else ''}{match_icon}", key=f"d_{day}"):
                        st.session_state.view_date = cur_date
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("<div style='height:95px;'></div>", unsafe_allow_html=True)

# --- 5. 하단: 타임라인 (동일) ---
st.write("---")
sel = st.session_state.view_date
day_df = df[df['날짜'] == sel].copy() if not df.empty else pd.DataFrame()

if not day_df.empty:
    st.markdown(f"### 📊 {sel} 타임라인 " + ("<span style='color:#FFD700;'>[MATCH]</span>" if check_8man_match(day_df) else ""), unsafe_allow_html=True)
    base = datetime.datetime.combine(sel, datetime.time.min)
    def get_end_time(row):
        s, e = int(row['시작']), int(row['종료'])
        return base + datetime.timedelta(days=(1 if e <= s else 0), hours=e)
    day_df['start_dt'] = day_df['시작'].apply(lambda x: base + datetime.timedelta(hours=int(x)))
    day_df['end_dt'] = day_df.apply(get_end_time, axis=1)
    
    fig = px.timeline(day_df, x_start="start_dt", x_end="end_dt", y="이름", color="이름", template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(xaxis=dict(title="", tickformat="%H시"), yaxis=dict(title="", autorange="reversed"), showlegend=False, height=300, margin=dict(l=0, r=20, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("등록된 인원이 없습니다.")
