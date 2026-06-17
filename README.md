# RTK-GPS

**RTK-GPS**는 u-blox ZED-F9P 수신기와 NTRIP 보정 데이터를 활용하여 ROS2 환경에서 정밀한 RTK(실시간 동역학) 위치 결정 서비스를 제공합니다.

## 📋 목차
- [빠른 시작 (Quick Start)](#빠른-시작-quick-start)
- [시스템 요구사항](#시스템-요구사항)
- [설치 과정 상세 설명](#설치-과정-상세-설명)
- [패키지 구성](#패키지-구성)
- [Launch 옵션](#launch-옵션)

---

## 🚀 빠른 시작 (Quick Start)

```bash
# 1️⃣ 저장소 클론 및 서브모듈 받기
cd ~/sensor_ws/src
git clone https://github.com/zeroworks-robotics/RTK-GPS.git
cd RTK-GPS
git submodule update --init --recursive

# 2️⃣ udev 규칙 적용 (Ardusimple 장치 권한)
sudo ./script/install_udev_rules.sh

# 3️⃣ ROS2 의존성 설치
cd ~/sensor_ws
rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# 4️⃣ 패키지 빌드
colcon build --symlink-install

# 5️⃣ 런치 파일 실행
ros2 launch combined_rtk combined_nodes.launch.py
```

---

## 📦 시스템 요구사항

| 항목 | 요구사항 |
|------|--------|
| **OS** | Ubuntu 22.04 LTS (Jammy) 이상 |
| **ROS** | ROS2 Humble 이상 |
| **Python** | Python 3.10 이상 |
| **하드웨어** | u-blox ZED-F9P + Antenna |
| **연결** | USB 시리얼(ArduSimple) 또는 직렬 포트 |

---

## 🔧 설치 과정 상세 설명

### 1️⃣ Git Clone & Submodule 받기

```bash
cd ~/sensor_ws/src
git clone https://github.com/zeroworks-robotics/RTK-GPS.git
cd RTK-GPS
git submodule update --init --recursive
```

**설명:**
- **`git clone`**: RTK-GPS 저장소를 로컬에 다운로드합니다.
- **`git submodule update --init --recursive`**: 프로젝트에 포함된 종속 저장소(ntrip_client, ublox 드라이버)를 자동으로 받습니다.
  - `ublox/`: u-blox 공식 GPS 드라이버 (ROS2 빌드)
  - `ntrip_client/`: NTRIP 보정 데이터 클라이언트 (LORD-MicroStrain)

---

### 2️⃣ udev Rules 적용

```bash
sudo ./script/install_udev_rules.sh
```

**설명:**
- **목적**: ArduSimple 장치(`/dev/tty_Ardusimple`)가 시리얼 포트로 인식되도록 udev 규칙을 설정합니다.
- **파일 위치**: [`script/50-ardusimple.rules`](script/50-ardusimple.rules)
- **수행 작업**:
  - u-blox VID/PID를 기반으로 심볼릭 링크 생성
  - 사용자가 sudo 없이 장치에 접근 가능하도록 권한 설정
  - 규칙 리로드: `sudo udevadm control --reload-rules && sudo udevadm trigger`

**확인 명령:**
```bash
ls -la /dev/tty_Ardusimple  # 심볼릭 링크 확인
```

---

### 3️⃣ rosdep init, update, install

```bash
cd ~/sensor_ws
rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

**각 단계 설명:**

| 명령 | 설명 |
|-----|------|
| `rosdep init` | rosdep의 초기 설정 폴더 생성 (`~/.ros/rosdep/`) |
| `rosdep update` | ROS 패키지 의존성 데이터베이스 최신화 |
| `rosdep install --from-paths src --ignore-src -r -y` | src 폴더의 모든 package.xml에서 선언된 시스템/ROS 의존성을 자동 설치 |

**설치되는 주요 의존성:**
- `python3-serial`: 시리얼 통신
- `python3-pyserial`: 시리얼 포트 라이브러리
- ROS2 관련 패키지: `rclpy`, `launch-ros`, `ament-cmake` 등

---

### 4️⃣ Colcon Build

```bash
cd ~/sensor_ws
colcon build --symlink-install
```

**설명:**
- **`colcon build`**: ROS2 빌드 도구로 모든 패키지를 컴파일합니다.
- **`--symlink-install`**: 설치 폴더를 심볼릭 링크로 연결하여 소스 수정 시 재빌드 없이 변경사항을 즉시 반영합니다.

**주요 빌드 대상:**
1. **`ublox_gps`**: C++ 드라이버 (CMake 빌드)
2. **`ublox_msgs`**: GPS 메시지 정의 (CMake 빌드)
3. **`ntrip_client`**: Python NTRIP 클라이언트 (ament_python 빌드)
4. **`combined_rtk`**: 통합 런치 (ament_python 빌드)

**성공 확인:**
```bash
source ~/sensor_ws/install/setup.bash
ros2 pkg list | grep -E 'ublox|ntrip|combined'  # 3개 패키지 모두 출력되어야 함
```

---

### 5️⃣ Launch 실행

```bash
source ~/sensor_ws/install/setup.bash
ros2 launch combined_rtk combined_nodes.launch.py
```

**실행 흐름:**
```
launch script 실행
  ├─ ublox_gps_node 시작 (ZED-F9P 드라이버)
  │   └─ /dev/tty_Ardusimple 열기 → GPS 데이터 수신 시작
  │
  ├─ ntrip_client 시작 (RTCM 보정 수신)
  │   └─ VRS 서버 연결 → RTCM 메시지 발행
  │
  └─ 두 노드 간 메시지 연결
      └─ /nmea (ublox → ntrip): 현재 위치 정보 전송
      └─ /rtcm (ntrip → ublox): RTCM 보정 데이터 수신
```

---

## 📦 패키지 구성

### 프로젝트 구조

```
RTK-GPS/
├── README.md                    # 본 문서
├── combined_rtk/                # ⭐ 통합 런치 패키지
│   ├── combined_rtk/__init__.py
│   ├── launch/
│   │   └── combined_nodes.launch.py    # 메인 런치 파일
│   ├── config/
│   │   └── zed_f9p.yaml               # ZED-F9P 설정 (10Hz, Rover 모드, GNSS 설정)
│   └── package.xml
│
├── ntrip_client/                # ✅ NTRIP 보정 클라이언트 (서브모듈)
│   ├── src/ntrip_client/
│   │   ├── ntrip_ros.py         # 메인 노드 (NTRIP 클라이언트 + ROS2 인터페이스)
│   │   ├── ntrip_base.py        # NTRIP 프로토콜 기본 구현
│   │   └── nmea_parser.py       # GGA 문장 파싱
│   ├── launch/
│   │   └── ntrip_client_launch.py
│   └── package.xml
│
├── ublox/                       # 📡 u-blox 드라이버 (서브모듈)
│   ├── ublox_gps/               # C++ 드라이버 (ZED-F9P 통신)
│   │   ├── src/
│   │   │   ├── node.cpp         # 메인 노드 (GPS 데이터 파싱 및 발행)
│   │   │   ├── gps.cpp          # GPS 제어 로직
│   │   │   ├── node_main.cpp    # 노드 엔트리 포인트
│   │   │   └── ublox_firmware*.cpp  # 펌웨어 버전별 최적화
│   │   ├── config/
│   │   │   └── zed_f9p.yaml     # 기본 설정 파일
│   │   ├── include/ublox_gps/   # 헤더 파일
│   │   └── CMakeLists.txt
│   │
│   ├── ublox_msgs/              # ROS2 메시지 정의
│   │   ├── msg/                 # GPS 관련 메시지 (80+개)
│   │   │   ├── CfgNAV5.msg      # 수신기 설정
│   │   │   ├── NavPVT.msg       # Position/Velocity/Time
│   │   │   ├── NavRelPosNED.msg # 상대 위치 (RTK 핵심)
│   │   │   └── ...
│   │   └── CMakeLists.txt
│   │
│   └── ublox_serialization/     # u-blox 바이너리 프로토콜 직렬화
│
└── script/
    ├── 50-ardusimple.rules      # udev 규칙 파일
    └── install_udev_rules.sh    # 설치 스크립트
```

### 각 패키지 역할

#### 📡 **ublox_gps** — GPS 드라이버
- **기능**: ZED-F9P 수신기와 직렬 통신하여 GPS 데이터 파싱 및 발행
- **출력 토픽**:
  - `/ublox_gps_node/fix` (sensor_msgs/NavSatFix): 위도/경도/고도
  - `/nmea` (nmea_msgs/Sentence): NMEA GGA 문장
  - `/ublox_gps_node/ublox_msgs/nav_pvt` (ublox_msgs/NavPVT): RTK 상태, 고도 표준편차
  - `/ublox_gps_node/ublox_msgs/nav_relposned` (ublox_msgs/NavRelPosNED): **RTK 상대 위치**
- **설정 파일**: [`config/zed_f9p.yaml`](combined_rtk/config/zed_f9p.yaml)

#### ✅ **ntrip_client** — RTCM 보정 클라이언트
- **기능**: VRS 서버에 연결하여 RTCM 보정 메시지를 ROS2 토픽으로 발행
- **입력 토픽**:
  - `/nmea` (nmea_msgs/Sentence): ublox_gps_node에서 현재 위치 정보 수신
- **출력 토픽**:
  - `/rtcm` (rtcm_msgs/Message): RTCM 보정 데이터
- **역할**: NTRIP VRS 서버와의 HTTP 통신, 인증, RTCM 파싱, ROS2 메시지 변환

#### 🎯 **combined_rtk** — 통합 관리
- **기능**: ublox_gps + ntrip_client를 하나의 런치 파일로 관리
- **런치 파일**: [`launch/combined_nodes.launch.py`](combined_rtk/launch/combined_nodes.launch.py)
- **역할**: 
  - 두 노드의 통신 설정 (remapping)
  - 공통 설정 파일 관리
  - 런치 인자 제공 (NTRIP 호스트, 포트, 계정 등)

---

## 🎛️ Launch 옵션

### 명령어 형식

```bash
ros2 launch combined_rtk combined_nodes.launch.py \
  [인자1=값1] [인자2=값2] ...
```

### 지원하는 Launch Arguments

#### **NTRIP 서버 설정**

| 인자 | 기본값 | 설명 |
|-----|------|------|
| `ntrip_host` | `rts1.ngii.go.kr` | NTRIP 보정 서버 호스트명 |
| `ntrip_port` | `2101` | NTRIP 서버 포트 |
| `ntrip_mountpoint` | `VRS-RTCM34` | NTRIP 마운트포인트 (서버에서 제공) |
| `ntrip_user` | `zero0023001` | NTRIP 인증 사용자명 |
| `ntrip_password` | `ngii` | NTRIP 인증 비밀번호 |

#### **GPS 성능 설정**

| 인자 | 기본값 | 설명 |
|-----|------|------|
| `hacc_limit` | `3.0` | 수평 정확도 필터 임계값 (m) |

### 사용 예시

#### **1️⃣ 기본 실행** (한국 NGII VRS 사용)
```bash
ros2 launch combined_rtk combined_nodes.launch.py
```

#### **2️⃣ u-blox PointPerfect 사용**
```bash
ros2 launch combined_rtk combined_nodes.launch.py \
  ntrip_host:=ppntrip.services.u-blox.com \
  ntrip_port:=2101 \
  ntrip_mountpoint:=pp \
  ntrip_user:=your_username \
  ntrip_password:=your_password
```

#### **3️⃣ 커스텀 NTRIP 서버**
```bash
ros2 launch combined_rtk combined_nodes.launch.py \
  ntrip_host:=your.ntrip.server.com \
  ntrip_port:=2101 \
  ntrip_mountpoint:=YOUR_MOUNT \
  ntrip_user:=your_user \
  ntrip_password:=your_pass
```

#### **4️⃣ 정확도 필터 조정**
```bash
ros2 launch combined_rtk combined_nodes.launch.py \
  hacc_limit:=5.0  # 5m 이상의 오차는 /fix 발행 안 함
```

---

## 📊 주요 설정 파일 상세 설명

### [`config/zed_f9p.yaml`](combined_rtk/config/zed_f9p.yaml)

#### 디바이스 설정
```yaml
device: /dev/tty_Ardusimple    # ArduSimple USB 장치
frame_id: gps                   # ROS tf frame ID
uart1:
  baudrate: 460800              # 높은 데이터율 (RTCM+NavPVT 동시 전송)
```

#### 측위 갱신 속도
```yaml
rate:
  meas: 100                      # 100ms = 10Hz (로봇 응용에 최적)
  nav: 1                         # 네비게이션 솔루션 갱신율
```

#### Rover 모드 설정 (⭐ 가장 중요)
```yaml
tmode3: 0                        # 0=Rover (상대 위치 계산)
                                 # 1=Base (기준점 역할)
                                 # 주의: 가이드 기본값 1은 ❌ 제거됨
```

#### 운동 모델 (멀티패스 내성)
```yaml
dynamic_model: automotive        # 지상 로봇용 (차량 모션 필터)
                                 # 드론: airborne1
                                 # 보행자: pedestrian
```

#### GNSS 성좌 설정 (위성 수 15~20개)
```yaml
gnss:
  gps: true                      # GPS (필수)
  galileo: true                  # Galileo EU 위성 (RTK 수렴 빠름)
  glonass: true                  # GLONASS 러시아 위성 (한국 하늘 우수)
  qzss: true                     # QZSS 일본/한국 추가 위성
  sbas: true                     # SBAS 보정 (DGNSS)
```

#### 발행 토픽 설정
```yaml
publish:
  nav:
    pvt: true                    # 위치/속도/시각 (필수)
    relposned: true              # RTK 상대 위치 (필수)
    sat: true                    # 위성 정보
    heading: true                # 듀얼 안테나 방위각
    cov: true                    # 위치 공분산 (EKF 입력)
```

---

## 🔄 실행 후 데이터 흐름

```
Hardware (ZED-F9P)
    ↓ [시리얼 UART 460800bps]
ublox_gps_node
    ├─ [NavPVT] → /nmea (GGA 문장)
    ├─ [NavPVT] → /ublox_gps_node/fix (위도/경도/고도)
    ├─ [NavPVT] → /ublox_gps_node/ublox_msgs/nav_pvt (상태)
    └─ [NavRelPosNED] → /ublox_gps_node/ublox_msgs/nav_relposned (RTK 위치)
         
ntrip_client
    ├─ [구독] /nmea ← ublox_gps_node (현재 위치 전송)
    ├─ [HTTP POST] GGA → VRS 서버
    └─ [발행] /rtcm ← VRS 서버로부터 RTCM 수신
         
ublox_gps_node (RTCM 수신)
    └─ [구독] /rtcm ← ntrip_client (보정 데이터 적용)
       └─ [NavPVT 업데이트] carr_soln = 2 (RTK Fix)
```

---

## 🛠️ 트러블슈팅

### ❌ `/dev/tty_Ardusimple` 없음
```bash
# udev 규칙 재설치
sudo ./script/install_udev_rules.sh
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -la /dev/tty_Ardusimple
```

### ❌ "Package not found" 에러
```bash
# 빌드된 패키지 경로 업데이트
source ~/sensor_ws/install/setup.bash
```

### ❌ RTCM 연결 실패
```bash
# 1. NTRIP 자격증명 확인
# 2. 마운트포인트 확인: http://rts1.ngii.go.kr:2101
# 3. 온라인 상태 확인
curl -u username:password http://rts1.ngii.go.kr:2101/
```

### ❌ RTK Fix 안 됨 (carr_soln != 2)
- RTCM 수신 확인: `ros2 topic echo /rtcm`
- GPS 신호 강도 확인: `ros2 topic echo /ublox_gps_node/ublox_msgs/nav_sat`
- 기준점 거리 확인 (VRS는 일반적으로 <100km)

---

## 📚 참고 자료

| 항목 | 링크 |
|-----|------|
| **u-blox 공식 드라이버** | https://github.com/KumarRobotics/ublox |
| **NTRIP 클라이언트** | https://github.com/LORD-MicroStrain/ntrip_client |
| **ZED-F9P 매뉴얼** | https://www.u-blox.com/en/product/zed-f9p-module |
| **한국 NGII VRS** | http://vrs.ngii.go.kr |
| **ROS2 공식 문서** | https://docs.ros.org/en/humble/ |

---

## 📝 라이선스

본 프로젝트는 포함된 각 패키지의 라이선스를 따릅니다:
- **ublox**: BSD 3-Clause
- **ntrip_client**: MIT
- **combined_rtk**: 프로젝트 정의

---

**Last Updated:** June 2026  
**Maintainer:** Zeroworks Robotics
