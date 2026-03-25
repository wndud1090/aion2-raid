import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
import plotly.express as px

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
        # 시트 이름을 공대장님의 실제 시트 이름과 일치시키세요.
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
    # 공대장님 요청대로 2026년 날짜로 기본값 설정
    input_date = st.date_input("레이드 날짜 선택", datetime.date(fixed_year, 3, 25))
    date_str = str(input_date)
    
    members = [f"유저{i}" for i in range(1, 9)]
    name = st.selectbox("본인 이름 선택", members)
    time_range = st.select_slider("접속 가능 시간대 (시)", options=list(range(25)), value=(20, 23))
    
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
    for i, d in enumerate(days):
        cols_h[i].markdown(f"<p style='text-align:center; color:#FF4B4B;'><b>{d}</b></p>", unsafe_allow_html=True)

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                t_date = datetime.date(cal_year, cal_month, day)
                cnt_row = summary[summary['날짜'] == t_date]
                cnt = cnt_row['인원'].values[0] if not cnt_row.empty else 0
                icon = "🔥" if cnt >= 8 else "✅" if cnt > 0 else "⚪"
                
                # 달력 버튼
                if cols[i].button(f"{day}\n({icon}{cnt}명)", key=f"d_{day}", use_container_width=True, 
                                  type="primary" if t_date == input_date else "secondary"):
                    st.session_state.selected_date = t_date

# --- 5. 상세 참여 현황 (가로 바 타임라인) ---
st.write("---")
display_date = st.session_state.get('selected_date', input_date)
st.markdown(f"### 📊 {display_date} 시간대별 겹침 확인")

day_df = df[df['날짜'] == display_date]

if not day_df.empty:
    # Plotly용 데이터 정리 (가로 바 형식)
    fig = px.timeline(
        day_df, 
        x_start=day_df['시작'].apply(lambda x: datetime.datetime(2026, 1, 1, int(x))),
        x_end=day_df['종료'].apply(lambda x: datetime.datetime(2026, 1, 1, int(x))),
        y="이름",
        color="이름",
        text="이름",
        labels={"이름": "공격대원"},
        template="plotly_dark"
    )

    # X축(시간) 설정: 0시부터 24시까지 명확하게 표시
    fig.update_layout(
        xaxis=dict(
            title="접속 시간 (시)",
            tickformat="%H시",
            dtick=3600000, # 1시간 간격 (밀리초)
            range=[datetime.datetime(2026, 1, 1, 0), datetime.datetime(2026, 1, 1, 24)]
        ),
        yaxis=dict(title="대원 명단", autorange="reversed"),
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 인원수 체크
    count = len(day_df)
    if count >= 8:
        st.balloons()
        st.success(f"🔥 현재 8명 풀파티! 위 그래프에서 세로로 꽉 찬 시간대에 출발하세요!")
    else:
        st.warning(f"현재 {count}명 대기 중 (8인까지 {8-count}명 남음)")
else:
    st.info("이날은 아직 등록된 일정이 없습니다.")

st.caption("AION2 RAID - 가로 바 타임라인 시스템")
