import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import datetime

# --- 1. 구글 시트 연결 설정 ---
def get_gspread_client():
    # Streamlit Secrets에 저장된 [gspread] 정보를 읽어옵니다.
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gspread"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def load_data():
    client = get_gspread_client()
    # 공대장님의 구글 시트 이름을 정확히 입력하세요 (예: "AION2_Raid_Data")
    # 시트 이름이 다르면 여기서 수정해야 합니다.
    try:
        sheet = client.open("AION2_Raid_Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except Exception as e:
        st.error(f"시트를 찾을 수 없습니다: {e}")
        return pd.DataFrame(), None

# --- 2. 페이지 기본 설정 ---
st.set_page_config(page_title="AION2 레이드 조율실", layout="wide")
st.title("⚔️ AION2 8인 레이드 실시간 조율실")

# 데이터 불러오기
df, sheet = load_data()

# --- 3. 입력 섹션 (사이드바) ---
with st.sidebar:
    st.header("📝 일정 등록/수정")
    # 날짜 선택 (기본값 오늘)
    input_date = st.date_input("레이드 날짜 선택", datetime.date.today())
    date_str = str(input_date)
    
    # 공격대원 명단 (필요시 수정 가능)
    members = [f"유저{i}" for i in range(1, 9)]
    name = st.selectbox("본인 이름 선택", members)
    
    # 시간 선택 슬라이더 (0시 ~ 24시)
    time_range = st.select_slider(
        "접속 가능 시간대",
        options=list(range(25)),
        value=(20, 23)
    )
    
    if st.button("🚀 일정 확정 (시트 저장)"):
        if sheet is not None:
            # 중복 데이터 삭제 로직: 동일 날짜 + 동일 유저 데이터가 있으면 제거
            if not df.empty:
                # 시트의 모든 데이터를 가져와서 유저 이름과 날짜가 일치하는 행 탐색
                all_values = sheet.get_all_values()
                for i, row in enumerate(all_values):
                    if row[0] == date_str and row[1] == name:
                        sheet.delete_rows(i + 1) # 해당 행 삭제
            
            # 새로운 데이터 추가 (날짜, 이름, 시작, 종료)
            sheet.append_row([date_str, name, time_range[0], time_range[1]])
            st.success(f"✅ {name}님 {date_str} 일정 저장 완료!")
            st.rerun() # 화면 새로고침하여 그래프 업데이트
        else:
            st.error("시트 연결에 실패하여 저장할 수 없습니다.")

# --- 4. 메인 현황판 섹션 ---
st.subheader(f"📅 {date_str} 참여 현황")

if not df.empty:
    # 현재 선택한 날짜의 데이터만 필터링
    current_day_df = df[df['날짜'].astype(str) == date_str]
    
    if not current_day_df.empty:
        # 타임라인 그래프 시각화
        fig = px.timeline(
            current_day_df, 
            x_start="시작", 
            x_end="종료", 
            y="이름", 
            color="이름",
            template="plotly_dark"
        )
        
        # 그래프 가독성 조절 (시간 축 설정)
        fig.update_layout(
            xaxis=dict(
                title="시간 (0시~24시)", 
                tickvals=list(range(25)),
                range=[0, 24]
            ),
            yaxis=dict(title="대원명", autorange="reversed"),
            showlegend=False,
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 인원수 체크 및 알림
        count = len(current_day_df)
        if count >= 8:
            st.balloons()
            st.success(f"🔥 축하합니다! {date_str}에 8명 풀파티 매칭 완료!")
        else:
            st.info(f"💡 현재 {count}명 등록 중입니다. (8인까지 {8-count}명 남음)")
    else:
        st.info("해당 날짜에 등록된 일정이 없습니다. 왼쪽에서 첫 일정을 등록해 보세요!")
else:
    st.warning("데이터베이스(시트)가 비어있습니다.")

st.write("---")
st.caption("AION2 RAID SCHEDULER - 데이터 실시간 동기화 모드")
