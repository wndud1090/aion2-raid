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
    # 시트 이름을 공대장님의 실제 시트 이름으로 정확히 수정하세요.
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

# 데이터 불러오기
df, sheet = load_data()

# --- 3. 입력 섹션 (사이드바) ---
with st.sidebar:
    st.header("📝 내 일정 등록")
    # 날짜 선택
    input_date = st.date_input("레이드 날짜 선택", datetime.date.today())
    date_str = str(input_date)
    
    # 공격대원 명단 (유저1~8)
    members = [f"유저{i}" for i in range(1, 9)]
    name = st.selectbox("본인 이름 선택", members)
    
    # 시간 선택 슬라이더
    time_range = st.select_slider(
        "접속 가능 시간대 (시)",
        options=list(range(25)),
        value=(20, 23)
    )
    
    if st.button("🚀 일정 확정 (시트 저장)"):
        if sheet is not None:
            # 중복 데이터 삭제 (같은 날짜 + 같은 이름)
            if not df.empty:
                all_values = sheet.get_all_values()
                for i, row in enumerate(all_values):
                    if row[0] == date_str and row[1] == name:
                        sheet.delete_rows(i + 1)
            
            # 새 데이터 추가
            sheet.append_row([date_str, name, time_range[0], time_range[1]])
            st.success(f"✅ {name}님 저장 완료!")
            st.rerun()

# --- 4. 메인 현황판 (달력 뷰) ---
st.write("---")
st.subheader(f"📅 {datetime.date.today().month}월 레이드 일정표")

if not df.empty:
    # 데이터 전처리
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    summary = df.groupby('날짜').size().reset_index(name='인원')

    # 현재 달 계산
    today = datetime.date.today()
    cal = calendar.monthcalendar(today.year, today.month)

    # 달력 헤더
    days = ["일", "월", "화", "수", "목", "금", "토"]
    cols_header = st.columns(7)
    for i, d in enumerate(days):
        cols_header[i].markdown(f"<p style='text-align:center'><b>{d}</b></p>", unsafe_allow_html=True)

    # 달력 본문 생성
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                target_date = datetime.date(today.year, today.month, day)
                count_row = summary[summary['날짜'] == target_date]
                count = count_row['인원'].values[0] if not count_row.empty else 0
                
                # 상태 아이콘 및 색상 설정
                status_icon = "🔥" if count >= 8 else "✅" if count > 0 else "⚪"
                
                # 날짜 버튼 생성 (클릭 시 세션에 저장)
                with cols[i]:
                    button_label = f"{day}\n({status_icon}{count}명)"
                    if st.button(button_label, key=f"d_{day}", use_container_width=True):
                        st.session_state.selected_date = target_date

# --- 5. 선택한 날짜 상세 명단 (표) ---
st.write("---")
if 'selected_date' in st.session_state:
    sel_date = st.session_state.selected_date
    st.markdown(f"### 🔍 {sel_date} 상세 참여 현황")
    
    # 해당 날짜 데이터만 필터링
    day_df = df[df['날짜'] == sel_date].sort_values(by='시작')
    
    if not day_df.empty:
        # 가독성 좋은 표로 출력
        display_df = day_df[['이름', '시작', '종료']].copy()
        display_df.columns = ['대원명', '시작 시간(시)', '종료 시간(시)']
        st.table(display_df)
        
        # 8명 달성 여부 표시
        if len(day_df) >= 8:
            st.balloons()
            st.success("🔥 8인 풀파티 매칭 완료! 레이드 출발!")
        else:
            st.warning(f"현재 {len(day_df)}명 등록됨 (8명까지 {8-len(day_df)}명 부족)")
    else:
        st.info("해당 날짜에 등록된 인원이 없습니다.")
else:
    st.info("위 달력에서 날짜를 클릭하면 상세 명단을 볼 수 있습니다.")

st.write("---")
st.caption("AION2 RAID - 사람이 편한 달력형 조율 시스템")
