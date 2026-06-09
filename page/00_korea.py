import streamlit as pd
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
# (실제 KDCA 서버 요청을 모방하여 수업에 필요한 변수들로 구성했습니다.)
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
    
    # 날짜별, 지역별 감염 데이터 생성 (특정 시점에 확진자가 급증하는 패턴 부여)
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

# 기간 선택에 따른 데이터 필터링 정의
max_date = df['날짜'].max()
if period_option == "최근 1일":
    start_filter_date = max_date - timedelta(days=1)
elif period_option == "최근 7일":
    start_filter_date = max_date - timedelta(days=7)
else:
