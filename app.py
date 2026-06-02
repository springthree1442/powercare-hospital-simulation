import streamlit as st

# =========================================================
# 1. 기본 설정
# =========================================================

st.set_page_config(
    page_title="PowerCare Hospital",
    page_icon="🏥",
    layout="wide"
)

# =========================================================
# 2. CSS 스타일
# =========================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 18px;
        color: #555555;
        margin-bottom: 20px;
    }
    .section-box {
        border: 1px solid #dddddd;
        border-radius: 14px;
        padding: 18px;
        background-color: #fafafa;
        margin-bottom: 16px;
    }
    .status-card {
        border: 1px solid #dddddd;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 10px;
        background-color: white;
    }
    .small-text {
        font-size: 13px;
        color: #666666;
    }
    .big-number {
        font-size: 30px;
        font-weight: 800;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# 3. 세션 상태 초기화
# =========================================================

if "time_passed" not in st.session_state:
    st.session_state.time_passed = 0

if "ess_level" not in st.session_state:
    st.session_state.ess_level = 70

if "external_power" not in st.session_state:
    st.session_state.external_power = "정상"

if "history" not in st.session_state:
    st.session_state.history = []

if "simulation_started" not in st.session_state:
    st.session_state.simulation_started = False

# =========================================================
# 4. 기본 데이터
# =========================================================

weather_data = {
    "맑음 ☀️": {
        "factor": 1.0,
        "description": "태양광 발전이 가장 원활하게 이루어집니다."
    },
    "구름 조금 ⛅": {
        "factor": 0.7,
        "description": "태양광 발전량이 일부 감소합니다."
    },
    "흐림 ☁️": {
        "factor": 0.3,
        "description": "태양광 발전량이 크게 감소합니다."
    },
    "비 🌧️": {
        "factor": 0.15,
        "description": "태양광 발전량이 매우 낮습니다."
    },
    "야간 🌙": {
        "factor": 0.0,
        "description": "태양광 발전이 이루어지지 않습니다."
    }
}

systems = {
    "환자 모니터링": {
        "power": 30,
        "role": "환자 생체정보 실시간 확인",
        "icon": "🫀"
    },
    "EMR": {
        "power": 25,
        "role": "진료기록·처방 정보 확인",
        "icon": "📋"
    },
    "서버·네트워크": {
        "power": 25,
        "role": "의료정보 저장·전송 유지",
        "icon": "🖥️"
    },
    "PACS": {
        "power": 35,
        "role": "CT·MRI 등 의료영상 확인",
        "icon": "🩻"
    },
    "일반 행정": {
        "power": 15,
        "role": "원무·일반 사무 업무",
        "icon": "🏢"
    }
}

strategy_order = {
    "환자 안전 우선": ["환자 모니터링", "EMR", "서버·네트워크", "PACS", "일반 행정"],
    "영상 진단 우선": ["PACS", "서버·네트워크", "EMR", "환자 모니터링", "일반 행정"],
    "전체 균등 공급": ["환자 모니터링", "EMR", "서버·네트워크", "PACS", "일반 행정"]
}

# =========================================================
# 5. 계산 함수
# =========================================================

def calculate_solar_power(base_power, weather):
    """날씨 조건에 따른 태양광 발전량 계산"""
    return base_power * weather_data[weather]["factor"]


def calculate_available_power(solar_power, ess_level, external_power, backup_generator):
    """
    현재 조건에서 병원에 공급 가능한 전력을 단순화하여 계산한다.
    실제 병원 설계 기준이 아니라 교육용 시뮬레이션 규칙이다.
    """

    available_power = solar_power

    if external_power == "정상":
        available_power += 120

    if external_power == "정전":
        available_power += ess_level * 1.2

    if backup_generator:
        available_power += 80

    return available_power


def get_system_statuses(available_power, strategy):
    """
    사용 가능한 전력과 공급 전략에 따라 의료정보시스템 상태를 결정한다.
    """

    statuses = {}

    if strategy == "전체 균등 공급":
        total_need = sum(info["power"] for info in systems.values())
        ratio = available_power / total_need if total_need > 0 else 0

        for name in systems:
            if ratio >= 1:
                statuses[name] = "🟢 정상 운영"
            elif ratio >= 0.65:
                statuses[name] = "🟡 제한 운영"
            elif ratio >= 0.35:
                statuses[name] = "🟠 중단 위험"
            else:
                statuses[name] = "🔴 우선 공급 제외"

        return statuses

    remaining_power = available_power

    for name in strategy_order[strategy]:
        need = systems[name]["power"]

        if remaining_power >= need:
            statuses[name] = "🟢 정상 운영"
            remaining_power -= need
        elif remaining_power >= need * 0.5:
            statuses[name] = "🟡 제한 운영"
            remaining_power = 0
        elif remaining_power > 0:
            statuses[name] = "🟠 중단 위험"
            remaining_power = 0
        else:
            statuses[name] = "🔴 우선 공급 제외"

    return statuses


def calculate_ess_change(weather, external_power, backup_generator, strategy):
    """
    1시간이 지났을 때 ESS 충전율 변화를 계산한다.
    """

    weather_factor = weather_data[weather]["factor"]

    if external_power == "정상":
        if weather_factor >= 0.7:
            return +6
        elif weather_factor >= 0.3:
            return +2
        else:
            return 0

    # 정전 상태
    if backup_generator:
        if strategy == "전체 균등 공급":
            return -8
        else:
            return -5

    if strategy == "전체 균등 공급":
        return -18
    elif strategy == "영상 진단 우선":
        return -15
    else:
        return -12


def add_history(message):
    """운영 기록 추가"""
    st.session_state.history.append(
        f"{st.session_state.time_passed}시간 경과 | {message}"
    )


def advance_time(weather, backup_generator, strategy):
    """1시간 진행 버튼을 눌렀을 때의 변화"""
    st.session_state.simulation_started = True
    st.session_state.time_passed += 1

    change = calculate_ess_change(
        weather,
        st.session_state.external_power,
        backup_generator,
        strategy
    )

    st.session_state.ess_level = max(
        0,
        min(100, st.session_state.ess_level + change)
    )

    if st.session_state.external_power == "정상":
        if change > 0:
            add_history(f"태양광 발전으로 ESS가 {change}% 충전되었습니다.")
        else:
            add_history("태양광 발전량이 낮아 ESS 충전 변화가 거의 없습니다.")
    else:
        add_history(f"정전 상황으로 ESS가 {abs(change)}% 사용되었습니다.")


def reset_simulation():
    """시뮬레이션 초기화"""
    st.session_state.time_passed = 0
    st.session_state.ess_level = 70
    st.session_state.external_power = "정상"
    st.session_state.history = []
    st.session_state.simulation_started = False


# =========================================================
# 6. 사이드바: 상황 조절 패널
# =========================================================

st.sidebar.header("⚙️ 상황 조절 패널")

weather = st.sidebar.selectbox(
    "날씨 조건",
    list(weather_data.keys())
)

base_solar_power = st.sidebar.slider(
    "태양광 기준 발전량",
    min_value=50,
    max_value=200,
    value=120,
    step=10,
    help="맑은 날을 기준으로 한 가상 태양광 발전량입니다."
)

strategy = st.sidebar.selectbox(
    "전력 공급 전략",
    ["환자 안전 우선", "전체 균등 공급", "영상 진단 우선"]
)

backup_generator = st.sidebar.checkbox(
    "비상발전기 작동",
    value=False
)

st.sidebar.divider()

col_a, col_b = st.sidebar.columns(2)

with col_a:
    if st.button("⚠️ 정전 발생", use_container_width=True):
        st.session_state.external_power = "정전"
        st.session_state.simulation_started = True
        add_history("외부 전력이 차단되어 비상 운영 모드로 전환되었습니다.")

with col_b:
    if st.button("🔌 전력 복구", use_container_width=True):
        st.session_state.external_power = "정상"
        add_history("외부 전력이 복구되었습니다.")

if st.sidebar.button("⏱️ 1시간 진행", use_container_width=True):
    advance_time(weather, backup_generator, strategy)

if st.sidebar.button("🔄 시뮬레이션 초기화", use_container_width=True):
    reset_simulation()

# =========================================================
# 7. 현재 계산값
# =========================================================

solar_power = calculate_solar_power(base_solar_power, weather)

available_power = calculate_available_power(
    solar_power,
    st.session_state.ess_level,
    st.session_state.external_power,
    backup_generator
)

system_statuses = get_system_statuses(
    available_power,
    strategy
)

normal_count = sum(
    1 for status in system_statuses.values()
    if "정상" in status
)

warning_count = sum(
    1 for status in system_statuses.values()
    if "제한" in status or "위험" in status
)

stopped_count = sum(
    1 for status in system_statuses.values()
    if "제외" in status
)

# =========================================================
# 8. 제목 및 안내
# =========================================================

st.markdown('<div class="main-title">🏥 PowerCare Hospital</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">신재생 에너지 기반 스마트병원 운영 시뮬레이션</div>',
    unsafe_allow_html=True
)

st.info(
    "본 웹앱은 태양광 발전, ESS, 정전 상황, 비상발전기 작동 여부, 전력 공급 전략에 따라 "
    "스마트병원의 의료정보시스템 상태가 어떻게 달라지는지 관찰하기 위한 교육용 시뮬레이션입니다. "
    "시스템별 전력량과 운영 상태는 탐구 목적에 맞게 설정한 가상 조건이며, 실제 병원의 비상전력 설계 기준과는 다를 수 있습니다."
)

# =========================================================
# 9. 상단 요약 카드
# =========================================================

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

with summary_col1:
    st.metric("현재 운영 시간", f"{st.session_state.time_passed}시간 경과")

with summary_col2:
    st.metric("외부 전력 상태", st.session_state.external_power)

with summary_col3:
    st.metric("ESS 잔량", f"{st.session_state.ess_level}%")

with summary_col4:
    st.metric("정상 운영 시스템", f"{normal_count}개")

# =========================================================
# 10. 메인 화면
# =========================================================

left, center, right = st.columns([1.1, 1.5, 1.3])

# ---------------------------------------------------------
# 왼쪽: 현재 조건
# ---------------------------------------------------------

with left:
    st.subheader("🌤️ 현재 조건")

    st.markdown('<div class="section-box">', unsafe_allow_html=True)

    st.write(f"**날씨**: {weather}")
    st.write(f"**태양광 기준 발전량**: {base_solar_power} kW")
    st.write(f"**현재 태양광 발전량**: {solar_power:.1f} kW")
    st.write(f"**외부 전력**: {st.session_state.external_power}")
    st.write(f"**비상발전기**: {'작동 중' if backup_generator else '작동 안 함'}")
    st.write(f"**전력 공급 전략**: {strategy}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("📌 조건 설명")
    st.write(weather_data[weather]["description"])

    if strategy == "환자 안전 우선":
        st.success("환자 모니터링, EMR, 서버를 우선 유지하는 전략입니다.")
    elif strategy == "영상 진단 우선":
        st.warning("PACS와 서버를 우선 유지하는 전략입니다.")
    else:
        st.info("모든 시스템에 전력을 균등하게 배분하는 전략입니다.")

# ---------------------------------------------------------
# 가운데: 에너지 흐름 상황판
# ---------------------------------------------------------

with center:
    st.subheader("🔋 에너지 흐름 상황판")

    st.markdown('<div class="section-box">', unsafe_allow_html=True)

    st.markdown("### 1. 태양광 발전")
    st.progress(min(1.0, solar_power / base_solar_power))
    st.write(f"현재 발전량: **{solar_power:.1f} kW**")

    if st.session_state.external_power == "정상":
        if solar_power >= base_solar_power * 0.7:
            st.success("태양광 발전과 외부 전력이 함께 병원 운영을 보조하고 있습니다.")
        elif solar_power > 0:
            st.info("태양광 발전량이 낮아 외부 전력 의존도가 높아졌습니다.")
        else:
            st.info("태양광 발전이 없어 외부 전력 중심으로 운영됩니다.")
    else:
        st.error("외부 전력이 차단되어 병원이 비상 운영 상태입니다.")

    st.markdown("### 2. ESS 저장장치")
    st.progress(st.session_state.ess_level / 100)
    st.write(f"ESS 잔량: **{st.session_state.ess_level}%**")

    if st.session_state.external_power == "정상":
        if solar_power > 80:
            st.write("태양광 발전량이 충분해 ESS 충전에 유리합니다.")
        else:
            st.write("태양광 발전량이 낮아 ESS 충전 효과가 제한적입니다.")
    else:
        if st.session_state.ess_level >= 50:
            st.warning("ESS가 방전되며 의료정보시스템 운영을 보조하고 있습니다.")
        elif st.session_state.ess_level >= 25:
            st.warning("ESS 잔량이 줄어들어 일부 시스템 제한 가능성이 커지고 있습니다.")
        else:
            st.error("ESS 잔량이 낮아 핵심 시스템 유지 위험이 커졌습니다.")

    st.markdown("### 3. 전력 흐름")
    if st.session_state.external_power == "정상":
        flow_text = "외부 전력망 🔌 + 태양광 ☀️ → 병원 운영 🏥 → ESS 충전 🔋"
    else:
        if backup_generator:
            flow_text = "태양광 ☀️ + ESS 🔋 + 비상발전기 ⚙️ → 핵심 시스템 우선 공급 🏥"
        else:
            flow_text = "태양광 ☀️ + ESS 🔋 → 제한된 전력으로 병원 비상 운영 🏥"

    st.code(flow_text)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 오른쪽: 의료정보시스템 상태
# ---------------------------------------------------------

with right:
    st.subheader("🏥 의료정보시스템 상태")

    for system_name, info in systems.items():
        status = system_statuses[system_name]

        if "정상" in status:
            box_color = "#e9f7ef"
        elif "제한" in status:
            box_color = "#fff8e1"
        elif "위험" in status:
            box_color = "#fff3e0"
        else:
            box_color = "#fdecea"

        st.markdown(
            f"""
            <div style="
                border: 1px solid #dddddd;
                border-radius: 12px;
                padding: 12px;
                margin-bottom: 10px;
                background-color: {box_color};
            ">
                <b>{info['icon']} {system_name}</b><br>
                상태: <b>{status}</b><br>
                <span class="small-text">역할: {info['role']}</span><br>
                <span class="small-text">가상 필요 전력: {info['power']} kW</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================================================
# 11. 현재 상황 알림
# =========================================================

st.divider()
st.subheader("📢 현재 상황 알림")

if st.session_state.external_power == "정상":
    if solar_power >= base_solar_power * 0.7:
        st.success(
            "현재는 외부 전력과 태양광 발전이 함께 활용되는 안정적인 운영 상황입니다. "
            "ESS 충전에도 비교적 유리합니다."
        )
    elif solar_power > 0:
        st.info(
            "태양광 발전량이 감소한 상태입니다. 병원 운영은 가능하지만, "
            "신재생 에너지의 변동성을 고려해야 합니다."
        )
    else:
        st.info(
            "야간에는 태양광 발전이 이루어지지 않습니다. "
            "병원 운영은 외부 전력과 저장 전력에 더 의존하게 됩니다."
        )
else:
    if backup_generator:
        st.warning(
            "정전 상황이지만 비상발전기가 작동하고 있어 핵심 의료정보시스템을 유지하기에 유리합니다."
        )
    elif st.session_state.ess_level < 25:
        st.error(
            "정전 상황에서 ESS 잔량이 낮습니다. 중요 의료정보시스템 중심의 우선 공급이 필요합니다."
        )
    else:
        st.warning(
            "정전 상황에서는 ESS 잔량과 전력 공급 전략에 따라 의료정보시스템의 상태가 달라집니다."
        )

if stopped_count > 0:
    st.error(
        f"현재 조건에서는 {stopped_count}개의 시스템이 우선 공급에서 제외되었습니다. "
        "전력 공급 전략, ESS 잔량, 비상발전기 작동 여부를 조절해 볼 수 있습니다."
    )
elif warning_count > 0:
    st.warning(
        f"현재 조건에서는 {warning_count}개의 시스템이 제한 운영 또는 중단 위험 상태입니다."
    )
else:
    st.success("현재 조건에서는 주요 의료정보시스템이 안정적으로 운영되고 있습니다.")

# =========================================================
# 12. 운영 기록 및 시뮬레이션 원리
# =========================================================

st.divider()

tab1, tab2, tab3 = st.tabs(
    ["🕒 운영 기록", "🧮 시뮬레이션 원리", "📄 산출물 설명"]
)

with tab1:
    st.subheader("운영 기록")

    if len(st.session_state.history) == 0:
        st.write("아직 기록된 시뮬레이션 변화가 없습니다. 왼쪽에서 정전을 발생시키거나 1시간을 진행해 보세요.")
    else:
        for record in reversed(st.session_state.history):
            st.write(f"- {record}")

    st.caption(
        "운영 기록은 사용자가 정전, 전력 복구, 시간 진행을 조작할 때마다 저장됩니다."
    )

with tab2:
    st.subheader("시뮬레이션 계산 원리")

    st.markdown(
        """
        이 프로그램은 실제 병원 전력 설계 프로그램이 아니라,  
        신재생 에너지와 의료정보시스템 안정성의 관계를 이해하기 위한 과제제출용 모형입니다.

        **1. 태양광 발전량 계산**

        - 맑음: 기준 발전량의 100%
        - 구름 조금: 기준 발전량의 70%
        - 흐림: 기준 발전량의 30%
        - 비: 기준 발전량의 15%
        - 야간: 기준 발전량의 0%

        **2. 사용 가능한 전력 계산**

        사용 가능한 전력은 다음 요소를 단순화하여 합산합니다.

        - 현재 태양광 발전량
        - 외부 전력망 공급 여부
        - ESS 잔량
        - 비상발전기 작동 여부

        **3. 시스템 상태 판단**

        사용 가능한 전력이 충분하면 시스템은 정상 운영됩니다.  
        전력이 부족해지면 선택한 전력 공급 전략에 따라 일부 시스템은 제한 운영, 중단 위험, 우선 공급 제외 상태가 됩니다.

        **4. ESS 변화**

        정전 상태에서 시간이 지나면 ESS가 감소합니다.  
        외부 전력이 정상이고 태양광 발전량이 충분하면 ESS가 충전되는 것으로 설정했습니다.
        """
    )

with tab3:
    st.subheader("산출물 설명")

    st.markdown(
        """
        **산출물명:**  
        PowerCare Hospital: 신재생 에너지 기반 스마트병원 운영 시뮬레이션

        **산출물 목적:**  
        본 산출물은 태양광 발전, ESS, 정전 상황, 비상발전기 작동 여부, 전력 공급 전략에 따라  
        스마트병원의 의료정보시스템 상태가 어떻게 달라지는지 관찰할 수 있도록 제작한 Python 기반 웹앱이다.

        **보고서와의 연결성:**  
        모둠 탐구에서 학교 태양광 발전 자료를 분석하며 발전량이 일조량과 시간대에 따라 변동한다는 점을 확인하였다.  
        이를 개별 심화 탐구에서는 스마트병원 상황으로 확장하여, 발전량이 일정하지 않은 신재생 에너지를 병원의 의료정보시스템 운영에 활용하려면  
        ESS, 비상발전기, 중요 시스템별 우선 공급 구조가 함께 고려되어야 한다는 점을 시뮬레이션으로 표현하였다.

        **주의:**  
        본 프로그램은 실제 병원 운영 기준을 계산하는 프로그램이 아니라, 탐구 내용을 시각적으로 이해하기 위한 교육용 시뮬레이션이다.
        """
        with tab3:
    st.subheader("산출물 설명")

    st.markdown(
        """
        **산출물명:**  
        PowerCare Hospital: 신재생 에너지 기반 스마트병원 운영 시뮬레이션

        **산출물 목적:**  
        본 산출물은 태양광 발전, ESS, 정전 상황, 비상발전기 작동 여부, 전력 공급 전략에 따라  
        스마트병원의 의료정보시스템 상태가 어떻게 달라지는지 관찰할 수 있도록 제작한 Python 기반 웹앱이다.

        **간단한 시뮬레이션 사용법:**  

        1. 왼쪽의 **상황 조절 패널**에서 날씨 조건을 선택한다.  
           날씨에 따라 태양광 발전량이 달라진다.

        2. **태양광 기준 발전량**을 조절하여 병원이 확보할 수 있는 신재생 에너지의 규모를 바꿔 본다.

        3. **전력 공급 전략**을 선택한다.  
           환자 안전 우선, 전체 균등 공급, 영상 진단 우선 중 어떤 방식을 선택하느냐에 따라  
           의료정보시스템의 상태가 다르게 나타난다.

        4. **정전 발생** 버튼을 누르면 병원이 비상 운영 상태로 전환된다.  
           이때 ESS와 비상발전기 작동 여부가 시스템 유지에 중요한 영향을 준다.

        5. **1시간 진행** 버튼을 누르면 시간이 흐르며 ESS 잔량이 변화한다.  
           시간이 지날수록 의료정보시스템의 운영 상태가 어떻게 달라지는지 확인할 수 있다.

        6. **비상발전기 작동**을 선택하거나 전력 공급 전략을 바꾸어,  
           같은 정전 상황에서도 병원 시스템 상태가 어떻게 달라지는지 비교한다.

        7. **시뮬레이션 초기화** 버튼을 누르면 처음 상태로 돌아가 다시 조건을 바꿔 볼 수 있다.

        **보고서와의 연결성:**  
        모둠 탐구에서 학교 태양광 발전 자료를 분석하며 발전량이 일조량과 시간대에 따라 변동한다는 점을 확인하였다.  
        이를 개별 심화 탐구에서는 스마트병원 상황으로 확장하여, 발전량이 일정하지 않은 신재생 에너지를 병원의 의료정보시스템 운영에 활용하려면  
        ESS, 비상발전기, 중요 시스템별 우선 공급 구조가 함께 고려되어야 한다는 점을 시뮬레이션으로 표현하였다.

        **주의:**  
        본 프로그램은 실제 병원 운영 기준을 계산하는 프로그램이 아니라, 탐구 내용을 시각적으로 이해하기 위한 교육용 시뮬레이션이다.
        """
    )
    )

# =========================================================
# 13. 하단 문구
# =========================================================

st.caption(
    "※ 본 시뮬레이션의 전력량, 시스템 상태, 우선순위는 탐구 목적에 맞게 단순화한 가상 조건입니다."
)
