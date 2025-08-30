# Radiance Fields for Robotic Teleoperation - 설치 가이드

## 🚀 빠른 시작

### 1. 시스템 요구사항

#### 하드웨어
- **GPU**: NVIDIA RTX 4080/4090 (12GB+ VRAM)
- **RAM**: 32GB 이상
- **저장공간**: 100GB 이상 (SSD 권장)
- **네트워크**: 기가비트 이더넷

#### 소프트웨어
- **OS**: Ubuntu 20.04 LTS
- **ROS**: Noetic
- **Python**: 3.8+
- **CUDA**: 11.8+
- **Unity**: 2022.3.12f1 (VR 개발용)

### 2. 자동 설치 (권장)

```bash
# 프로젝트 클론
git clone https://github.com/your-repo/radiance-teleoperation.git
cd radiance-teleoperation

# 자동 환경 설정 스크립트 실행
./scripts/setup_environment.sh
```

### 3. 수동 설치

#### 3.1 ROS Noetic 설치

```bash
# ROS 저장소 추가
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654

# ROS 설치
sudo apt update
sudo apt install ros-noetic-desktop-full

# 의존성 설치
sudo apt install python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool build-essential

# rosdep 초기화
sudo rosdep init
rosdep update
```

#### 3.2 CUDA 및 GPU 드라이버 설치

```bash
# NVIDIA 드라이버 설치
sudo apt install nvidia-driver-470

# CUDA Toolkit 설치
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt update
sudo apt install cuda-toolkit-11-8
```

#### 3.3 Miniconda 및 NerfStudio 설치

```bash
# Miniconda 설치
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
$HOME/miniconda3/bin/conda init bash
source ~/.bashrc

# NerfStudio 환경 생성
conda create --name nerfstudio -y python=3.8
conda activate nerfstudio

# PyTorch 설치
conda install pytorch==2.1.2 torchvision==0.16.2 pytorch-cuda=11.8 -c pytorch -c nvidia -y

# tinyCudaNN 설치
pip install ninja
pip install git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch

# NerfStudio 설치
pip install nerfstudio
```

#### 3.4 RealSense SDK 설치

```bash
# RealSense 저장소 추가
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main"
sudo apt update
sudo apt install librealsense2-dkms librealsense2-utils librealsense2-dev
```

#### 3.5 ROS 워크스페이스 설정

```bash
# Catkin 워크스페이스 생성
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/
catkin_make

# 환경 설정
echo "source ~/catkin_ws/devel/setup.bash" >> ~/.bashrc
source ~/catkin_ws/devel/setup.bash
```

### 4. 프로젝트 빌드

```bash
# 프로젝트 소스 복사
cp -r src/* ~/catkin_ws/src/

# 의존성 설치
cd ~/catkin_ws
rosdep install --from-paths src --ignore-src -r -y

# 빌드
catkin_make
```

### 5. Unity VR 프로젝트 설정

1. Unity Hub에서 Unity 2022.3.12f1 설치
2. `unity_vr/` 폴더를 Unity 프로젝트로 열기
3. Oculus Integration 패키지 설치
4. OpenXR Plugin 활성화
5. Meta Quest 3 개발자 모드 활성화

### 6. 설정 파일 구성

```bash
# 카메라 설정 파일 편집
nano config/camera_config.yaml

# ROS 네트워크 설정
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=your_ip_address
```

### 7. 설치 검증

```bash
# 통합 테스트 실행
./test/integration_test.sh
```

## 🔧 문제 해결

### 일반적인 문제

#### CUDA 설치 실패
```bash
# NVIDIA 드라이버 재설치
sudo apt purge nvidia*
sudo apt autoremove
sudo apt install nvidia-driver-470
```

#### ROS 토픽 연결 실패
```bash
# 네트워크 설정 확인
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=$(hostname -I | awk '{print $1}')
```

#### GPU 메모리 부족
```bash
# 배치 크기 조정
# config/nerf_config.yaml에서 batch_size를 줄이기
```

### 로그 확인

```bash
# ROS 로그 확인
rqt_console

# 시스템 리소스 모니터링
htop
nvidia-smi
```

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. [문제 해결 가이드](docs/TROUBLESHOOTING.md)
2. [GitHub Issues](https://github.com/your-repo/radiance-teleoperation/issues)
3. [Wiki](https://github.com/your-repo/radiance-teleoperation/wiki)

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
