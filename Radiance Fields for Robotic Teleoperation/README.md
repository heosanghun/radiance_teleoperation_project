# 🤖 Radiance Fields for Robotic Teleoperation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![ROS Noetic](https://img.shields.io/badge/ROS-Noetic-green.svg)](http://wiki.ros.org/noetic)
[![Unity 2022.3](https://img.shields.io/badge/Unity-2022.3-black.svg)](https://unity.com/)

ETH Zurich의 "Radiance Fields for Robotic Teleoperation" 논문을 바탕으로 한 **실시간 로봇 원격 조작 시스템**입니다. Neural Radiance Fields(NeRF)와 3D Gaussian Splatting(3DGS)을 활용하여 고품질의 몰입형 VR 텔레오퍼레이션 환경을 제공합니다.

## 🎯 프로젝트 개요

### 핵심 기능
- **🌐 온라인 Radiance Field 훈련**: 다중 카메라 실시간 데이터로 학습
- **🎨 다양한 방법 지원**: NeRF, 3DGS 등 여러 radiance field 방법 통합
- **🥽 VR 시각화 시스템**: Meta Quest 3 기반 몰입형 인터페이스
- **🔗 완전한 ROS 통합**: 기존 텔레오퍼레이션 시스템과 원활한 통합
- **🤖 다중 로봇 지원**: Franka Panda, Anymal, DynaArm+Anymal

### 목표 성능 지표
- **품질**: NeRF PSNR > 20, 3DGS PSNR > 25
- **속도**: 3DGS 렌더링 > 100 FPS, 훈련 속도 ~35ms/iteration
- **사용성**: VR 인터페이스 선호도 > 70%
- **안정성**: 1시간 연속 운영 가능

## 🛠️ 시스템 요구사항

### 하드웨어
- **개발 워크스테이션**: NVIDIA RTX 4080/4090 (12GB+ VRAM)
- **로봇 플랫폼**: Franka Panda 또는 Anymal (선택)
- **센서**: Intel RealSense 435i/L515
- **VR 헤드셋**: Meta Quest 3
- **네트워크**: 기가비트 이더넷

### 소프트웨어
- **OS**: Ubuntu 20.04 LTS
- **ROS**: Noetic
- **Python**: 3.8+
- **CUDA**: 11.8+
- **Unity**: 2022.3.12f1 (VR 개발용)
- **NerfStudio**: 최신 버전
- **PyTorch**: 2.1.2+
- **OpenCV**: 4.x
- **RealSense SDK**: 2.x
- **OpenXR**: 최신 버전
- **ROS TCP Endpoint**: 최신 버전

## 📦 설치 가이드

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/radiance-fields-robotic-teleoperation.git
cd radiance-fields-robotic-teleoperation/radiance_teleoperation_project
```

### 2. 자동 설치 (권장)
```bash
# 실행 권한 부여
chmod +x scripts/setup_environment.sh

# 자동 설치 실행
./scripts/setup_environment.sh
```

### 3. 수동 설치

#### 3.1 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential cmake git wget curl
```

#### 3.2 ROS Noetic 설치
```bash
# ROS Noetic 설치
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
wget -qO - https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo apt update
sudo apt install -y ros-noetic-desktop-full

# ROS 환경 설정
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

#### 3.3 Catkin 워크스페이스 설정
```bash
# Catkin 워크스페이스 생성
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src

# 프로젝트 패키지 복사
cp -r /path/to/radiance_teleoperation_project/src/* .

# 의존성 설치
sudo apt install -y python3-catkin-tools python3-rosdep
sudo rosdep init
rosdep update
rosdep install --from-paths . --ignore-src -r -y

# 빌드
cd ~/catkin_ws
catkin build
```

#### 3.4 CUDA 및 PyTorch 설치
```bash
# CUDA 11.8 설치
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run

# 환경 변수 설정
echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# PyTorch 설치
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 3.5 NerfStudio 설치
```bash
# Conda 환경 생성
conda create -n nerfstudio python=3.8
conda activate nerfstudio

# NerfStudio 설치
pip install nerfstudio

# tinycudann 설치
pip install tinycudann
```

#### 3.6 RealSense SDK 설치
```bash
# RealSense SDK 설치
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main"
sudo apt update
sudo apt install -y librealsense2-dkms librealsense2-utils librealsense2-dev librealsense2-dbg
```

#### 3.7 Unity VR 프로젝트 설정
```bash
# Unity Hub 설치
wget https://hub.unity3d.com/linux/repos/deb/pool/main/u/unity-hub/unity-hub_3.6.1_amd64.deb
sudo dpkg -i unity-hub_3.6.1_amd64.deb
sudo apt-get install -f

# Unity 2022.3.12f1 설치 (Unity Hub에서)
# VR 프로젝트 열기
unity-hub -- --projectPath /path/to/radiance_teleoperation_project/unity_vr
```

### 4. 설치 검증
```bash
# 통합 테스트 실행
chmod +x test/integration_test.sh
./test/integration_test.sh
```

## 📁 프로젝트 구조

```
radiance_teleoperation_project/
├── 📄 README.md                                    # 프로젝트 메인 README
├── 📄 INSTALLATION.md                              # 상세 설치 가이드
├── 📄 USER_MANUAL.md                               # 사용자 매뉴얼
│
├── 📁 src/                                         # ROS 패키지 소스 코드
│   ├── 📁 radiance_camera/                         # 카메라 데이터 수집 패키지
│   │   ├── 📁 src/
│   │   │   ├── 📄 multi_camera_node.py             # 다중 카메라 노드
│   │   │   ├── 📄 image_preprocessor.py            # 이미지 전처리
│   │   │   └── 📄 data_buffer.py                   # 데이터 버퍼링
│   │   ├── 📁 launch/
│   │   │   └── 📄 multi_camera.launch              # 카메라 실행 파일
│   │   ├── 📁 config/
│   │   │   └── 📄 camera_params.yaml               # 카메라 파라미터
│   │   ├── 📄 package.xml                          # ROS 패키지 정의
│   │   └── 📄 CMakeLists.txt                       # 빌드 설정
│   │
│   ├── 📁 radiance_nerf/                           # NeRF 훈련 패키지
│   │   ├── 📁 src/
│   │   │   ├── 📄 ros_dataset.py                   # ROS 데이터셋
│   │   │   ├── 📄 online_trainer.py                # 온라인 훈련기
│   │   │   ├── 📄 render_server.py                 # 렌더링 서버
│   │   │   └── 📄 model_manager.py                 # 모델 관리자
│   │   ├── 📁 launch/
│   │   │   └── 📄 nerf_training.launch             # NeRF 훈련 실행
│   │   ├── 📄 package.xml
│   │   └── 📄 CMakeLists.txt
│   │
│   ├── 📁 radiance_viz/                            # 시각화 패키지
│   │   ├── 📁 src/
│   │   │   ├── 📄 nerf_view_controller.cpp         # RViz 뷰 컨트롤러
│   │   │   └── 📄 viz_manager.py                   # 시각화 관리자
│   │   ├── 📁 launch/
│   │   │   └── 📄 visualization.launch             # 시각화 실행
│   │   ├── 📄 package.xml
│   │   └── 📄 CMakeLists.txt
│   │
│   ├── 📁 radiance_robot/                          # 로봇 제어 패키지
│   │   ├── 📁 src/
│   │   │   ├── 📄 robot_manager.py                 # 로봇 관리자
│   │   │   ├── 📄 pose_publisher.py                # 포즈 발행자
│   │   │   └── 📄 teleop_controller.py             # 텔레오퍼레이션 컨트롤러
│   │   ├── 📁 launch/
│   │   │   ├── 📄 franka_panda.launch              # Franka Panda 실행
│   │   │   ├── 📄 anymal.launch                    # Anymal 실행
│   │   │   └── 📄 dyna_anymal.launch               # DynaArm+Anymal 실행
│   │   ├── 📄 package.xml
│   │   └── 📄 CMakeLists.txt
│   │
│   └── 📁 radiance_teleop/                         # 메인 텔레오퍼레이션 패키지
│       ├── 📁 src/
│       │   ├── 📄 teleop_node.py                   # 메인 텔레오퍼레이션 노드
│       │   ├── 📄 system_manager.py                # 시스템 관리자
│       │   └── 📄 performance_monitor.py           # 성능 모니터
│       ├── 📁 launch/
│       │   └── 📄 teleop_system.launch             # 전체 시스템 실행
│       ├── 📄 package.xml
│       └── 📄 CMakeLists.txt
│
├── 📁 config/                                      # 설정 파일들
│   ├── 📄 camera_config.yaml                       # 카메라 설정
│   ├── 📄 nerf_config.yaml                         # NeRF 설정
│   ├── 📄 robot_config.yaml                        # 로봇 설정
│   ├── 📄 vr_config.yaml                           # VR 설정
│   └── 📄 system_config.yaml                       # 시스템 설정
│
├── 📁 scripts/                                     # 스크립트 파일들
│   ├── 📄 setup_environment.sh                     # 환경 설정 스크립트
│   ├── 📄 build_project.sh                         # 프로젝트 빌드 스크립트
│   ├── 📄 start_system.sh                          # 시스템 시작 스크립트
│   ├── 📄 performance_test.py                      # 성능 테스트 스크립트
│   └── 📄 data_collection.py                       # 데이터 수집 스크립트
│
├── 📁 test/                                        # 테스트 파일들
│   ├── 📄 integration_test.sh                      # 통합 테스트
│   ├── 📄 unit_test_camera.py                      # 카메라 단위 테스트
│   ├── 📄 unit_test_nerf.py                        # NeRF 단위 테스트
│   ├── 📄 unit_test_vr.py                          # VR 단위 테스트
│   └── 📄 performance_benchmark.py                 # 성능 벤치마크
│
├── 📁 unity_vr/                                    # Unity VR 프로젝트
│   ├── 📁 Assets/
│   │   ├── 📁 Scripts/
│   │   │   ├── 📄 VRManager.cs                     # VR 관리자
│   │   │   ├── 📄 ROSConnector.cs                  # ROS 연결자
│   │   │   ├── 📄 NerfViewer.cs                    # NeRF 뷰어
│   │   │   ├── 📄 RobotController.cs               # 로봇 컨트롤러
│   │   │   ├── 📄 HandTracking.cs                  # 손 추적
│   │   │   └── 📄 PerformanceOptimizer.cs          # 성능 최적화
│   │   ├── 📁 Prefabs/
│   │   │   ├── 📄 VRController.prefab              # VR 컨트롤러 프리팹
│   │   │   ├── 📄 NerfRenderer.prefab              # NeRF 렌더러 프리팹
│   │   │   └── 📄 RobotModel.prefab                # 로봇 모델 프리팹
│   │   ├── 📁 Materials/
│   │   │   └── 📄 NerfMaterial.mat                 # NeRF 머티리얼
│   │   └── 📁 Scenes/
│   │       └── 📄 TeleopScene.unity                # 메인 VR 씬
│   ├── 📁 ProjectSettings/
│   │   ├── 📄 ProjectVersion.txt                   # Unity 버전
│   │   └── 📄 XRSettings.asset                     # XR 설정
│   └── 📁 Packages/
│       └── 📄 manifest.json                        # 패키지 매니페스트
│
├── 📁 launch/                                      # ROS 실행 파일들
│   ├── 📄 full_system.launch                       # 전체 시스템 실행
│   ├── 📄 camera_only.launch                       # 카메라만 실행
│   ├── 📄 nerf_only.launch                         # NeRF만 실행
│   └── 📄 vr_only.launch                           # VR만 실행
│
├── 📁 docs/                                        # 문서들
│   ├── 📄 01_프로젝트_개요.md                      # 프로젝트 개요
│   ├── 📄 02_Phase1_환경설정.md                    # Phase 1: 환경 설정
│   ├── 📄 03_Phase2_데이터파이프라인.md            # Phase 2: 데이터 파이프라인
│   ├── 📄 04_Phase3_Radiance_Fields.md             # Phase 3: Radiance Fields
│   ├── 📄 05_Phase4_VR_시각화.md                   # Phase 4: VR 시각화
│   ├── 📄 06_Phase5-7_완성.md                      # Phase 5-7: 완성
│   ├── 📄 API_Reference.md                         # API 참조
│   ├── 📄 Development_Guide.md                     # 개발 가이드
│   ├── 📄 Troubleshooting.md                       # 문제 해결
│   └── 📄 Performance_Analysis.md                  # 성능 분석
│
├── 📁 docker/                                      # Docker 설정
│   ├── 📄 Dockerfile                               # 메인 Dockerfile
│   ├── 📄 docker-compose.yml                       # Docker Compose 설정
│   └── 📄 requirements.txt                         # Python 의존성
│
└── 📁 data/                                        # 데이터 저장소
    ├── 📁 raw/                                     # 원시 데이터
    ├── 📁 processed/                               # 처리된 데이터
    ├── 📁 models/                                  # 훈련된 모델
    └── 📁 logs/                                    # 로그 파일들
```

## 🚀 사용법

### 1. 시스템 시작

#### 1.1 전체 시스템 실행
```bash
# ROS 마스터 시작
roscore

# 새 터미널에서 전체 시스템 실행
roslaunch radiance_teleop teleop_system.launch
```

#### 1.2 개별 컴포넌트 실행
```bash
# 카메라만 실행
roslaunch radiance_camera multi_camera.launch

# NeRF 훈련만 실행
roslaunch radiance_nerf nerf_training.launch

# VR 시각화만 실행
roslaunch radiance_viz visualization.launch
```

### 2. Unity VR 앱 실행
```bash
# Unity 프로젝트 열기
unity-hub -- --projectPath /path/to/radiance_teleoperation_project/unity_vr

# Meta Quest 3에 빌드 및 배포
# Unity에서 Build Settings > Android > Build and Run
```

### 3. 시스템 모니터링
```bash
# ROS 토픽 확인
rostopic list
rostopic echo /camera_data
rostopic echo /nerf_rendered_image

# ROS 노드 확인
rosnode list
rosnode info /multi_camera_node

# RViz 실행
rviz
```

### 4. VR 인터페이스 사용법

#### 4.1 기본 조작
- **헤드셋**: 시점 이동 및 회전
- **컨트롤러**: 손 추적 및 제스처 인식
- **팜 메뉴**: 시스템 설정 및 모드 전환

#### 4.2 로봇 제어
- **포인팅 제스처**: 로봇 관절 선택
- **그랩 제스처**: 로봇 관절 제어
- **메뉴 제스처**: 제어 모드 전환

#### 4.3 NeRF 뷰어
- **컨트롤러 스틱**: 카메라 이동
- **트리거**: 렌더링 요청
- **버튼**: 품질/속도 모드 전환

## ⚙️ 설정

### 카메라 설정 (`config/camera_config.yaml`)
```yaml
cameras:
  front:
    device_id: "0"
    resolution: [640, 480]
    fps: 30
    pose:
      x: 0.0
      y: 0.0
      z: 0.5
      roll: 0.0
      pitch: 0.0
      yaw: 0.0
```

### NeRF 설정 (`config/nerf_config.yaml`)
```yaml
training:
  num_iterations: 1000
  learning_rate: 0.001
  batch_size: 4096

rendering:
  num_rays: 1024
  num_samples: 64
  near_plane: 0.1
  far_plane: 100.0
```

### 로봇 설정 (`config/robot_config.yaml`)
```yaml
robot_type: "franka_panda"  # or "anymal", "dyna_anymal"
control_mode: "position"    # or "velocity", "torque"
safety_limits:
  max_velocity: 1.0
  max_acceleration: 2.0
```

## 🧪 테스트

### 통합 테스트
```bash
# 전체 시스템 통합 테스트
./test/integration_test.sh
```

### 단위 테스트
```bash
# 카메라 테스트
python3 test/unit_test_camera.py

# NeRF 테스트
python3 test/unit_test_nerf.py

# VR 테스트
python3 test/unit_test_vr.py
```

### 성능 벤치마크
```bash
# 성능 테스트 실행
python3 test/performance_benchmark.py
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. CUDA 메모리 부족
```bash
# GPU 메모리 확인
nvidia-smi

# 배치 크기 줄이기
# config/nerf_config.yaml에서 batch_size 수정
```

#### 2. ROS 연결 실패
```bash
# ROS 마스터 확인
echo $ROS_MASTER_URI

# 네트워크 설정 확인
ifconfig
```

#### 3. RealSense 카메라 인식 실패
```bash
# RealSense SDK 확인
realsense-viewer

# USB 권한 설정
sudo usermod -a -G video $USER
```

#### 4. Unity VR 빌드 실패
```bash
# Android SDK 확인
echo $ANDROID_HOME

# Unity 버전 확인
# Unity 2022.3.12f1 사용 권장
```

## 📊 성능 최적화

### GPU 최적화
- **CUDA 그래프 사용**: 반복적인 연산 최적화
- **혼합 정밀도**: FP16 사용으로 메모리 절약
- **메모리 풀링**: GPU 메모리 재사용

### 네트워크 최적화
- **압축 전송**: 이미지 압축으로 대역폭 절약
- **지연 시간 최적화**: UDP 사용으로 지연 감소
- **로컬 캐싱**: 자주 사용되는 데이터 캐싱

### VR 최적화
- **포비에이티드 렌더링**: 시야 중심 고품질 렌더링
- **LOD 시스템**: 거리에 따른 상세도 조절
- **비동기 렌더링**: 백그라운드 렌더링

## 🤝 기여하기

### 개발 환경 설정
```bash
# 포크 및 클론
git clone https://github.com/yourusername/radiance-fields-robotic-teleoperation.git
cd radiance-fields-robotic-teleoperation

# 개발 브랜치 생성
git checkout -b feature/your-feature-name

# 변경사항 커밋
git add .
git commit -m "Add your feature description"

# PR 생성
git push origin feature/your-feature-name
```

### 코딩 스타일
- **Python**: PEP 8 준수
- **C++**: Google C++ Style Guide 준수
- **C#**: Microsoft C# Coding Conventions 준수
- **주석**: 한국어 또는 영어로 상세한 설명

### 테스트 작성
- **단위 테스트**: 각 모듈별 테스트 작성
- **통합 테스트**: 전체 시스템 테스트
- **성능 테스트**: 벤치마크 테스트

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

- **ETH Zurich**: 원본 논문 및 연구
- **NerfStudio**: NeRF 구현 프레임워크
- **ROS Community**: 로봇 운영 체제
- **Unity Technologies**: VR 개발 플랫폼

## 📞 연락처

- **이슈 리포트**: [GitHub Issues](https://rffr.leggedrobotics.com/works/teleoperation/))
- **문의사항**: wwwhunycom@naver.com
- **프로젝트 홈페이지**: [Project Website](http://moduirum.ai)

## 📈 로드맵

- [ ] **v1.0**: 기본 NeRF 텔레오퍼레이션 시스템
- [ ] **v1.1**: 3D Gaussian Splatting 지원
- [ ] **v1.2**: 다중 로봇 플랫폼 지원
- [ ] **v2.0**: 고급 VR 인터페이스
- [ ] **v2.1**: 실시간 협업 기능
- [ ] **v3.0**: AI 기반 자동화

---

⭐ **이 프로젝트가 도움이 되었다면 스케이드보드를 함께 타고 놀아주세요!**


