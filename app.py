import streamlit as st

st.set_page_config(
    page_title="PowerCare Hospital",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 PowerCare Hospital")
st.subheader("신재생 에너지 기반 스마트병원 운영 시뮬레이션")

st.info(
    "이 웹앱은 태양광 발전, ESS, 정전 상황, 비상발전기 작동 여부에 따라 "
    "스마트병원의 의료정보시스템 상태가 어떻게 달라지는지 관찰하기 위한 "
    "과제제출용 시뮬레이션입니다."
)

st.markdown("### 현재 단계")
st.write(" 정상적으로 실행 확인중... ")

st.markdown("### 앞으로 구현할 기능")
st.write("- 날씨 조건에 따른 태양광 발전량 변화")
st.write("- ESS 충전량 및 방전 상태 변화")
st.write("- 정전 발생 시 병원 비상 운영 모드 전환")
st.write("- EMR, PACS, 서버, 환자 모니터링 시스템 상태 변화")
st.write("- 전력 공급 우선순위에 따른 병원 상황 시뮬레이션")
