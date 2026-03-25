import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import matplotlib.pyplot as plt
import numpy as np

# --- 1. 구글 시트 연결 설정 ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["gspread"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Secrets 설정 오류: {e}")
        st.stop()

def load_data():
    client = get_gspread_client()
    try:
        sheet = client.open("AION2_Raid_Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except Exception as e:
        st.error(f"시트 로드 실패: {e}")
        return pd.DataFrame(), None

# --- 2. 페이지 기본 설정 ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")
st.title("⚔️ AION2 8인 레이드 실시간 조율실")

df, sheet = load_data()

# --- 3. 입력 섹션 (사이드바) ---
with st.sidebar:
    st.header("📝 내 일정 등록")
    fixed_year = 2026
    input_date = st.date_input("레이드 날짜 선택", datetime.date(fixed_year, 3, 25))
    date_str = str(input_date)
    
    members = [f"유저{i}" for i in range(1, 9)]
    name = st.selectbox("본인 이름 선택", members)
    time_range = st.select_slider("접속 가능 시간대", options=list(range(25)), value=(20, 23))
    
    if st.button("🚀 일정 확정 (시트 저장)"):
        if sheet is not None:
            if not df.empty:
                all_values = sheet.get_all_values()
                for i, row in enumerate(all_values):
                    if row[0] == date_str and row[1] == name:
                        sheet.delete_rows(i + 1)
            sheet.append_row([date_str, name, time_range[0], time_range[1]])
            st.success(f"✅ {name}님 저장 완료!")
            st.rerun()

# --- 4. 메인 현황판 (2026년 달력) ---
st.write("---")
cal_year, cal_month = input_date.year, input_date.month
st.subheader(f"📅 {cal_year}년 {cal_month}월 일정표")

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')
    cal = calendar.monthcalendar(cal_year, cal_month)
    days = ["일", "월", "화", "수", "목", "금", "토"]
    cols_h = st.columns(7)
    for i, d in enumerate(days): cols_h[i].markdown(f"<p style='text-align:center; color:#FF4B4B;'><b>{d}</b></p>", unsafe_allow_html=True)

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                t_date = datetime.date(cal_year, cal_month, day)
                cnt = summary[summary['날짜'] == t_date]['인원'].values[0] if not summary[summary['날짜'] == t_date].empty else 0
                icon = "🔥" if cnt >= 8 else "✅" if cnt > 0 else "⚪"
                if cols[i].button(f"{day}\n({icon}{cnt}명)", key=f"d_{day}", use_container_width=True, type="primary" if t_date == input_date else "secondary"):
                    st.session_state.selected_date = t_date

# --- 5. 상세 참여 현황 (정밀 시계형 차트) ---
st.write("---")
display_date = st.session_state.get('selected_date', input_date)
st.markdown(f"### 🔍 {display_date} 24시 정밀 조율 시계")

day_df = df[df['날짜'] == display_date]

if not day_df.empty:
    # --- Matplotlib을 이용한 정밀 원형 시계 생성 ---
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
    ax.set_theta_direction(-1) # 시계 방향
    ax.set_theta_offset(np.pi/2.0) # 0시를 12시 방향으로

    # 24시간 눈금 설정
    hours = np.arange(0, 24, 1)
    theta = np.linspace(0, 2*np.pi, 25)
    ax.set_xticks(np.linspace(0, 2*np.pi, 24, endpoint=False))
    ax.set_xticklabels([f"{h}시" for h in hours], fontsize=10, color="white")
    
    # 대원별 시간 표시 (동심원 형태로 층을 쌓음)
    for i, (idx, row) in enumerate(day_df.iterrows()):
        start_rad = (row['시작'] / 24) * 2 * np.pi
        end_rad = (row['종료'] / 24) * 2 * np.pi
        # 각 대원마다 반지름 위치를 다르게 해서 겹침 방지
        r = [0.4 + (i * 0.07), 0.4 + (i * 0.07)]
        ax.plot([start_rad, end_rad], r, lw=6, label=row['이름'], solid_capstyle='round')
        ax.text(start_rad, r[0], row['이름'], fontsize=8, color="white")

    ax.set_yticklabels([]) # 반지름 숫자 제거
    ax.set_rmax(1.1)
    ax.grid(True, alpha=0.3)
    fig.patch.set_facecolor('#0E1117') # Streamlit 다크모드 배경색
    ax.set_facecolor('#0E1117')
    
    st.pyplot(fig)
    
    if len(day_df) >= 8:
        st.balloons()
        st.success("🔥 8인 매칭 완료! 위 시계에서 겹치는 구간을 확인하세요!")
else:
    st.info("등록된 인원이 없습니다.")

st.caption("AION2 RAID - 정밀 24시 레이어드 클락")
