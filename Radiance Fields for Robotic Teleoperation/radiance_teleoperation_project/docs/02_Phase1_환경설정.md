# Phase 1: 환경 설정 및 기초 구조 구축 (2-3주)

## 🎯 목표
개발 환경 구축 및 기본 ROS 패키지 구조 생성

## 📋 상세 작업 계획

### 1.1 ROS 환경 설정 (1주)

#### 1.1.1 Ubuntu 20.04 LTS 설치 및 기본 설정
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y build-essential cmake git wget curl
sudo apt install -y python3-pip python3-dev python3-venv
sudo apt install -y nvidia-driver-470 nvidia-cuda-toolkit
```

#### 1.1.2 ROS Noetic 설치
```bash
# ROS Noetic 설치
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
sudo apt update
sudo apt install -y ros-noetic-desktop-full

# ROS 환경 설정
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
source ~/.bashrc

# ROS 의존성 설치
sudo apt install -y python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool build-essential
sudo rosdep init
rosdep update
```

#### 1.1.3 Catkin Workspace 생성
```bash
# Catkin workspace 생성
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/
catkin_make

# 환경 설정
echo "source ~/catkin_ws/devel/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 1.2 NerfStudio 환경 구축 (1주)

#### 1.2.1 Conda 환경 설정
```bash
# Miniconda 설치 (없는 경우)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# NerfStudio 환경 생성
conda create --name nerfstudio -y python=3.8
conda activate nerfstudio

# 기본 패키지 업그레이드
pip install --upgrade pip
```

#### 1.2.2 PyTorch 및 CUDA 설치
```bash
# PyTorch 설치 (CUDA 11.8 호환)
conda install pytorch==2.1.2 torchvision==0.16.2 pytorch-cuda=11.8 -c pytorch -c nvidia

# CUDA Toolkit 설치
conda install -c "nvidia/label/cuda-11.8.0" cuda-toolkit

# tinyCudaNN 설치
pip install ninja
pip install git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch
```

#### 1.2.3 NerfStudio 설치
```bash
# NerfStudio 설치
pip install nerfstudio

# 설치 검증
ns-train --help
ns-render --help
```

### 1.3 GPU 환경 검증 (3일)

#### 1.3.1 CUDA 호환성 확인
```bash
# CUDA 버전 확인
nvcc --version
nvidia-smi

# PyTorch CUDA 확인
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'CUDA version: {torch.version.cuda}')"
```

#### 1.3.2 메모리 요구사항 확인
```bash
# GPU 메모리 확인
nvidia-smi --query-gpu=memory.total,memory.free --format=csv

# PyTorch 메모리 테스트
python -c "
import torch
x = torch.randn(1000, 1000).cuda()
print(f'GPU memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB')
"
```

#### 1.3.3 tinyCudaNN 성능 테스트
```bash
# tinyCudaNN 테스트 스크립트 생성
cat > test_tinycudann.py << 'EOF'
import torch
import tinycudann as tcnn

# 간단한 네트워크 생성
encoding_config = {
    "otype": "HashGrid",
    "n_levels": 16,
    "n_features_per_level": 2,
    "log2_hashmap_size": 19,
    "base_resolution": 16,
    "per_level_scale": 2.0
}

network_config = {
    "otype": "FullyFusedMLP",
    "activation": "ReLU",
    "output_activation": "None",
    "n_neurons": 64,
    "n_hidden_layers": 1
}

encoding = tcnn.Encoding(3, encoding_config)
network = tcnn.Network(encoding.n_output_dims, 4, network_config)

# 테스트
x = torch.randn(1000, 3).cuda()
with torch.no_grad():
    output = network(encoding(x))
print(f"Output shape: {output.shape}")
print("tinyCudaNN test successful!")
EOF

python test_tinycudann.py
```

### 1.4 기본 ROS 패키지 구조 생성 (3일)

#### 1.4.1 패키지 생성
```bash
cd ~/catkin_ws/src

# 메인 패키지 생성
catkin_create_pkg radiance_teleoperation std_msgs rospy roscpp sensor_msgs geometry_msgs tf2_ros image_transport cv_bridge

# 서브 패키지들 생성
catkin_create_pkg radiance_camera std_msgs rospy sensor_msgs geometry_msgs
catkin_create_pkg radiance_nerf std_msgs rospy sensor_msgs geometry_msgs
catkin_create_pkg radiance_viz std_msgs rospy sensor_msgs geometry_msgs rviz
```

#### 1.4.2 디렉토리 구조 설정
```bash
# 메인 패키지 구조
cd radiance_teleoperation
mkdir -p config launch scripts msg srv test

# 설정 파일 생성
cat > config/camera_config.yaml << 'EOF'
# 카메라 설정 예시
cameras:
  - name: "front_camera"
    image_topic: "/camera/color/image_raw"
    depth_topic: "/camera/depth/image_rect_raw"
    info_topic: "/camera/color/camera_info"
    camera_frame: "camera_color_optical_frame"
    intrinsics:
      fx: 615.0
      fy: 615.0
      cx: 320.0
      cy: 240.0
    distortion:
      k1: 0.0
      k2: 0.0
      k3: 0.0
      p1: 0.0
      p2: 0.0
EOF

# Launch 파일 생성
cat > launch/radiance_teleop.launch << 'EOF'
<launch>
  <!-- 카메라 노드 -->
  <include file="$(find radiance_camera)/launch/camera.launch" />
  
  <!-- NeRF 노드 -->
  <include file="$(find radiance_nerf)/launch/nerf.launch" />
  
  <!-- 시각화 노드 -->
  <include file="$(find radiance_viz)/launch/viz.launch" />
</launch>
EOF
```

### 1.5 하드웨어 연결 테스트 (3일)

#### 1.5.1 Intel RealSense 설정
```bash
# RealSense SDK 설치
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main"
sudo apt update
sudo apt install -y librealsense2-dkms librealsense2-utils librealsense2-dev

# RealSense 테스트
realsense-viewer
```

#### 1.5.2 카메라 연결 테스트
```bash
# RealSense ROS 패키지 설치
cd ~/catkin_ws/src
git clone https://github.com/IntelRealSense/realsense-ros.git
cd realsense-ros
git checkout `git tag | sort -V | grep -P "^2.\d+\.\d+" | tail -1`
cd ~/catkin_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make

# 카메라 테스트
roslaunch realsense2_camera rs_camera.launch
```

#### 1.5.3 멀티 카메라 동기화 테스트
```bash
# 카메라 동기화 스크립트 생성
cat > scripts/test_multi_camera.py << 'EOF'
#!/usr/bin/env python3

import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class MultiCameraTest:
    def __init__(self):
        rospy.init_node('multi_camera_test')
        self.bridge = CvBridge()
        
        # 카메라 토픽 구독
        self.camera1_sub = rospy.Subscriber('/camera1/color/image_raw', Image, self.camera1_callback)
        self.camera2_sub = rospy.Subscriber('/camera2/color/image_raw', Image, self.camera2_callback)
        
        self.camera1_image = None
        self.camera2_image = None
        
    def camera1_callback(self, msg):
        self.camera1_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        
    def camera2_callback(self, msg):
        self.camera2_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        
    def run(self):
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            if self.camera1_image is not None and self.camera2_image is not None:
                # 이미지 표시
                cv2.imshow('Camera 1', self.camera1_image)
                cv2.imshow('Camera 2', self.camera2_image)
                cv2.waitKey(1)
            rate.sleep()

if __name__ == '__main__':
    try:
        test = MultiCameraTest()
        test.run()
    except rospy.ROSInterruptException:
        pass
EOF

chmod +x scripts/test_multi_camera.py
```

## ✅ 검증 기준

### 환경 설정 검증
- [ ] ROS Noetic 정상 설치 및 실행
- [ ] NerfStudio 환경에서 `ns-train --help` 명령어 실행 성공
- [ ] CUDA 11.8 및 PyTorch 정상 작동
- [ ] tinyCudaNN 설치 및 테스트 성공
- [ ] GPU 메모리 8GB 이상 확인

### 하드웨어 연결 검증
- [ ] Intel RealSense 카메라 정상 연결
- [ ] 카메라 스트림 정상 수신
- [ ] 멀티 카메라 동기화 테스트 성공
- [ ] 카메라 캘리브레이션 완료

### 패키지 구조 검증
- [ ] Catkin workspace 정상 빌드
- [ ] 모든 패키지 의존성 해결
- [ ] Launch 파일 정상 실행
- [ ] 기본 노드 실행 및 통신 확인

## 🚨 문제 해결 가이드

### 일반적인 문제들
1. **CUDA 버전 불일치**
   - 해결: PyTorch와 CUDA 버전 맞춤 설치
2. **ROS 의존성 문제**
   - 해결: `rosdep install --from-paths src --ignore-src -r -y` 실행
3. **카메라 연결 실패**
   - 해결: USB 권한 설정 및 드라이버 재설치

### 성능 최적화 팁
- GPU 메모리 모니터링: `watch -n 1 nvidia-smi`
- ROS 노드 성능: `rostopic hz /topic_name`
- 시스템 리소스: `htop` 및 `iotop`
