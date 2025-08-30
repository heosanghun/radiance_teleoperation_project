#!/bin/bash

# Radiance Fields for Robotic Teleoperation - 환경 설정 스크립트
# Phase 1: 환경 설정 및 기초 구조 구축

set -e  # 오류 발생 시 스크립트 중단

echo "🚀 Radiance Fields for Robotic Teleoperation 환경 설정을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 시스템 확인
check_system() {
    log_info "시스템 요구사항 확인 중..."
    
    # OS 확인
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_success "Linux 시스템 감지됨"
    else
        log_error "이 스크립트는 Linux 시스템에서만 실행됩니다."
        exit 1
    fi
    
    # Ubuntu 버전 확인
    if command -v lsb_release &> /dev/null; then
        UBUNTU_VERSION=$(lsb_release -rs)
        log_info "Ubuntu 버전: $UBUNTU_VERSION"
        
        if [[ "$UBUNTU_VERSION" != "20.04" && "$UBUNTU_VERSION" != "18.04" ]]; then
            log_warning "Ubuntu 20.04 또는 18.04를 권장합니다. 현재 버전: $UBUNTU_VERSION"
        fi
    fi
    
    # GPU 확인
    if command -v nvidia-smi &> /dev/null; then
        log_success "NVIDIA GPU 감지됨"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    else
        log_warning "NVIDIA GPU가 감지되지 않았습니다. CUDA 지원이 제한될 수 있습니다."
    fi
}

# 시스템 업데이트
update_system() {
    log_info "시스템 패키지 업데이트 중..."
    sudo apt update && sudo apt upgrade -y
    log_success "시스템 업데이트 완료"
}

# 필수 패키지 설치
install_basic_packages() {
    log_info "기본 패키지 설치 중..."
    
    sudo apt install -y \
        build-essential \
        cmake \
        git \
        wget \
        curl \
        python3-pip \
        python3-dev \
        python3-venv \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    
    log_success "기본 패키지 설치 완료"
}

# ROS Noetic 설치
install_ros_noetic() {
    log_info "ROS Noetic 설치 중..."
    
    # ROS 저장소 추가
    sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
    sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
    
    sudo apt update
    sudo apt install -y ros-noetic-desktop-full
    
    # ROS 환경 설정
    echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
    source /opt/ros/noetic/setup.bash
    
    # ROS 의존성 설치
    sudo apt install -y \
        python3-rosdep \
        python3-rosinstall \
        python3-rosinstall-generator \
        python3-wstool \
        build-essential
    
    sudo rosdep init
    rosdep update
    
    log_success "ROS Noetic 설치 완료"
}

# Catkin Workspace 생성
setup_catkin_workspace() {
    log_info "Catkin Workspace 설정 중..."
    
    # 워크스페이스 생성
    mkdir -p ~/catkin_ws/src
    cd ~/catkin_ws/
    catkin_make
    
    # 환경 설정
    echo "source ~/catkin_ws/devel/setup.bash" >> ~/.bashrc
    source ~/catkin_ws/devel/setup.bash
    
    log_success "Catkin Workspace 설정 완료"
}

# CUDA 및 GPU 드라이버 설치
install_cuda() {
    log_info "CUDA 및 GPU 드라이버 설치 중..."
    
    # NVIDIA 드라이버 설치
    sudo apt install -y nvidia-driver-470
    
    # CUDA Toolkit 설치
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
    sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
    sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
    sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
    sudo apt update
    sudo apt install -y cuda-toolkit-11-8
    
    log_success "CUDA 설치 완료"
}

# Miniconda 설치
install_miniconda() {
    log_info "Miniconda 설치 중..."
    
    if ! command -v conda &> /dev/null; then
        wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
        bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
        rm Miniconda3-latest-Linux-x86_64.sh
        
        # conda 초기화
        $HOME/miniconda3/bin/conda init bash
        source ~/.bashrc
    else
        log_info "Miniconda가 이미 설치되어 있습니다."
    fi
    
    log_success "Miniconda 설치 완료"
}

# NerfStudio 환경 설정
setup_nerfstudio() {
    log_info "NerfStudio 환경 설정 중..."
    
    # conda 환경 생성
    conda create --name nerfstudio -y python=3.8
    conda activate nerfstudio
    
    # 기본 패키지 업그레이드
    pip install --upgrade pip
    
    # PyTorch 설치 (CUDA 11.8 호환)
    conda install pytorch==2.1.2 torchvision==0.16.2 pytorch-cuda=11.8 -c pytorch -c nvidia -y
    
    # CUDA Toolkit 설치
    conda install -c "nvidia/label/cuda-11.8.0" cuda-toolkit -y
    
    # tinyCudaNN 설치
    pip install ninja
    pip install git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch
    
    # NerfStudio 설치
    pip install nerfstudio
    
    log_success "NerfStudio 환경 설정 완료"
}

# RealSense SDK 설치
install_realsense() {
    log_info "Intel RealSense SDK 설치 중..."
    
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
    sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main"
    sudo apt update
    sudo apt install -y librealsense2-dkms librealsense2-utils librealsense2-dev
    
    log_success "RealSense SDK 설치 완료"
}

# 프로젝트 패키지 생성
create_project_packages() {
    log_info "ROS 패키지 생성 중..."
    
    cd ~/catkin_ws/src
    
    # 메인 패키지 생성
    catkin_create_pkg radiance_teleoperation std_msgs rospy roscpp sensor_msgs geometry_msgs tf2_ros image_transport cv_bridge
    
    # 서브 패키지들 생성
    catkin_create_pkg radiance_camera std_msgs rospy sensor_msgs geometry_msgs
    catkin_create_pkg radiance_nerf std_msgs rospy sensor_msgs geometry_msgs
    catkin_create_pkg radiance_viz std_msgs rospy sensor_msgs geometry_msgs rviz
    catkin_create_pkg radiance_robot std_msgs rospy sensor_msgs geometry_msgs
    
    # RealSense ROS 패키지 클론
    git clone https://github.com/IntelRealSense/realsense-ros.git
    cd realsense-ros
    git checkout `git tag | sort -V | grep -P "^2.\d+\.\d+" | tail -1`
    cd ..
    
    # 의존성 설치
    cd ~/catkin_ws
    rosdep install --from-paths src --ignore-src -r -y
    
    # 빌드
    catkin_make
    
    log_success "ROS 패키지 생성 완료"
}

# 환경 검증
verify_installation() {
    log_info "설치 검증 중..."
    
    # ROS 검증
    if command -v roscore &> /dev/null; then
        log_success "ROS 설치 확인됨"
    else
        log_error "ROS 설치에 문제가 있습니다."
        return 1
    fi
    
    # CUDA 검증
    if command -v nvcc &> /dev/null; then
        log_success "CUDA 설치 확인됨"
        nvcc --version
    else
        log_warning "CUDA 설치에 문제가 있을 수 있습니다."
    fi
    
    # NerfStudio 검증
    if conda activate nerfstudio && ns-train --help &> /dev/null; then
        log_success "NerfStudio 설치 확인됨"
    else
        log_error "NerfStudio 설치에 문제가 있습니다."
        return 1
    fi
    
    # RealSense 검증
    if command -v realsense-viewer &> /dev/null; then
        log_success "RealSense SDK 설치 확인됨"
    else
        log_warning "RealSense SDK 설치에 문제가 있을 수 있습니다."
    fi
    
    log_success "모든 설치 검증 완료"
}

# 메인 실행 함수
main() {
    log_info "Radiance Fields for Robotic Teleoperation 환경 설정을 시작합니다..."
    
    check_system
    update_system
    install_basic_packages
    install_ros_noetic
    setup_catkin_workspace
    install_cuda
    install_miniconda
    setup_nerfstudio
    install_realsense
    create_project_packages
    verify_installation
    
    log_success "🎉 환경 설정이 완료되었습니다!"
    log_info "다음 단계:"
    log_info "1. 터미널을 재시작하거나 'source ~/.bashrc' 실행"
    log_info "2. 'conda activate nerfstudio'로 NerfStudio 환경 활성화"
    log_info "3. 'cd ~/catkin_ws && source devel/setup.bash'로 ROS 환경 설정"
    log_info "4. Phase 2: 데이터 수집 및 처리 파이프라인 구현으로 진행"
}

# 스크립트 실행
main "$@"
