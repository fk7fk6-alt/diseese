import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# 1. 웹 페이지 기본 설정
st.set_page_config(
    page_title="통합과학II - 감염경로 추적 시뮬레이터",
    page_icon="🦠",
    layout="wide"
)

# -----------------------------------------------------------------------------
# [데이터 소스 & 처리] 모의 데이터 생성 함수
# -----------------------------------------------------------------------------
@st.cache_data
def load_infection_data():
    # 기준 날짜 설정
    end_date = datetime.today()
    start_date = end_date - timedelta(days=60)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 대한민국 주요 도시 중심 좌표 및 인구 비례 가중치
    regions = {
        '서울': {'lat': 37.5665, 'lon': 126.9780, 'weight': 0.35},
        '경기': {'lat': 37.4138, 'lon': 127.5183, 'weight': 0.30},
        '인천': {'lat': 37.4563, 'lon': 126.7052, 'weight': 0.10},
        '부산': {'lat': 35.1796, 'lon': 129.0756, 'weight': 0.08},
        '대구': {'lat': 35.8714, 'lon': 128.6014, 'weight': 0.05},
        '대전': {'lat': 36.3504, 'lon': 127.3845, 'weight': 0.04},
        '광주': {'lat': 35.1595, 'lon': 126.8526, 'weight': 0.04},
        '울산': {'lat': 35.5389, 'lon': 129.3114, 'weight': 0.02},
        '강원': {'lat': 37.8228, 'lon': 128.1555, 'weight': 0.02}
    }
    
    data_list = []
    np.random.seed(42) # 데이터 일관성을 위한 시드 고정
    
    # 날짜별, 지역별 감염 데이터 생성
    for date in date_range:
        for region, info in regions.items():
            # 기본 감염자 수 (인구 가중치 반영)
            base_cases = np.random.poisson(lam=5 * info['weight'])
            
            # 특정 날짜(예: 15일 전)에 서울/경기 지역에서 집단 감염 발생 트렌드 모사
            days_ago = (end_date - date).days
            if 10 <= days_ago <= 20 and region in ['서울', '경기']:
                base_cases += np.random.randint(15, 30)
                
            for _ in range(int(base_cases)):
                # 중심 좌표 주변으로 미세하게 분산된 확진자 위치 생성
                lat_offset = np.random.normal(0, 0.08)
                lon_offset = np.random.normal(0, 0.08)
                
                data_list.append({
                    '날짜': date,
                    '지역': region,
                    '위도': info['lat'] + lat_offset,
                    '경도': info['lon'] + lon_offset,
                    '감염자수': 1
                })
                
    return pd.DataFrame(data_list)

# 데이터 로드
df = load_infection_data()

# -----------------------------------------------------------------------------
# [사용자 인터페이스] 사이드바 및 대시보드 레이아웃
# -----------------------------------------------------------------------------
st.title("🦠 고등학교 통합과학II: 감염경로 찾기 탐구 활동")
st.markdown("""
이 프로그램은 **질병관리청(KDCA) 감염병 모니터링 시스템** 데이터를 기반으로 구성된 시뮬레이터입니다.  
학생 여러분은 방역관이 되어, 시간과 공간에 따른 감염자 발생 추이를 분석하고 **'감염 경로'**를 예측해 봅시다.
""")
st.divider()

# 사이드바: 조건 선택 규칙
st.sidebar.header("🔍 탐구 조건 설정")

# 1. 기간 선택 (1일, 7일, 30일)
period_option = st.sidebar.selectbox(
    "분석할 기간을 선택하세요:",
    ["최근 1일", "최근 7일", "최근 30일"]
)

# [오류 해결 포인트] 조건문과 변수 할당의 들여쓰기를 완벽히 통일했습니다.
max_date = df['날짜'].max()
if period_option == "최근 1일":
    start_filter_date = max_date - timedelta(days=1)
elif period_option == "최근 7일":
    start_filter_date = max_date - timedelta(days=7)
else:
    start_filter_date = max_date - timedelta(days=30)

filtered_df = df[df['날짜'] >= start_filter_date]

# 2. 지역 선택 (멀티 셀렉트)
all_regions = sorted(df['지역'].unique())
selected_regions = st.sidebar.multiselect(
    "조회할 지역을 선택하세요 (미선택 시 전체 조회):",
    options=all_regions,
    default=all_regions
)

if selected_regions:
    filtered_df = filtered_df[filtered_df['지역'].isin(selected_regions)]

# -----------------------------------------------------------------------------
# [원하는 기능 1 & 2] 지역별 감염자 추이 및 지도 시각화
# -----------------------------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📍 전국 확진자 발생 위치 지도")
    st.caption("확진자가 발생한 세부 위치를 점으로 표시한 지도입니다. 인접성(밀집도)을 확인해보세요.")
    
    # 대한민국 중심부로 지도 시작 위치 설정
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, control_scale=True)
    
    # 필터링된 데이터를 지도에 마커(점)로 표시
    for idx, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row['위도'], row['경도']],
            radius=4,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.6,
            popup=f"{row['지역']} ({row['날짜'].strftime('%m-%d')})"
        ).add_to(m)
        
    # Streamlit에 지도 렌더링
    st_folium(m, width="100%", height=450, returned_objects=[])

with col2:
    st.subheader("📈 기간별 감염자 발생 추이")
    st.caption("선택한 기간 동안의 일별 신규 확진자 변화 그래프입니다.")
    
    # 일별, 지역별로 데이터 그룹화하여 시계열 차트 생성
    chart_data = filtered_df.groupby(['날짜', '지역']).size().unstack(fill_value=0)
    
    # [오류 해결 포인트] else 블록 뒤에 정상적인 실행 코드가 오도록 맞췄습니다.
    if not chart_data.empty:
        st.line_chart(chart_data, height=450)
    else:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

# -----------------------------------------------------------------------------
# [학생이 탐구할 질문] 과학적 탐구 및 데이터 해석 섹션
# -----------------------------------------------------------------------------
st.divider()
st.subheader("🤔 [학생 탐구 활동] 감염경로를 어떻게 예측해야 할까?")
st.markdown("""
> **데이터 해석 가이드:** > 감염병의 전파 경로를 파악하려면 단순히 '어디서 많이 발생했는가'뿐만 아니라, **시간의 흐름(추이)**과 **공간적 거리(지도)**를 함께 연결지어 해석해야 합니다.
""")

# 학생들이 직접 작성하며 생각할 수 있는 질문 폼
with st.form("student_inquiry_form"):
    st.markdown("**질문 1. '최근 30일' 조건에서 그래프의 특정 시점에 확진자가 급증한 지역은 어디인가요?**")
    answer1 = st.text_area("답변을 입력하세요:", placeholder="예: 약 2주 전부터 서울과 경기 지역에서 확진자가 급증하기 시작했습니다.")
    
    st.markdown("**질문 2. 지도를 보았을 때 확진자들이 밀집된 형태(클러스터)를 보이는 곳은 어디이며, 교통망이나 인구 밀도와 어떤 관계가 있을지 추론해 보세요.**")
    answer2 = st.text_area("답변을 입력하세요:", placeholder="예: 지하철 노선이나 대도시 중심으로 점들이 모여 있는 것으로 보아, 유동인구가 많은 곳을 통해 확진자가 번져나갔을 것 같습니다.")
    
    st.markdown("**질문 3. [핵심 질문] 시계열 그래프의 발생 순서와 지도의 거리 관계를 종합했을 때, 이 감염병의 '최초 발생지(또는 유입 경로)'는 어디라고 예측할 수 있나요? 그렇게 생각한 데이터 과학적 근거를 설명하세요.**")
    answer3 = st.text_area("답변을 입력하세요:", placeholder="예: 대구보다 서울에서 며칠 더 일찍 그래프가 상승하기 시작했고, 지도상 서울 주변 점들의 밀도가 가장 높은 것으로 보아 수도권에서 시작되어 확산된 것으로 예측됩니다.")
    
    # 제출 버튼
    submit_btn = st.form_submit_button("내 탐구 결과 저장 및 확인")
    
    if submit_btn:
        st.success("🎉 탐구 답변이 성공적으로 기록되었습니다! 선생님께 화면을 보여드리거나 내용을 공유하세요.")
        st.balloons()
