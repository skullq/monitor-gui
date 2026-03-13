# Server Monitoring System (GUI)

PyQt5를 이용한 실시간 서버 상태 모니터링 시스템입니다. HTTP 요청을 통해 서버의 응답 상태(Status), 응답 속도(Latency), 응답 데이터(Data)를 주기적으로 확인합니다.
This is a real-time server status monitoring system built with PyQt5. It periodically checks the server's response status, latency, and data via HTTP requests.

## 1. 설치 및 환경 구성 (Using uv)
## 1. Installation and Setup (Using uv)

이 프로젝트는 Python 패키지 관리를 위해 `uv`를 사용하는 것을 권장합니다.
This project recommends using `uv` for Python package management.

### 필수 패키지
소스코드 실행을 위해 다음의 외부 라이브러리가 필요합니다:
- `requests`: HTTP 요청 처리
- `PyQt5`: GUI 구성
### Required Packages
The following external libraries are required to run the source code:
- `requests`: For handling HTTP requests
- `PyQt5`: For the GUI

### 설치 명령
터미널에서 프로젝트 폴더로 이동 후 다음 명령어를 실행하여 가상환경을 생성하고 패키지를 설치하세요.
### Installation Commands
Navigate to the project folder in your terminal and run the following commands to create a virtual environment and install the packages.

```bash
# 1. 가상환경 생성 (선택 사항)
# 1. Create a virtual environment (optional)
uv venv

# 윈도우의 경우 가상환경 활성화
# Activate the virtual environment (on Windows)
.venv\Scripts\activate

# 2. 패키지 설치
# 2. Install packages
uv pip install requests PyQt5
```

## 2. 사용법

### 실행
```bash
python monitor-gui-v2.py
# 또는 uv를 통해 직접 실행
uv run monitor-gui-v2.py
```

### 주요 기능
1.  **서버 추가**: 상단의 IP와 Port 입력란에 정보를 입력하고 `추가` 버튼을 누릅니다. (IP 유효성 검사가 포함되어 있습니다.)
2.  **서버 삭제**: 리스트에서 항목을 선택한 후 `삭제` 버튼을 누르거나 `Delete` 키를 누릅니다.
3.  **모니터링 주기 변경**: 상단의 `간격` 버튼을 눌러 0.5s, 1.0s, 2.0s 중 선택할 수 있습니다.
4.  **데이터 저장**: 추가된 서버 리스트는 `servers.json` 파일에 자동으로 저장되어 프로그램 재실행 시 유지됩니다.

### 상태 표시 (색상 구분)
- **초록색 (Green)**: 정상 (Status 200 등)
- **빨간색 (Red)**: 접속 실패 (DOWN) 또는 에러 발생
- **파란색 굵은 글씨 (Blue/Bold)**: 이전 응답과 비교하여 **데이터(Data)가 변경됨**을 감지했을 때 표시됩니다.

---
*Note: `monitor-gui-v2.py`가 최신 버전의 기능을 포함하고 있습니다.*