import streamlit as st

# =========================
# 1. 기본 설정
# =========================

st.set_page_config(
    page_title="PowerCare Hospital",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 PowerCare Hospital")
st.caption("신재생 에너지 기반 스마트병원 운영 시뮬레이션")

st.info(
    "본 프로그램은 신재생 에너지와 의료정보시스템 안정성의 관계를 이해하기 위해 제작한 "
    "교육용 시뮬레이션입니다. 시스템별 전력량과 운영 상태는 탐구 목적에 맞게 설정한 "
    "가상 조건이며, 실제 병원의 비상전력 설계 기준과는 다를 수 있습니다."
)

# =========================
# 2. 조건 조절 패널
# =========================

st.sidebar.header("⚙️ 상황 조절 패널")

weather = st.sidebar.selectbox(
    "날씨 조건",
    ["맑음", "구름 조금", "흐림", "야간"]
)

power_status = st.sidebar.radio(
    "외부 전력 상태",
    ["정상", "정전"]
)

ess_level = st.sidebar.slider(
    "ESS 현재 충전율 (%)",
    min_value=0,
    max_value=100,
    value=70,
    step=5
)

backup_generator = st.sidebar.checkbox(
    "비상발전기 작동",
    value=False
)

strategy = st.sidebar.selectbox(
    "전력 공급 전략",
    ["환자 안전 우선", "전체 균등 공급", "영상 진단 우선"]
)

# =========================
# 3. 날씨별 태양광 발전 상태
# =========================

weather_factor = {
    "맑음": 100,
    "구름 조금": 70,
    "흐림": 30,
    "야간": 0
}

solar_power = weather_factor[weather]

# =========================
# 4. 화면 레이아웃
# =========================

col1, col2, col3 = st.columns([1.1, 1.4, 1.2])

# =========================
# 5. 현재 조건 표시
# =========================

with col1:
    st.subheader("🌤️ 현재 조건")

    st.metric("날씨", weather)
    st.metric("태양광 발전 상태", f"{solar_power}%")
    st.metric("외부 전력", power_status)
    st.metric("ESS 충전율", f"{ess_level}%")

    if backup_generator:
        st.success("비상발전기: 작동 중")
    else:
        st.warning("비상발전기: 작동 안 함")

# =========================
# 6. 에너지 흐름 상황판
# =========================

with col2:
    st.subheader("🔋 에너지 흐름 상황판")

    if weather == "맑음":
        solar_icon = "☀️"
        solar_status = "태양광 발전이 원활하게 이루어지고 있습니다."
    elif weather == "구름 조금":
        solar_icon = "⛅"
        solar_status = "태양광 발전량이 일부 감소했습니다."
    elif weather == "흐림":
        solar_icon = "☁️"
        solar_status = "태양광 발전량이 크게 감소했습니다."
    else:
        solar_icon = "🌙"
        solar_status = "야간에는 태양광 발전이 이루어지지 않습니다."

    st.markdown(f"### {solar_icon} 태양광 발전")
    st.progress(solar_power / 100)
    st.write(solar_status)

    st.markdown("### 🔋 ESS 저장장치")
    st.progress(ess_level / 100)

    if power_status == "정상":
        st.success("외부 전력이 정상 공급되고 있습니다.")
        if solar_power > 50:
            st.write("태양광 발전량이 충분하여 ESS 충전에 활용될 수 있습니다.")
        else:
            st.write("태양광 발전량이 낮아 외부 전력 의존도가 높습니다.")
    else:
        st.error("외부 전력이 차단되어 병원이 비상 운영 상태입니다.")
        st.write("ESS 저장 전력과 비상발전기 작동 여부가 중요해집니다.")

# =========================
# 7. 의료정보시스템 상태 판단
# =========================

def get_system_status(system_name, ess, power, generator, strategy_name):
    """
    입력 조건에 따라 의료정보시스템의 상태를 단순화하여 판단하는 함수.
    실제 병원 기준이 아니라 교육용 시뮬레이션 규칙이다.
    """

    if power == "정상":
        return "🟢 정상 운영"

    # 정전 상태에서 비상발전기가 작동하면 핵심 시스템 안정
    if generator:
        if system_name in ["환자 모니터링", "EMR", "서버·네트워크"]:
            return "🟢 정상 운영"
        elif system_name == "PACS":
            return "🟡 제한 운영"
        else:
            return "🟠 중단 위험"

    # 정전 + 비상발전기 없음
    if strategy_name == "환자 안전 우선":
        if ess >= 50:
            priority = {
                "환자 모니터링": "🟢 정상 운영",
                "EMR": "🟢 정상 운영",
                "서버·네트워크": "🟢 정상 운영",
                "PACS": "🟡 제한 운영",
                "일반 행정": "🔴 중단"
            }
        elif ess >= 25:
            priority = {
                "환자 모니터링": "🟢 정상 운영",
                "EMR": "🟡 제한 운영",
                "서버·네트워크": "🟡 제한 운영",
                "PACS": "🔴 중단",
                "일반 행정": "🔴 중단"
            }
        else:
            priority = {
                "환자 모니터링": "🟠 중단 위험",
                "EMR": "🟠 중단 위험",
                "서버·네트워크": "🟠 중단 위험",
                "PACS": "🔴 중단",
                "일반 행정": "🔴 중단"
            }
        return priority[system_name]

    if strategy_name == "전체 균등 공급":
        if ess >= 60:
            return "🟡 제한 운영"
        elif ess >= 30:
            return "🟠 중단 위험"
        else:
            return "🔴 중단"

    if strategy_name == "영상 진단 우선":
        if system_name in ["PACS", "서버·네트워크"] and ess >= 40:
            return "🟢 정상 운영"
        elif system_name in ["환자 모니터링", "EMR"] and ess >= 40:
            return "🟡 제한 운영"
        else:
            return "🔴 중단"

# =========================
# 8. 의료정보시스템 상태 화면
# =========================

with col3:
    st.subheader("🏥 의료정보시스템 상태")

    systems = [
        "환자 모니터링",
        "EMR",
        "서버·네트워크",
        "PACS",
        "일반 행정"
    ]

    for system in systems:
        status = get_system_status(
            system,
            ess_level,
            power_status,
            backup_generator,
            strategy
        )
        st.write(f"**{system}** : {status}")

# =========================
# 9. 현재 상황 알림
# =========================

st.divider()
st.subheader("📢 현재 상황 알림")

if power_status == "정상":
    if solar_power >= 70:
        st.success("현재는 외부 전력과 태양광 발전이 함께 활용될 수 있는 안정적인 운영 상황입니다.")
    elif solar_power > 0:
        st.info("태양광 발전량이 낮아지고 있어, ESS 충전량을 함께 고려해야 합니다.")
    else:
        st.info("야간에는 태양광 발전이 이루어지지 않으므로 외부 전력과 ESS 의존도가 높아집니다.")
else:
    if backup_generator:
        st.warning("정전 상황이지만 비상발전기가 작동하여 핵심 의료정보시스템을 우선 유지할 수 있습니다.")
    elif ess_level < 25:
        st.error("ESS 잔량이 낮아 핵심 의료정보시스템의 운영 위험이 커지고 있습니다.")
    else:
        st.warning("정전 상황에서는 ESS 잔량과 전력 공급 전략에 따라 시스템 상태가 달라집니다.")

st.caption(
    "※ 이 시뮬레이션은 실제 병원 운영 기준이 아니라, 신재생 에너지·ESS·의료정보시스템 안정성의 관계를 이해하기 위한 탐구용 모형입니다."
)
