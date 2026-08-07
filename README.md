# 💧 RO/EDI 순수 설비 점검일지 통합 관리 시스템 (Pure Water Inspection App)

반도체 및 정밀 공정 부문의 **순수(Pure Water) 제조 설비(R/O, EDI, DI M/B Polisher, 2-Metal Filter)** 운용 현황을 디지털화하여 모바일 및 PC 환경에서 편리하게 기록, 조회, 분석 및 CSV 내보내기를 지원하는 웹 애플리케이션입니다.

---

## 🌟 주요 기능 (Key Features)

1. **🏢 건물별 맞춤형 점검 서식 (B동, C동 1차, D동 2메탈, D동 1,2F PS, PS 3F, E동)**
   - 현장 점검 서식 100% 매칭
   - 동별 R/O 1차/2차, EDI(A/B/C), DI Polisher, Resin Trap 등 독자 구조 및 임계 범위 지정

2. **⚡ 가동 / 비가동 교차 인터락 (Standby Auto-Locking & Manual Toggle)**
   - 펌프/라인(A/B 1가동 1예비, 3중 2가동 등) 수치 입력 시 미작동 예비 펌프가 자동으로 `[비가동]` 상태로 교차 잠금
   - 우측 상단 **`[가동] / [비가동]` 뱃지를 수동으로 클릭**하여 개별 펌프 상태 직접 전환 가능

3. **📱 모바일 최적화 엔터(Enter) 키 자동 순차 이동**
   - 모바일 키보드의 **[다음 / Enter]** 버튼 클릭 시 다음 입력 창으로 자동 포커스 이동 및 중앙 스크롤

4. **📊 통합 비교 트렌드 그래프 (Multi-Line Trend Charts)**
   - 펌프/라인 간 비교(예: 라인 A vs 라인 B vs 라인 C)를 한눈에 파악할 수 있는 통합 꺾은선 그래프 제공
   - 교차 운전 또는 미입력 날짜 발생 시에도 끊김 없이 연결선 유지 (`spanGaps: true`)

5. **📋 이전 기록 불러오기 및 CSV 엑셀 내보내기**
   - [이전 값 복사] 버튼으로 기존 작성 데이터 자동 불러오기
   - 점검 이력 한글 깨짐 없는 UTF-8 BOM CSV 내보내기 지원

---

## 🛠️ 기술 스택 (Tech Stack)

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Database**: SQLite3 (WAL 모드)
- **Frontend**: Vanilla JavaScript (ES6+), Vanilla CSS (Flexbox & CSS Grid)
- **Visualization**: Chart.js 4.4

---

## 🚀 시작하기 (Quick Start)

### 1. 저장소 복제 (Clone Repository)
```bash
git clone https://github.com/your-username/ro-edi-inspection-app.git
cd ro-edi-inspection-app
```

### 2. 가상환경 생성 및 의존성 설치
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 서버 실행
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
웹 브라우저에서 `http://localhost:8000` 접속

---

## 🔑 기본 로그인 계정 (Credentials)

- **사번 (ID)**: `1234`
- **비밀번호 (Password)**: `5678`

---

## 📂 프로젝트 구조 (Directory Structure)

```text
ro-edi-inspection-app/
├── main.py                # FastAPI 서버 메인 및 API 라우트
├── database.py            # SQLite 데이터베이스 연결 및 CRUD 함수
├── seed_sample_data.py    # 샘플 데이터 생성 유틸리티 (선택 실행)
├── requirements.txt       # 파이썬 라이브러리 목록
├── .gitignore             # Git 제외 설정 파일
├── README.md              # 프로젝트 안내 문서
└── static/                # 프론트엔드 정적 파일
    ├── index.html         # 메인 웹 페이지
    ├── styles.css         # UI 커스텀 스타일시트
    └── app.js             # 폼 제어 및 Chart.js 시각화 로직
```

---

## 📄 라이선스 (License)

본 프로젝트는 자유롭게 활용 및 수정이 가능합니다.
