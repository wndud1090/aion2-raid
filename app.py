import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar

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
        # 시트 이름을 실제 이름과 대조하세요.
        sheet = client.open("AION2_Raid_Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except Exception as e:
        st.error(f"시트 로드 실패: {e}")
        return pd.DataFrame(), None

# --- 2. 페이지 기본 설정 ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")
st.title("⚔️ AION2 8인 레이드 실시간 조율실")

# 데이터 불러오기
df, sheet = load_data()

# --- 3. 입력 섹션 (사이드바) ---
with st.sidebar:
    st.header("📝 내 일정 등록")
    # 현재 연도를 2026년으로 명시적 고정
    fixed_year = 2026
    input_date = st.date_input("레이드 날짜 선택", datetime.date(fixed_year, 3, 25))
    date_str = str(input_date)
    
    members = [f"유저{i}" for i in range(1, 9)]
    name = st.selectbox("본인 이름 선택", members)
    
    time_range = st.select_slider(
        "접속 가능 시간대 (시)",
        options=list(range(25)),
        value=(20, 23)
    )
    
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

# --- 4. 메인 현황판 (2026년 달력 뷰) ---
st.write("---")
# 공대장님이 선택한 날짜의 연/월을 기준으로 달력 표시
cal_year = input_date.year
cal_month = input_date.month

st.subheader(f"📅 {cal_year}년 {cal_month}월 레이드 일정표")

if not df.empty:
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')

    # 해당 연/월의 달력 배열 생성
    cal = calendar.monthcalendar(cal_year, cal_month)

    # 달력 헤더 (일~토)
    days = ["일", "월", "화", "수", "목", "금", "토"]
    cols_header = st.columns(7)
    for i, d in enumerate(days):
        cols_header[i].markdown(f"<p style='text-align:center; color:#FF4B4B;'><b>{d}</b></p>", unsafe_allow_html=True)

    # 달력 본문 생성
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                target_date = datetime.date(cal_year, cal_month, day)
                count_row = summary[summary['날짜'] == target_date]
                count = count_row['인원'].values[0] if not count_row.empty else 0
                
                # 아이콘 설정
                status_icon = "🔥" if count >= 8 else "✅" if count > 0 else "⚪"
                
                # 버튼 색상 및 강조 (선택된 날짜 강조)
                is_selected = "primary" if target_date == input_date else "secondary"
                
                with cols[i]:
                    button_label = f"{day}\n({status_icon}{count}명)"
                    if st.button(button_label, key=f"d_{day}", use_container_width=True, type=is_selected):
                        # 달력의 날짜를 누르면 사이드바의 날짜도 바뀔 수 있게 유도 (세션 저장)
                        st.session_state.selected_date = target_date

# --- 5. 상세 참여 현황 ---
st.write("---")
# 사이드바 입력 날짜를 우선으로 보여줌
display_date = input_date
if 'selected_date' in st.session_state:
    # 달력에서 버튼을 눌렀다면 그 날짜를 우선시함
    display_date = st.session_state.selected_date

st.markdown(f"### 🔍 {display_date} 상세 참여 현황")
day_df = df[df['날짜'] == display_date].sort_values(by='시작')

if not day_df.empty:
    display_df = day_df[['이름', '시작', '종료']].copy()
    display_df.columns = ['대원명', '시작 시간(시)', '종료 시간(시)']
    st.table(display_df)
    
    if len(day_df) >= 8:
        st.balloons()
        st.success("🔥 8인 풀파티 매칭 완료!")
    else:
        st.warning(f"현재 {len(day_df)}명 등록됨 (8명까지 {8-len(day_df)}명 부족)")
else:
    st.info("해당 날짜에 등록된 인원이 없습니다.")

st.write("---")
st.caption("AION2 RAID - 2026년 정밀 동기화 모드")
