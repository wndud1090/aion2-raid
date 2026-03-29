import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import timedelta, timezone
import calendar
import numpy as np

# [1] 시스템 설정
calendar.setfirstweekday(calendar.SUNDAY)
KST = timezone(timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
today = datetime.date(2026, now_kst.month, now_kst.day)

st.set_page_config(page_title="AION2 RAID HQ", layout="wide")

# [2] 완전히 새로운 시각적 아이덴티티 (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* 전체 테마 배경 */
    .stApp { background: #080808; font-family: 'Inter', sans-serif; }
    
    /* 캘린더 컨테이너 */
    .cal-wrapper {
        background: #111;
        border: 1px solid #222;
        border-radius: 24px;
        padding: 30px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }

    /* 요일 헤더 디자인 */
    .weekday-row {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        margin-bottom: 15px;
        border-bottom: 1px solid #222;
        padding-bottom: 10px;
    }
    .weekday-item {
        text-align: center;
        font-size: 0.75rem;
        font-weight: 800;
        color: #444;
        letter-spacing: 1px;
    }

    /* 날짜 그리드 */
    .date-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 12px;
    }

    /* 날짜 타일 - 버튼이 아닌 아트보드 개념 */
    .date-tile {
        background: #181818;
        border: 1px solid #282828;
        border-radius: 16px;
        aspect-ratio: 1 / 1;
        position: relative;
        padding: 12px;
        transition: 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        overflow: hidden;
    }

    /* 호버 효과: 버튼이 아닌 살아있는 오브젝트 느낌 */
    .date-tile:hover {
        background: #222;
        border-color: #ff4b4b;
        transform: scale(1.05);
        z-index: 10;
    }

    .date-num { font-size: 1.2rem; font-weight: 600; color: #555; }
    .status-dot {
        width: 6px; height: 6px;
        background: #00ff88;
        border-radius: 50%;
        margin-top: 8px;
    }

    /* 매칭 성공 시: 압도적인 골드 테마 */
    .match-gold {
        background: linear-gradient(145deg, #1a1608, #0a0a0a) !important;
        border: 1px solid #ffd700 !important;
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.15);
    }
    .match-gold .date-num { color: #ffd700; }
    .match-gold::before {
        content: '';
        position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,215,0,0.05) 0%, transparent 70%);
    }

    /* 오늘 날짜 표시 */
    .today-marker { border: 1.5px solid #ff4b4b !important; }

    /* 스트림릿 버튼 투명화 (타일 위에 덮어씌움) */
    .stButton > button {
        position: absolute; top: 0; left: 0; width: 100% !important; height: 100% !important;
        background: transparent !important; border: none !important; color: transparent !important;
        z-index: 100;
    }
    </style>
    """, unsafe_allow_html=True)

# [3] 데이터 및 멤버 로드
def get_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client = gspread.authorize(creds)
        doc = client.open("AION2_Raid_Data")
        return doc.get_worksheet(0), doc.get_worksheet(1)
    except: return None, None

@st.cache_data(ttl=5)
def load_all():
    s1, s2 = get_sheets()
    df = pd.DataFrame(s1.get_all_records()) if s1 else pd.DataFrame()
    if not df.empty: df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    members = s2.col_values(1)[1:] if s2 else ["공대장"]
    return df, members

df, MEMBER_LIST = load_all()

def is_8man(day_df):
    if len(day_df) < 8: return False
    time_slots = np.zeros(48)
    for _, r in day_df.iterrows():
        s, e = int(r['시작']), int(r['종료'])
        if e <= s: e += 24
        time_slots[s:e] += 1
    return np.any(time_slots >= 8)

# [4] 고품격 캘린더 엔진
def draw_premium_calendar(year, month, data_df):
    st.markdown(f"<h1 style='text-align:center; color:#fff; font-weight:800; letter-spacing:-1px;'>{year} / {month}</h1>", unsafe_allow_html=True)
    
    st.markdown('<div class="cal-wrapper">', unsafe_allow_html=True)
    
    # 요일 헤더
    st.markdown("""
        <div class="weekday-row">
            <div class="weekday-item" style="color:#ff4b4b">SUN</div>
            <div class="weekday-item">MON</div><div class="weekday-item">TUE</div>
            <div class="weekday-item">WED</div><div class="weekday-item">THU</div>
            <div class="weekday-item">FRI</div><div class="weekday-item">SAT</div>
        </div>
    """, unsafe_allow_html=True)

    cal = calendar.monthcalendar(year, month)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
                continue
            
            target = datetime.date(year, month, day)
            day_data = data_df[data_df['날짜'] == target] if not data_df.empty else pd.DataFrame()
            count = day_data['이름'].nunique()
            matched = is_8man(day_data)
            
            # 스타일 태그 조합
            tile_class = "date-tile"
            if matched: tile_class += " match-gold"
            if target == today: tile_class += " today-marker"
            
            with cols[i]:
                # 1. 시각적 타일 레이어
                st.markdown(f"""
                    <div class="{tile_class}">
                        <div class="date-num">{day}</div>
                        {"<div class='status-dot'></div>" if count > 0 else ""}
                        <div style="position:absolute; bottom:12px; right:12px; font-size:0.7rem; color:#666;">
                            {f"👥 {count}" if count > 0 else ""}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 2. 기능적 투명 버튼 레이어 (타일 위에 덮음)
                if st.button("", key=f"t-{year}-{month}-{day}"):
                    st.session_state.target_date = target
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# [5] 메인 인터페이스
if 'target_date' not in st.session_state: st.session_state.target_date = today

m1 = today.replace(day=1)
m2 = (m1 + timedelta(days=32)).replace(day=1)

c_l, c_r = st.columns(2)
with c_l: draw_premium_calendar(m1.year, m1.month, df)
with c_r: draw_premium_calendar(m2.year, m2.month, df)

# 하단 컨트롤 센터 (Dashboard 컨셉)
st.markdown("<br><br>", unsafe_allow_html=True)
l_col, r_col = st.columns([1, 2.5])

with l_col:
    st.markdown(f"### 📍 FOCUS: {st.session_state.target_date}")
    with st.container(border=True):
        u_name = st.selectbox("OPERATOR", MEMBER_LIST)
        u_start = st.slider("START TIME", 0, 23, 22)
        u_end = st.slider("END TIME", 0, 23, 2)
        if st.button("CONFIRM SCHEDULE", use_container_width=True):
            s1, _ = get_sheets()
            if s1:
                all_v = s1.get_all_values()
                new_rows = [all_v[0]]
                f = False
                for r in all_v[1:]:
                    if r[0] == str(st.session_state.target_date) and r[1] == u_name:
                        new_rows.append([str(st.session_state.target_date), u_name, u_start, u_end]); f = True
                    else: new_rows.append(r)
                if not f: new_rows.append([str(st.session_state.target_date), u_name, u_start, u_end])
                s1.update('A1', new_rows)
                st.cache_data.clear(); st.rerun()

with r_col:
    sel_df = df[df['날짜'] == st.session_state.target_date]
    if not sel_df.empty:
        st.markdown(f"### 🛡️ ACTIVE MEMBERS ({len(sel_df)})")
        st.dataframe(sel_df[['이름', '시작', '종료']], hide_index=True, use_container_width=True)
    else:
        st.markdown("<div style='height:200px; display:flex; align-items:center; justify-content:center; border:1px dashed #333; border-radius:15px; color:#555;'>NO ACTIVE SCHEDULE</div>", unsafe_allow_html=True)
