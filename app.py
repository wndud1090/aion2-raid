import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

# --- 1. 페이지 설정 및 프리미엄 밀착형 그리드 CSS ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")

st.markdown("""
    <style>
    /* 배경 및 기본 폰트 */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* [핵심] 컬럼 간격 및 여백 완전 제거 (4분의 1로 축소 효과) */
    div[data-testid="stColumn"] {
        padding: 0px !important;
        margin: 0px !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0 !important;
    }

    /* 프리미엄 버튼 디자인: 컬럼에 꽉 차게 밀착 */
    .stButton > button {
        width: 100% !important;
        height: 120px !important; /* 높이 고정으로 정사각형 그리드 유지 */
        margin: 0 !important;
        padding: 0 !important;
        border-radius: 0px !important; /* 각진 그리드 스타일 */
        border: 1px solid #262730 !important; /* 미세한 경계선 */
        background-color: #161920 !important;
        color: #888 !important;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* 호버 시 효과 */
    .stButton > button:hover {
        background-color: #262730 !important;
        border: 1px solid #FF4B4B !important;
        z-index: 10; /* 테두리 강조 */
    }

    /* 데이터가 있는 날짜: 네온 블루 하이라이트 (가독성 유지) */
    .has-data > div > div > button {
        background-color: #1c2533 !important;
        color: #00FBFF !important;
        border: 1px solid #00FBFF !important;
    }
    .has-data > div > div > button p {
        font-weight: 900 !important;
        font-size: 1.1rem !important; /* 인원수 글자 크게 유지 */
    }

    /* 선택된 날짜 강조 (AION2 레드) */
    .selected-date > div > div > button {
        border: 2px solid #FF4B4B !important;
        background-color: #2D1A1E !important;
        color: #FF4B4B !important;
    }

    /* 요일 헤더 디자인 */
    .day-header {
        text-align: center;
        font-weight: 900;
        background-color: #1a1d24;
        padding: 10px 0;
        border: 1px solid #262730;
        color: #aaa;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=10) # 10초마다 데이터 갱신
def load_data():
    client = get_gspread_client()
    try:
        # 시트 이름을 공대장님의 실제 시트 이름과 일치시키세요.
        sheet = client.open("AION2_Raid_Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except Exception as e:
        return pd.DataFrame(), None

df, sheet = load_data()

# --- 3. 사이드바 (등록 섹션) ---
with st.sidebar:
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>🛡️ AION2</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>공격대 조율 시스템</p>", unsafe_allow_html=True)
    st.write("---")
    
    fixed_year = 2026
    # 공대장님 요청대로 2026년 날짜로 기본값 설정
    input_date = st.date_input("📅 레이드 날짜 선택", datetime.date(fixed_year, 3, 25))
    date_str = str(input_date)
    
    members = [f"유저{i}" for i in range(1, 9)]
    name = st.selectbox("👤 본인 이름 선택", members)
    
    # 시간 선택 슬라이더
    time_range = st.select_slider(
        "⏰ 접속 가능 시간대 (시)",
        options=list(range(25)),
        value=(20, 23)
    )
    
    if st.button("🚀 일정 확정 (시트 저장)"):
        if sheet is not None:
            # 중복 데이터 삭제 (같은 날짜 + 같은 이름)
            if not df.empty:
                all_values = sheet.get_all_values()
                for i, row in enumerate(all_values):
                    if len(row) >= 2 and row[0] == date_str and row[1] == name:
                        sheet.delete_rows(i + 1)
            
            # 새 데이터 추가
            sheet.append_row([date_str, name, time_range[0], time_range[1]])
            st.success(f"✅ {name}님 저장 완료!")
            st.rerun()

# --- 4. 메인 현황판 (밀착형 격자 달력) ---
st.title("AION2 공격대 실시간 현황")
# 공대장님이 선택한 날짜의 연/월을 기준으로 달력 표시
cal_year, cal_month = input_date.year, input_date.month
st.subheader(f"📅 {cal_year}년 {cal_month}월 일정표")

if not df.empty:
    # 데이터 전처리
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')

    # 해당 연/월의 달력 배열 생성
    cal = calendar.monthcalendar(cal_year, cal_month)

    # 요일 헤더 (심플 디자인)
    days = ["일", "월", "화", "수", "목", "금", "토"]
    h_cols = st.columns(7)
    for i, d in enumerate(days):
        color = "#FF4B4B" if i == 0 else "#E0E0E0"
        h_cols[i].markdown(f"<div class='day-header' style='color:{color};'>{d}</div>", unsafe_allow_html=True)

    # 달력 격자 생성 (빈틈없이 채우기)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("<div style='height:120px; background-color:#0E1117; border:0.5px solid #161920;'></div>", unsafe_allow_html=True)
            else:
                t_date = datetime.date(cal_year, cal_month, day)
                count_row = summary[summary['날짜'] == t_date]
                count = count_row['인원'].values[0] if not count_row.empty else 0
                
                # 상태에 따른 CSS 클래스 부여
                c_class = ""
                if count > 0: c_class = "has-data"
                if t_date == input_date: c_class = "selected-date"
                
                # 버튼 레이블 구성 (가독성 유지)
                label = f"{day}\n\n{f'👥 {count}명' if count > 0 else ''}"
                
                with cols[i]:
                    st.markdown(f"<div class='{c_class}'>", unsafe_allow_html=True)
                    if st.button(label, key=f"d_{day}"):
                        # 달력의 날짜를 누르면 사이드바의 날짜도 바뀜 (세션 저장 필요 시 추가)
                        st.session_state.selected_date = t_date
                    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. 상세 타임라인 ---
st.write("---")
# 사이드바에서 선택한 날짜 또는 달력에서 클릭한 날짜를 우선으로 보여줌
display_date = input_date
if 'selected_date' in st.session_state:
    display_date = st.session_state.selected_date

st.markdown(f"### 📊 {display_date} 상세 타임라인")

day_df = df[df['날짜'] == display_date]

if not day_df.empty:
    # Plotly용 데이터 정리
    def to_dt(h):
        # 24시는 다음 날 0시로 처리하여 에러 방지
        if h == 24: return datetime.datetime(2026, 1, 2, 0, 0)
        return datetime.datetime(2026, 1, 1, int(h), 0)

    fig = px.timeline(
        day_df, 
        x_start=day_df['시작'].apply(to_dt),
        x_end=day_df['종료'].apply(to_dt),
        y="이름", color="이름",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_layout(
        xaxis=dict(title="접속 시간", tickformat="%H시", dtick=3600000 * 2), # 2시간 간격
        yaxis=dict(title="", autorange="reversed", tickfont=dict(size=20, color="white")), # 이름 폰트 크게
        showlegend=False, height=400, margin=dict(l=0, r=20, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("해당 날짜에 등록된 대원이 없습니다.")

st.caption("AION2 RAID - 2026년 프리미엄 밀착형 그리드")
